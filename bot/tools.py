import json
import os
import obsidian
import search_service

def read_note(path: str) -> str:
    """Reads the content of a specific note from the vault."""
    full_path = os.path.join(obsidian.VAULT_PATH, path)
    if not os.path.exists(full_path):
        return f"Error: Note '{path}' does not exist."
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"

def create_note(path: str, content: str) -> str:
    """Creates a new note or overwrites an existing note."""
    try:
        actual_path = obsidian.save_note(path, content)
        return f"Success: Note saved as '{actual_path}'"
    except Exception as e:
        return f"Error saving note: {e}"

def update_note(path: str, target_string: str, replacement_string: str) -> str:
    """Replaces a specific substring in an existing note."""
    full_path = os.path.join(obsidian.VAULT_PATH, path)
    if not os.path.exists(full_path):
        return f"Error: Note '{path}' does not exist."
    
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if target_string not in content:
            return f"Error: The target_string was not found in the note."
            
        new_content = content.replace(target_string, replacement_string)
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        return f"Success: Note '{path}' updated."
    except Exception as e:
        return f"Error updating note: {e}"

async def search_notes_tool(query: str) -> str:
    """Searches the vault using Multi-Query decomposition for better context."""
    import ai_service
    import json
    
    prompt = (
        f"Пользователь ищет информацию по запросу: '{query}'.\n"
        "Сгенерируй 3 синонимичных или более точных поисковых запроса для векторной базы данных. "
        "Верни ТОЛЬКО массив строк в формате JSON, без маркдауна и других слов.\n"
        'Пример: ["запрос 1", "запрос 2", "запрос 3"]'
    )
    try:
        response = await ai_service.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        content = response.choices[0].message.content.strip('` \n')
        if content.startswith('json'):
            content = content[4:].strip()
        queries = json.loads(content)
    except Exception:
        queries = [query]
        
    if query not in queries:
        queries.append(query)
        
    all_results = []
    seen_chunks = set()
    
    for q in queries:
        try:
            results = await search_service.search_notes(q, top_k=3)
            for res in results:
                if res not in seen_chunks:
                    seen_chunks.add(res)
                    all_results.append(res)
        except Exception as e:
            print(f"Search error for '{q}': {e}")
            
    if not all_results:
        return "No relevant notes found."
        
    return "\n\n---\n\n".join(all_results)

def link_notes(source_path: str, target_path: str, reason: str) -> str:
    """Creates a backlink from source to target note with an explanation."""
    full_source = os.path.join(obsidian.VAULT_PATH, source_path)
    if not os.path.exists(full_source):
        return f"Error: Source note '{source_path}' does not exist."
        
    link_text = f"\n\n### Связанные заметки\n- [[{target_path}]] — {reason}\n"
    try:
        with open(full_source, 'a', encoding='utf-8') as f:
            f.write(link_text)
        return f"Success: Linked '{source_path}' to '{target_path}'"
    except Exception as e:
        return f"Error linking notes: {e}"

def append_note(path: str, content: str) -> str:
    """Appends content to the end of an existing note."""
    full_path = os.path.join(obsidian.VAULT_PATH, path)
    if not os.path.exists(full_path):
        return f"Error: Note '{path}' does not exist. Use create_note instead."
    try:
        with open(full_path, 'a', encoding='utf-8') as f:
            if not content.startswith('\n'):
                f.write('\n\n')
            f.write(content)
        return f"Success: Content appended to '{path}'"
    except Exception as e:
        return f"Error appending to note: {e}"

def list_directory(path: str) -> str:
    """Lists files and folders in a specific directory inside the Vault."""
    full_path = os.path.join(obsidian.VAULT_PATH, path)
    
    if not os.path.abspath(full_path).startswith(os.path.abspath(obsidian.VAULT_PATH)):
        return "Error: Path is outside the vault."
        
    if not os.path.exists(full_path):
        return f"Error: Directory '{path}' does not exist."
    if not os.path.isdir(full_path):
        return f"Error: '{path}' is not a directory."
        
    try:
        items = os.listdir(full_path)
        items = [i for i in items if not i.startswith('.')]
        if not items:
            return f"Directory '{path}' is empty."
            
        result = []
        for item in sorted(items):
            item_path = os.path.join(full_path, item)
            if os.path.isdir(item_path):
                result.append(f"📁 {item}/")
            else:
                result.append(f"📄 {item}")
        return "\n".join(result)
    except Exception as e:
        return f"Error listing directory: {e}"

# OpenAI Function Definitions
OPENAI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_note",
            "description": "Reads the full content of a specific note from the Obsidian vault. Use this to inspect the contents of a file before updating it.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The relative path to the note (e.g. '1-Projects/Design.md')."
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_note",
            "description": "Creates a new note in the Obsidian vault using the PARA structure. Must include valid YAML frontmatter.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The relative path for the new note (e.g. '3-Resources/Health/Diet.md')."
                    },
                    "content": {
                        "type": "string",
                        "description": "The full markdown content of the note, including YAML frontmatter with tags, summary, and type."
                    }
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_note",
            "description": "Replaces a specific substring in an existing note. Use this to update task statuses (e.g., replacing '- [ ] Task' with '- [x] Task') or edit sections.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The relative path to the note being edited."
                    },
                    "target_string": {
                        "type": "string",
                        "description": "The exact string in the file to be replaced."
                    },
                    "replacement_string": {
                        "type": "string",
                        "description": "The new string that will replace the target_string."
                    }
                },
                "required": ["path", "target_string", "replacement_string"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_notes_tool",
            "description": "Performs a semantic search across all notes in the vault to find information related to the query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query or question."
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "append_note",
            "description": "Appends text to the end of an existing note. Use this for adding tasks, thoughts, or log entries without rewriting the whole file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The relative path to the note (e.g. '0-Inbox/Today.md')."
                    },
                    "content": {
                        "type": "string",
                        "description": "The content to append."
                    }
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "Lists all files and subdirectories in a specific folder within the Obsidian vault.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The relative path to the directory. Use '' (empty string) for the root of the vault."
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "link_notes",
            "description": "Adds a backlink from one note to another with a reason. Use this to connect related ideas or projects.",
            "parameters": {
                "type": "object",
                "properties": {
                    "source_path": {
                        "type": "string",
                        "description": "The path of the note where the link will be written."
                    },
                    "target_path": {
                        "type": "string",
                        "description": "The path of the note being linked to."
                    },
                    "reason": {
                        "type": "string",
                        "description": "A short explanation of why these notes are related."
                    }
                },
                "required": ["source_path", "target_path", "reason"]
            }
        }
    }
]
