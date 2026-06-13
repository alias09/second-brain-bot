# Plan: OpenCode Environment Setup

Адаптация "Every Agentic Engineering Hack I Know" под opencode.

**Machine:** macOS (личная)  
**Engine:** opencode v1.17.3  
**Terminal:** Пока Terminal.app → установим Ghostty  
**Provider:** Нужно настроить  
**Notes:** Obsidian

---

## Порядок выполнения

### 1. Ghostty (терминал)
Установить Ghostty через brew — современный терминал с поддержкой всех фич.

### 2. Провайдер для opencode
Настроить LLM провайдер (OpenCode Zen или свой API ключ).

### 3. Конфигурация opencode (HACK 8)
- Частичный YOLO: разрешить bash/edit/read, но ask для опасного
- Звук завершения задачи
- Базовые настройки

### 4. cmux (HACK 5)
Установить cmux — терминальный мультиплексор для параллельных сессий.

### 5. Ghostty → opencode launcher (HACK 6)
Каждая новая вкладка сразу открывает opencode.

### 6. Obsidian MCP (HACK 14)
Подключить Obsidian через MCP сервер.

### 7. Remote control (HACK 7)
Настроить opencode serve для доступа с телефона.

### 8. Skills + Commands (HACK 1, 17)
- `/plan` → `/work` команды
- Skill для research перед планированием
- Custom команды

### 9. Never sleep (HACK 19)
`pmset -a disablesleep 1`

---

## Финальная проверка
- [ ] Ghostty установлен, новая вкладка → opencode
- [ ] Провайдер работает (opencode выполняет задачи)
- [ ] Permissions настроены (YOLO для разработки)
- [ ] Звук завершения задачи
- [ ] cmux установлен
- [ ] Obsidian подключён
- [ ] Remote control работает
- [ ] /plan → /work команды настроены
