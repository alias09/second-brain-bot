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

async def update_embeddings():
    """Синхронизирует кэш эмбеддингов с файлами в Vault."""
    cache = load_cache()
    md_files = get_all_md_files()
    
    updated = False
    current_files = set()
    
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
                    
                # Получаем вектор (ограничим размер текста)
                text_to_embed = content[:8000]
                import ai_service
                embedding = await ai_service.get_embedding(text_to_embed)
                
                cache[file_path] = {
                    'mtime': mtime,
                    'embedding': embedding,
                    'content': content
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
    """Ищет наиболее релевантные заметки для запроса."""
    cache = await update_embeddings()
    if not cache:
        return []
        
    import ai_service
    query_embedding = await ai_service.get_embedding(query)
    
    results = []
    for file_path, data in cache.items():
        if 'embedding' in data:
            sim = cosine_similarity(query_embedding, data['embedding'])
            results.append((sim, data['content'], file_path))
            
    # Сортируем по убыванию сходства
    results.sort(key=lambda x: x[0], reverse=True)
    
    # Возвращаем контент топ K заметок с их относительным путем
    return [f"File: {os.path.relpath(path, VAULT_PATH)}\nContent:\n{content}" for _, content, path in results[:top_k]]
