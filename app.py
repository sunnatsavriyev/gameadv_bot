import os
import django
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.contrib.fsm_storage.memory import MemoryStorage  
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext
from aiogram.types import ContentType
from asgiref.sync import sync_to_async
from django.db import close_old_connections
from aiogram.dispatcher.filters import Text
from django.core.files.storage import default_storage
from aiogram import types
from aiogram.types import InputFile



# Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from home.models import TelegramUser, GameAdv
from hendlers.form import GameAdvForm

# Bot token
BOT_TOKEN = os.getenv('BOT_TOKEN')
ALLOWED_GAMES = ["Pubg", "Football"]
# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())




# Bu Start uchun handler
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    telegram_id = message.from_user.id
    
    user_exists = await sync_to_async(TelegramUser.objects.filter(telegram_id=telegram_id).exists)()

    if user_exists:
        button1 = KeyboardButton("O'yin qo'shish ")
        button2 = KeyboardButton("Pubg akauntlar 🔫")
        button3 = KeyboardButton("Futbol akauntlar ⚽️")
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(button1, button2, button3)
        await message.answer("Sizning kontaktlaringiz allaqachon saqlangan.", reply_markup=keyboard)
    else:
        button = KeyboardButton("Send Contact", request_contact=True)
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(button)
        await message.answer("Iltimos, kontaktingizni ulashing!", reply_markup=keyboard)




#Bu esa kontaktlarni olish uchun handler

@dp.message_handler(content_types=types.ContentType.CONTACT)
async def contact_handler(message: types.Message):
    contact = message.contact
    telegram_id = contact.user_id
    name = contact.first_name
    phone_number = contact.phone_number


    user, created = await sync_to_async(TelegramUser.objects.get_or_create)(
        telegram_id=telegram_id,
        defaults={
            'name': name,
            'phone_number': phone_number,
        }
    )

    if not created:
        user.name = name
        user.phone_number = phone_number
        await sync_to_async(user.save)()

    button1 = KeyboardButton("O'yin qo'shish")
    button2 = KeyboardButton("Pubg akauntlar 🔫")
    button3 = KeyboardButton("Futbol akauntlar ⚽️")
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(button1, button2, button3)
    remove_keyboard = ReplyKeyboardRemove()
    
    await message.answer(f"Raxmat, {name}! Sizning kontaktingiz saqlandi", reply_markup=remove_keyboard)
    await message.answer("Endi tanlang:", reply_markup=keyboard)






#Bu O'yin qo'shish uchun class handler


