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
    """Searches the vault for notes matching the query using semantic search."""
    try:
        results = await search_service.search_notes(query, top_k=5)
        if not results:
            return "No relevant notes found."
        return "\n\n---\n\n".join(results)
    except Exception as e:
        return f"Error searching notes: {e}"

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
    }
]
