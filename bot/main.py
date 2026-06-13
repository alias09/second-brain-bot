import asyncio
import os
from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import load_dotenv

import handlers
import consolidation

load_dotenv()

class AccessMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        allowed_ids_str = os.getenv("ALLOWED_USER_IDS", "")
        if allowed_ids_str and event.from_user:
            try:
                allowed_ids = [int(i.strip()) for i in allowed_ids_str.split(",") if i.strip()]
                if event.from_user.id not in allowed_ids:
                    return # Игнорируем чужих
            except ValueError:
                pass
        return await handler(event, data)

async def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token or token == "your_telegram_bot_token_here":
        print("❌ Токен Telegram бота не найден! Укажите TELEGRAM_BOT_TOKEN в файле .env")
        return

    bot = Bot(
        token=token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    
    # Добавляем middleware для проверки ID пользователя
    dp.message.middleware(AccessMiddleware())
    
    dp.include_router(handlers.router)

    print("🚀 Запуск Telegram бота 'Второй Мозг'...")
    # Запускаем фоновый процесс консолидации памяти
    asyncio.create_task(consolidation.run_consolidation_loop())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