@dp.message_handler(lambda message: message.text == "O'yin qo'shish")
async def game_adv_start(message: types.Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [
        KeyboardButton(text="Pubg 🔫"),
        KeyboardButton(text="Futbol ⚽️")
    ]
    keyboard.add(*buttons)
    await message.reply("Qaysi o'yinni qo'shmoqchisiz?", reply_markup=keyboard)
    await GameAdvForm.name.set()






# Handle game name and degree
@dp.message_handler(state=GameAdvForm.name)
async def process_name(message: types.Message, state: FSMContext):
    game_name = message.text
    
    if game_name in ['Pubg 🔫', 'Futbol ⚽️']:
        game_name = game_name.split(' ')[0]  # Extract game name
        await state.update_data(name=game_name)
        
        await message.reply("Ajoyib! Endi darajangizni kiriting:", reply_markup=ReplyKeyboardRemove())
        await GameAdvForm.degree.set()
    else:
        await message.reply("Iltimos, o'yin tanlash uchun tugmalardan birini bosing.")





# Handle degree and prompt for image upload
@dp.message_handler(state=GameAdvForm.degree)
async def process_degree(message: types.Message, state: FSMContext):
    await state.update_data(degree=message.text)
    await message.reply("Keyingi qadam, iltimos rasm yuklang:")
    await GameAdvForm.image.set()






# Handle image upload and prompt for additional information
@dp.message_handler(content_types=['photo'], state=GameAdvForm.image)
async def process_image(message: types.Message, state: FSMContext):
    photo = message.photo[-1]  # Get the highest resolution photo
    file_path = f"media/{photo.file_id}.jpg"
    await photo.download(destination=file_path)
    
    await state.update_data(image=file_path)

    # Ask for additional information with "Ha" and "Yo'q" buttons
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [
        KeyboardButton(text="Ha"),
        KeyboardButton(text="Yo'q")
    ]
    keyboard.add(*buttons)
    await message.reply("Qo'shimcha ma'lumotlar bormi?", reply_markup=keyboard)
    await GameAdvForm.qoshimchalar_input.set()




# Handle the response to the additional information prompt
@dp.message_handler(lambda message: message.text in ["Ha", "Yo'q"], state=GameAdvForm.qoshimchalar_input)
async def process_qoshimchalar(message: types.Message, state: FSMContext):
    if message.text == "Ha":
        await message.reply("Qo'shimcha ma'lumot kiriting:", reply_markup=ReplyKeyboardRemove())
        await GameAdvForm.qoshimchalar_input.set()  # Davomiy input uchun holatni o'rnating
    elif message.text == "Yo'q":
        await save_game_adv(message, state)

# Handle the actual input of additional information
@dp.message_handler(state=GameAdvForm.qoshimchalar_input)
async def process_qoshimchalar_input(message: types.Message, state: FSMContext):
    await state.update_data(qoshimchalar=message.text)
    await save_game_adv(message, state)

async def save_game_adv(message: types.Message, state: FSMContext):
    try:
        user_data = await state.get_data()

        # TelegramUser obyektini olish
        telegram_user = await TelegramUser.objects.aget(telegram_id=message.from_user.id)
        
        new_game_adv = GameAdv(
            name=user_data['name'],
            degree=user_data['degree'],
            image=user_data['image'],
            qoshimchalar=user_data.get('qoshimchalar', ""),
            user=telegram_user  # TelegramUser obyektini tayinlaymiz
        )
        new_game_adv.save()

        await message.reply("Reklamangiz muvaffaqiyatli qo'shildi! Raxmat!", reply_markup=ReplyKeyboardRemove())
        
        # Yakuniy menyuni uchta variant bilan jo'nating
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = [
            KeyboardButton(text="O'yin qo'shish"),
            KeyboardButton(text="Pubg akauntlar 🔫"),
            KeyboardButton(text="Futbol akauntlar ⚽️")
        ]
        keyboard.add(*buttons)
        await message.reply("Yana nima qilishni xohlaysiz?", reply_markup=keyboard)
        await state.finish()

    except TelegramUser.DoesNotExist:
        await message.reply("Foydalanuvchi topilmadi. Iltimos, qaytadan urinib ko'ring.")
        await state.finish()
    except Exception as e:
        await message.reply(f"Xatolik yuz berdi: {str(e)}")
        await state.finish()




@dp.message_handler(Text(equals="Pubg akauntlar 🔫"))
async def pubg_accounts(message: types.Message):
    close_old_connections()
    
    try:
        game_ads = await sync_to_async(lambda: GameAdv.objects.filter(name__iexact="Pubg").all())()
        
        if not game_ads:
            await message.reply("Hozircha 'Pubg' reklamalari mavjud emas.")
            return

        for ad in game_ads:
            response = f"Nom: {ad.name}\n" \
                       f"Daraja: {ad.degree}\n" \
                       f"Akaunt egasi: {ad.user.name}\n" \
                       f"Telefon: {ad.user.phone_number}\n\n"
            
            await message.reply(response)
            
            # Send the image if it exists
            image_path = ad.image.name  # Assuming 'image' is a FileField in your model
            if image_path:
                # Get the absolute path to the image file
                image_full_path = default_storage.path(image_path)
                # Send the image
                image = InputFile(image_full_path)
                await message.reply_photo(photo=image)
                    
    except Exception as e:
        await message.reply(f"Xato yuz berdi: {str(e)}")

@dp.message_handler(Text(equals="Futbol akauntlar ⚽️"))
async def football_accounts(message: types.Message):
    close_old_connections()
    
    try:
        game_ads = await sync_to_async(lambda: GameAdv.objects.filter(name__iexact="Futbol").all())()
        
        if not game_ads:
            await message.reply("Hozircha 'Futbol' reklamalari mavjud emas.")
            return

        for ad in game_ads:
            response = f"Nom: {ad.name}\n" \
                       f"Daraja: {ad.degree}\n" \
                       f"Akaunt egasi: {ad.user.name}\n" \
                       f"Telefon: {ad.user.phone_number}\n\n"
            
            await message.reply(response)
            
            # Send the image if it exists
            image_path = ad.image.name  # Assuming 'image' is a FileField in your model
            if image_path:
                # Get the absolute path to the image file
                image_full_path = default_storage.path(image_path)
                # Send the image
                image = InputFile(image_full_path)
                await message.reply_photo(photo=image)
                    
    except Exception as e:
        await message.reply(f"Xato yuz berdi: {str(e)}")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
