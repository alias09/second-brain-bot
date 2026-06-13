import os
import json
import numpy as np
import asyncio
import asyncio

VAULT_PATH = "/vault"
CACHE_FILE = os.path.join(VAULT_PATH, ".embeddings_cache.json")

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def get_all_md_files():
    files = []
    for root, _, filenames in os.walk(VAULT_PATH):
        for name in filenames:
            if name.endswith('.md'):
                files.append(os.path.join(root, name))
    return files

def chunk_markdown(text: str, max_chunk_size: int = 1500, overlap_size: int = 400) -> list[str]:
    """Разбивает текст на куски с пересечением (overlap) для сохранения контекста."""
    paragraphs = text.split('\n\n')
    chunks = []
    current_paragraphs = []
    current_length = 0
    
    for p in paragraphs:
        p_len = len(p) + 2
        
        if current_length + p_len > max_chunk_size and current_paragraphs:
            chunks.append("\n\n".join(current_paragraphs).strip())
            
            overlap_paragraphs = []
            overlap_length = 0
            for op in reversed(current_paragraphs):
                if overlap_length + len(op) + 2 <= overlap_size:
                    overlap_paragraphs.insert(0, op)
                    overlap_length += len(op) + 2
                else:
                    if not overlap_paragraphs:
                        overlap_paragraphs.insert(0, op)
                        overlap_length += len(op) + 2
                    break
            
            current_paragraphs = overlap_paragraphs
            current_length = overlap_length
            
        current_paragraphs.append(p)
        current_length += p_len
        
    if current_paragraphs:
        chunks.append("\n\n".join(current_paragraphs).strip())
        
    return [c for c in chunks if len(c) > 10]

async def update_embeddings():
    """Синхронизирует кэш эмбеддингов с файлами в Vault."""
    cache = load_cache()
    md_files = get_all_md_files()
    
    updated = False
    current_files = set()
    
    import ai_service
    
    for file_path in md_files:
        current_files.add(file_path)
        mtime = os.path.getmtime(file_path)
        
        # Если файла нет в кэше или он был изменен
        if file_path not in cache or cache[file_path].get('mtime') != mtime:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Не эмбеддим пустые файлы
                if len(content.strip()) < 10:
                    continue
                    
                chunks_texts = chunk_markdown(content)
                chunks_data = []
                
                for idx, text_chunk in enumerate(chunks_texts):
                    rel_path = os.path.relpath(file_path, VAULT_PATH)
                    # Обогащаем чанк контекстом файла для лучшего эмбеддинга
                    enriched_text = f"[Файл: {rel_path}]\n{text_chunk}"
                    embedding = await ai_service.get_embedding(enriched_text)
                    chunks_data.append({
                        'index': idx,
                        'text': text_chunk,
                        'embedding': embedding
                    })
                
                cache[file_path] = {
                    'mtime': mtime,
                    'chunks': chunks_data
                }
                updated = True
            except Exception as e:
                print(f"Ошибка при обработке {file_path}: {e}")
                
    # Удаляем из кэша удаленные файлы
    keys_to_remove = [k for k in cache.keys() if k not in current_files]
    for k in keys_to_remove:
        del cache[k]
        updated = True
        
    if updated:
        save_cache(cache)
        
    return cache

def cosine_similarity(a, b):
    # Защита от нулевых векторов
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return np.dot(a, b) / (norm_a * norm_b)

async def search_notes(query: str, top_k: int = 5) -> list[str]:
    """Ищет наиболее релевантные заметки (чанки) для запроса."""
    cache = await update_embeddings()
    if not cache:
        return []
        
    import ai_service
    query_embedding = await ai_service.get_embedding(query)
    
    results = []
    for file_path, data in cache.items():
        rel_path = os.path.relpath(file_path, VAULT_PATH)
        if 'chunks' in data:
            for chunk in data['chunks']:
                sim = cosine_similarity(query_embedding, chunk['embedding'])
                results.append((sim, chunk['text'], rel_path, chunk.get('index', 0)))
            
    # Сортируем по убыванию сходства
    results.sort(key=lambda x: x[0], reverse=True)
    
    # Возвращаем контент топ K чанков с указанием их расположения
    return [f"Файл: {path}\nФрагмент:\n{text}" for _, text, path, _ in results[:top_k]]
