import os
import shutil
from datetime import datetime
from datetime import datetime

VAULT_PATH = "/vault"
ATTACHMENTS_DIR = os.path.join(VAULT_PATH, "Attachments")

def ensure_dirs():
    os.makedirs(ATTACHMENTS_DIR, exist_ok=True)

def save_note(path: str, content: str) -> str:
    ensure_dirs()
    
    # Убеждаемся, что путь безопасен
    path = path.lstrip('/')
    if not path.endswith('.md'):
        path += '.md'
        
    full_path = os.path.join(VAULT_PATH, path)
    
    # Создаем все вложенные папки, если их нет
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    
    # Добавляем таймстемп, если файл уже существует
    if os.path.exists(full_path):
        name, ext = os.path.splitext(path)
        timestamp = datetime.now().strftime("%H%M%S")
        path = f"{name}_{timestamp}{ext}"
        full_path = os.path.join(VAULT_PATH, path)
    
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return path

def save_attachment(file_path: str, original_name: str) -> str:
    ensure_dirs()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name, ext = os.path.splitext(original_name)
    new_name = f"{name}_{timestamp}{ext}"
    dest_path = os.path.join(ATTACHMENTS_DIR, new_name)
    
    shutil.copy(file_path, dest_path)
    return new_name
