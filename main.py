from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.dispatcher.router import Router
from reverso_context_api import Client
import asyncio
import csv
import os
from dotenv import load_dotenv, find_dotenv

# Загрузка переменных окружения (токен телеграм-бота)
load_dotenv(find_dotenv())

# Инициализация бота и диспетчера
bot = Bot(os.getenv("API_TOKEN"))
dp = Dispatcher()

# Переводчик
client = Client("en", "ru")

# Создаем объект Router
router = Router()

# Создание карточки Anki
def create_anki_card_csv(response):
    filename = "anki_import.csv"
    with open(filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, quoting=csv.QUOTE_NONE, delimiter=' ', escapechar=' ')
        writer.writerow([response])
    print(f"Карточка добавлена в CSV.")
    

# Хендлер для обработки сообщений
@router.message()
async def translate_word(message: Message):
    user_word = message.text.strip()  # Извлечение слова из сообщения пользователя
    
    try:
        # Получение переводов через Reverso API
        translations = list(client.get_translations(user_word))
        del translations[5:-1]
        if translations:
            response = f"{user_word}\t{', '.join(translations)}"
            
            # Ограничиваем количество контекстов, например, до 3
            context_count = 0
            for context in client.get_translation_samples(user_word, cleanup=True):
                if context_count >= 3:
                    break  # Прекращаем после получения 3 контекстов
                source_sentence, target_sentence = context
                response += f"\tПример: {source_sentence} - {target_sentence}"
                context_count += 1

            if context_count == 0:
                response += "\tКонтекстов не найдено."
            
            # Если перевод найден, записываем в файл и импортируем
            create_anki_card_csv(response)
        else:
            response = f"Не удалось найти перевод для '{user_word}'."
    
    except Exception as e:
        # Обработка всех возможных ошибок, включая ошибки API
        response = f"Произошла ошибка при переводе: {str(e)}"

    await message.reply(response)

async def main():
    # Регистрация Router в диспетчере
    dp.include_router(router)
    
    # Запуск поллинга
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())