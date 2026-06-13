import os
from aiogram import Router, F, Bot
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from datetime import datetime

import ai_service
import obsidian

router = Router()

BTN_CLEAR_CONTEXT = "🧹 Очистить контекст диалога"

def get_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_CLEAR_CONTEXT)]],
        resize_keyboard=True,
        persistent=True
    )

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.update_data(history=[])
    await message.answer(
        "Привет! Я твой Второй Мозг — ИИ Агент. 🧠\n\n"
        "Я умею сам создавать, находить и изменять заметки. Просто напиши мне, что ты хочешь сделать:\n"
        "- Сохрани идею для проекта...\n"
        "- Найди, что я записывал про дизайн...\n"
        "- Отметь выполненной задачу X в файле Y...",
        reply_markup=get_keyboard(),
        parse_mode="Markdown"
    )

@router.message(F.text == BTN_CLEAR_CONTEXT)
async def clear_context(message: Message, state: FSMContext):
    await state.update_data(history=[])
    await message.answer("🧹 Память очищена. Я готов к новой теме!", reply_markup=get_keyboard())

async def process_user_input(text: str, message: Message, state: FSMContext, wait_msg: Message = None):
    data = await state.get_data()
    history = data.get("history", [])
    
    history.append({"role": "user", "content": text})
    
    if not wait_msg:
        wait_msg = await message.answer("💭 Анализирую запрос...")
        
    try:
        answer, new_history = await ai_service.agent_chat(history)
        await state.update_data(history=new_history)
        await wait_msg.edit_text(answer, parse_mode="Markdown")
    except Exception as e:
        await wait_msg.edit_text(f"❌ Ошибка агента: {e}")

@router.message(F.text)
async def handle_text(message: Message, state: FSMContext):
    await process_user_input(message.text, message, state)

@router.message(F.voice)
async def handle_voice(message: Message, bot: Bot, state: FSMContext):
    msg = await message.answer("📥 Скачиваю голосовое сообщение...")
    file_id = message.voice.file_id
    file = await bot.get_file(file_id)
    
    os.makedirs("temp", exist_ok=True)
    temp_ogg_path = f"temp/{file_id}.ogg"
    await bot.download_file(file.file_path, temp_ogg_path)
    
    await msg.edit_text("🎙 Транскрибирую аудио...")
    try:
        raw_text = await ai_service.transcribe_audio(temp_ogg_path)
        await msg.edit_text("🧠 Структурирую аудио...")
        structured_text = await ai_service.structure_raw_text(raw_text)
        
        # Отправляем структурированный текст в Агента
        await process_user_input(structured_text, message, state, wait_msg=msg)
    except Exception as e:
        await msg.edit_text(f"❌ Ошибка при обработке аудио: {e}")
    finally:
        if os.path.exists(temp_ogg_path):
            os.remove(temp_ogg_path)

@router.message(F.photo)
async def handle_photo(message: Message, bot: Bot, state: FSMContext):
    msg = await message.answer("📥 Сохраняю фото...")
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    
    os.makedirs("temp", exist_ok=True)
    temp_path = f"temp/{photo.file_id}.jpg"
    await bot.download_file(file.file_path, temp_path)
    
    try:
        saved_name = obsidian.save_attachment(temp_path, "photo.jpg")
        caption = message.caption or "Фото с телефона"
        
        await msg.edit_text("👁 Анализирую изображение (Vision)...")
        analysis_result = await ai_service.analyze_image(temp_path, caption)
        
        time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        note_content = f"---\ncreated: '{time_now}'\ntags: [фото, медиа, vision]\ntype: 'фото'\n---\n# Анализ изображения\n\n![[{saved_name}]]\n\n{analysis_result}"
        filename = obsidian.save_note(f"0-Inbox/Photo_{saved_name}.md", note_content)
        await msg.edit_text(f"✅ Фото сохранено и проанализировано: `{filename}`", parse_mode="Markdown")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@router.message(F.video)
async def handle_video(message: Message, bot: Bot, state: FSMContext):
    msg = await message.answer("📥 Сохраняю видео...")
    file = await bot.get_file(message.video.file_id)
    
    os.makedirs("temp", exist_ok=True)
    temp_path = f"temp/{message.video.file_id}.mp4"
    await bot.download_file(file.file_path, temp_path)
    
    try:
        saved_name = obsidian.save_attachment(temp_path, "video.mp4")
        caption = message.caption or "Видео с телефона"
        time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        note_content = f"---\ncreated: '{time_now}'\ntags: [видео, медиа]\ntype: 'видео'\n---\n# Видео\n\n![[{saved_name}]]\n\n{caption}"
        filename = obsidian.save_note(f"0-Inbox/Video_{saved_name}.md", note_content)
        await msg.edit_text(f"✅ Видео сохранено: `{filename}`", parse_mode="Markdown")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@router.message(F.document)
async def handle_document(message: Message, bot: Bot, state: FSMContext):
    msg = await message.answer("📥 Сохраняю файл...")
    file = await bot.get_file(message.document.file_id)
    
    os.makedirs("temp", exist_ok=True)
    temp_path = f"temp/{message.document.file_id}_{message.document.file_name}"
    await bot.download_file(file.file_path, temp_path)
    
    try:
        saved_name = obsidian.save_attachment(temp_path, message.document.file_name or "file")
        caption = message.caption or f"Файл: {message.document.file_name}"
        time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        note_content = f"---\ncreated: '{time_now}'\ntags: [файл, документ]\ntype: 'документ'\n---\n# Файл\n\n![[{saved_name}]]\n\n{caption}"
        filename = obsidian.save_note(f"0-Inbox/File_{saved_name}.md", note_content)
        await msg.edit_text(f"✅ Файл сохранен: `{filename}`", parse_mode="Markdown")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
