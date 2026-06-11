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
        "Ты имеешь доступ к инструментам (Tools) для чтения, создания, поиска и обновления файлов. "
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
        "2. Если пользователь просит найти что-то, используй search_notes_tool.\n"
        "3. Если пользователь хочет отметить задачу выполненной, сначала прочитай заметку (read_note), затем обнови (update_note), заменив '- [ ]' на '- [x]'.\n"
        "4. Если пользователь просто делится мыслями, поддерживай диалог. Создавай заметку (create_note), когда мысль завершена или если пользователь просит об этом."
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
                else:
                    result = f"Error: Unknown tool {fn_name}"
            except Exception as e:
                result = f"Error executing {fn_name}: {e}"
                
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(result)
            })
