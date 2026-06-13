import os
import asyncio
from datetime import datetime, timedelta
import obsidian
import ai_service

async def run_consolidation_loop():
    """Фоновый процесс для сбора Daily Synthesis из папки Inbox."""
    print("🔄 Фоновый процесс консолидации памяти запущен.")
    # Первый запуск через 24 часа. Для демо-целей можно уменьшить время.
    # Но по плану это Daily процесс.
    while True:
        try:
            await asyncio.sleep(24 * 60 * 60)
            
            inbox_path = os.path.join(obsidian.VAULT_PATH, "0-Inbox")
            if not os.path.exists(inbox_path):
                continue
                
            yesterday = datetime.now() - timedelta(days=1)
            notes_content = []
            
            for filename in os.listdir(inbox_path):
                if not filename.endswith('.md'):
                    continue
                file_path = os.path.join(inbox_path, filename)
                mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                # Собираем только файлы за последние 24 часа
                if mtime > yesterday:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        notes_content.append(f"Файл: {filename}\n{f.read()}\n")
                        
            if not notes_content:
                continue # Нет новых заметок
                
            all_text = "\n---\n".join(notes_content)
            all_text = all_text[:80000] # Ограничиваем размер текста
            
            prompt = (
                "Ты — модуль консолидации памяти. Тебе на вход дают все заметки, созданные пользователем за последний день в папке Inbox. "
                "Твоя задача — сделать единую структурированную выжимку новых знаний, идей и проектов за день. "
                "Сгруппируй информацию по темам. Выдели самые важные инсайты или невыполненные задачи. "
                "Верни текст в формате Markdown."
            )
            
            response = await ai_service.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": all_text}
                ]
            )
            
            synthesis = response.choices[0].message.content
            
            time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            date_str = datetime.now().strftime("%Y-%m-%d")
            
            note_content = (
                "---\n"
                f"created: '{time_now}'\n"
                "tags: [synthesis, daily]\n"
                "type: 'synthesis'\n"
                "---\n"
                f"# Синтез за {date_str}\n\n"
                f"{synthesis}"
            )
            
            obsidian.save_note(f"3-Resources/Daily_Synthesis/{date_str}.md", note_content)
            print(f"✅ Фоновый синтез за {date_str} успешно завершен.")
            
        except Exception as e:
            print(f"❌ Ошибка в процессе консолидации памяти: {e}")
            await asyncio.sleep(3600) # В случае ошибки ждем час и пробуем снова
