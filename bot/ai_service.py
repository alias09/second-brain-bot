import os
import json
from datetime import datetime
from openai import AsyncOpenAI
import tools

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def transcribe_audio(file_path: str) -> str:
    """Транскрибирует аудиофайл с помощью Whisper."""
    with open(file_path, "rb") as audio_file:
        transcript = await client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file
        )
    return transcript.text

async def get_embedding(text: str) -> list[float]:
    """Генерирует вектор для текста."""
    response = await client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

import base64

async def structure_raw_text(raw_text: str) -> str:
    """Уплотняет сырой текст от Whisper, извлекая факты и задачи."""
    prompt = (
        "Ты — препроцессор памяти. Тебе на вход дают сырой неструктурированный текст (поток сознания, возможно с ошибками распознавания голоса). "
        "Твоя задача — извлечь из него максимум полезной информации и вернуть плотный Markdown.\n"
        "Правила:\n"
        "1. Удали весь словесный мусор и воду.\n"
        "2. Выдели основную суть в 1-2 предложения (Саммари).\n"
        "3. Перечисли ключевые факты в виде маркированного списка (bullet points).\n"
        "4. Если в тексте упоминаются намерения что-то сделать, выпиши их как задачи: '- [ ] Задача'.\n"
        "Верни ТОЛЬКО отформатированный текст, без вводных слов."
    )
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": raw_text}
        ]
    )
    return response.choices[0].message.content

async def analyze_image(image_path: str, caption: str) -> str:
    """Использует GPT-4o Vision для извлечения текста и смысла из изображения."""
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        
    prompt = (
        "Посмотри на это изображение. Твоя задача — извлечь из него все полезные данные для базы знаний.\n"
        "1. Если это текст (документ, визитка, скриншот кода) — выпиши весь текст (OCR).\n"
        "2. Если это график, схема или диаграмма — подробно опиши её суть и выводы.\n"
        "3. Если это просто фото — опиши, что на нем происходит.\n"
        f"Пользователь добавил подпись: '{caption}'. Учти её при анализе.\n"
        "Верни результат в формате Markdown, разбитый на логические секции (например, 'Суть', 'Распознанный текст', 'Выводы')."
    )
    
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ]
    )
    return response.choices[0].message.content

async def agent_chat(history: list[dict]) -> tuple[str, list[dict]]:
    """
    Единый цикл Агента. Вызывает инструменты (tools), пока не получит нужный результат,
    затем возвращает текстовый ответ пользователю и обновленную историю.
    """
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    system_prompt = (
        "Ты — умный автономный агент 'Второго Мозга' (Second Brain) на базе Obsidian. "
        "Твоя задача — помогать пользователю находить, создавать и редактировать заметки. "
        "Vault использует структуру PARA (1-Projects, 2-Areas, 3-Resources, 4-Archives, 0-Inbox). "
        "Ты имеешь доступ к инструментам (Tools) для чтения, создания, поиска, добавления и просмотра папок. "
        "ВАЖНО: Если ты создаешь заметку, она ОБЯЗАТЕЛЬНО должна начинаться с YAML frontmatter:\n"
        "---\n"
        f"created: '{current_time}'\n"
        "tags: [теги]\n"
        "summary: 'Краткое описание без точки в конце'\n"
        "participants: [участники, если есть]\n"
        "type: 'тип'\n"
        "---\n\n"
        "Правила:\n"
        "1. ВСЕГДА отвечай на русском языке.\n"
        "2. Если пользователь просит найти что-то, используй search_notes_tool. Запрос может быть неточным, перефразируй его для лучшего поиска.\n"
        "3. ПЛОТНОСТЬ ДАННЫХ: При создании или дописывании заметок не сохраняй сырой текст. Извлекай суть, формируй факты (bullet points) и четкие списки задач (- [ ]). Каждая запись должна быть понятна без контекста всей беседы.\n"
        "4. Для дописывания идей в существующую заметку используй append_note. Для изменения статуса конкретной задачи используй update_note.\n"
        "5. Если не уверен в структуре папок, используй list_directory('') перед созданием новых файлов."
    )
    
    # Собираем контекст: системный промпт + история
    messages = [{"role": "system", "content": system_prompt}] + history
    
    # Agent Loop
    while True:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=tools.OPENAI_TOOLS
        )
        
        message = response.choices[0].message
        
        # Если модель не вызвала инструмент, значит это финальный ответ пользователю
        if not message.tool_calls:
            # Не сохраняем системный промпт в возвращаемую историю, только диалог
            return message.content, messages[1:]
            
        # Добавляем сообщение ассистента с вызовами инструментов в историю
        messages.append(message)
        
        # Выполняем каждый инструмент
        for tool_call in message.tool_calls:
            fn_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            
            try:
                if fn_name == "read_note":
                    result = tools.read_note(args["path"])
                elif fn_name == "create_note":
                    result = tools.create_note(args["path"], args["content"])
                elif fn_name == "update_note":
                    result = tools.update_note(args["path"], args["target_string"], args["replacement_string"])
                elif fn_name == "search_notes_tool":
                    result = await tools.search_notes_tool(args["query"])
                elif fn_name == "append_note":
                    result = tools.append_note(args["path"], args["content"])
                elif fn_name == "list_directory":
                    result = tools.list_directory(args["path"])
                elif fn_name == "link_notes":
                    result = tools.link_notes(args["source_path"], args["target_path"], args["reason"])
                else:
                    result = f"Error: Unknown tool {fn_name}"
            except Exception as e:
                result = f"Error executing {fn_name}: {e}"
                
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(result)
            })
