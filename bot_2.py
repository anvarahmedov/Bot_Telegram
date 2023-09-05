from aiogram import executor, Bot, types, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.filters.state import State, StatesGroup
from config import TOKEN_API
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from sqlite import db_start, create_profile, update_profile

bot = Bot(TOKEN_API)

storage = MemoryStorage()

dp = Dispatcher(bot=bot,
                storage=storage)


class BotStatesGroup(StatesGroup):
    initial_choice = State()
    course_choice = State()
    python_course = State()
    java_course = State()
    python_name = State()
    python_address = State()
    python_age = State()
    java_name = State()
    java_address = State()
    java_age = State()


async def on_startup(_):
    await db_start()


def get_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("Biz haqimizda"), KeyboardButton("Bizning kurslarimiz"))
    return kb


def get_ikb() -> InlineKeyboardMarkup:
    ikb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton("Python", callback_data="python"),
                                                 InlineKeyboardButton("Java", callback_data="java")],
                                                [InlineKeyboardButton("Boshidan boshlash", callback_data="start_over")]])
    return ikb


def cancel_kb(state) -> ReplyKeyboardMarkup:
    cancel_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    if state == BotStatesGroup.initial_choice:
        cancel_keyboard.add(KeyboardButton("Orqaga"))
    elif state == BotStatesGroup.course_choice:
        cancel_keyboard.add(KeyboardButton("Orqaga"),KeyboardButton("Boshidan boshlash"))
    elif state == BotStatesGroup.python_course or state == BotStatesGroup.java_course:
        cancel_keyboard.add(KeyboardButton("Boshidan boshlash."))
    return cancel_keyboard


def get_python_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("Python kursi dars jadvali"),
                                                       KeyboardButton("Python kursiga a'zo bo'lish"))
    return kb


def get_java_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("Java kursi dars jadvali"),
                                                       KeyboardButton("Java kursiga a'zo bo'lish"))
    return kb


@dp.message_handler(Text(equals="Boshidan boshlash."), state="*")
async def start_over_auth(message: types.Message, state: FSMContext):
    await state.finish()
    await cmd_start(message)


@dp.message_handler(commands=["start"], state=None)
async def cmd_start(message: types.Message) -> None:
    await message.answer("Bizning botimizga xush kelibsiz!", reply_markup=get_kb())
    await BotStatesGroup.initial_choice.set()
    await create_profile(user_id=message.from_user.id)


@dp.message_handler(commands=["start"], state='*')
async def cmd_start_duplicate(message: types.Message) -> None:
    await message.answer("Bot allaqachon ishga tushgan. Botni qayta ishga tushirish uchun Boshidan boshlash tugmasini bosing.",
                         reply_markup=cancel_kb(BotStatesGroup.python_course))
    await message.delete()

@dp.message_handler(state=BotStatesGroup.initial_choice)
async def initial_state_handler(message: types.Message, state: FSMContext):
    if message.text == "Biz haqimizda":
        return await bot.send_photo(chat_id=message.chat.id,
                            photo="https://marketbusinessnews.com/wp-content/uploads/2018/11/Information-Technology.jpg",
                            caption="Bu yerda biz haqimizdagi matn bo'ladi.",
                            reply_markup=cancel_kb(BotStatesGroup.initial_choice))
    elif message.text == "Bizning kurslarimiz":
        await BotStatesGroup.next()
        return await message.answer("Quyidagi kurslardan birini tanlang.", reply_markup=get_ikb())
    elif message.text == "Orqaga":
        await state.finish()
        return await cmd_start(message)
    await message.answer("Noto'g'ri yozuv")


@dp.callback_query_handler(state=BotStatesGroup.course_choice)
async def course_cb_handler(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == "start_over":
        return await cmd_start(callback.message)
    elif callback.data == "python":
        await BotStatesGroup.python_course.set()
        return await callback.message.answer(
            f"{callback.data.capitalize()} kursi dars jadvalini bilib oling yoki kursga a'zo bo'ling",
            reply_markup=get_python_kb())
    await callback.message.answer(f"{callback.data.capitalize()} kursi dars jadvalini bilib oling yoki kursga a'zo bo'ling",
                                     reply_markup=get_java_kb())
    await BotStatesGroup.java_course.set()


@dp.message_handler(Text(equals="Python kursi dars jadvali"), state=BotStatesGroup.python_course)
async def python_schedule(message: types.Message):
    await message.answer("Bu yerda python kursi dars jadvali keladi.", reply_markup=cancel_kb(BotStatesGroup.course_choice))


@dp.message_handler(lambda message: message.text == "Orqaga" or message.text =="Boshidan boshlash",
                    state=BotStatesGroup.python_course)
async def back_python_handler(message: types.Message, state: FSMContext):
    if message.text == "Orqaga":
        return await message.answer("Python kursi dars jadvalini bilib oling yoki kursga a'zo bo'ling",
            reply_markup=get_python_kb())
    await state.finish()
    await cmd_start(message)


@dp.message_handler(Text(equals="Python kursiga a'zo bo'lish"), state=BotStatesGroup.python_course)
async def python_auth(message: types.Message, state: FSMContext):
    await message.answer("Python kursiga a'zo bolish uchun birinchi ism familiyangizni kiriting.", reply_markup=cancel_kb(BotStatesGroup.python_course))
    async with state.proxy() as data:
        data["course"] = "python"
    await BotStatesGroup.python_name.set()


@dp.message_handler(lambda message: not message.text.isalpha or message.text.count(" ") == 0,
                    state=BotStatesGroup.python_name)
async def python_name_check(message: types.Message):
    await message.answer("Bu sizning to'liq ismingiz emas yoki haqiqiy ismingizni kiritmadingiz.")


@dp.message_handler(state=BotStatesGroup.python_name)
async def python_address_auth(message: types.Message, state: FSMContext):
    await message.answer("Ismingiz bazaga kiritildi. Endi manzilingizni kiriting.")
    async with state.proxy() as data:
        data["name"] = message.text
    await BotStatesGroup.next()


@dp.message_handler(state=BotStatesGroup.python_address)
async def python_age_auth(message: types.Message, state: FSMContext):
    await message.answer("Manzilingiz ham bazaga kiritildi. Endi yoshingizni kiriting.")
    async with state.proxy() as data:
        data["address"] = message.text
    await BotStatesGroup.next()


@dp.message_handler(lambda message: not message.text.isdigit() or float(message.text) > 100, state=BotStatesGroup.python_age)
async def python_age_check(message: types.Message):
    await message.answer("Haqiqiy yoshingizni kiriting.")


@dp.message_handler(state=BotStatesGroup.python_age)
async def end_python_auth(message: types.Message, state: FSMContext):
    await message.answer("Sizning anketangiz muvaffaqiyatli yaratildi. Quyida siz kiritgan ma'lumotlar")
    async with state.proxy() as data:
        data["age"] = message.text
        await message.answer(f"Siz yozilgan kurs:{data['course']}. Sizning to'liq ismingiz:{data['name']}. Sizning manzilingiz:{data['address']}. Sizning yoshingiz:{data['age']}")
    await update_profile(state, user_id=message.from_user.id)

    await state.finish()


@dp.message_handler(Text(equals="Java kursi dars jadvali"), state=BotStatesGroup.java_course)
async def java_schedule(message: types.Message):
    await message.answer("Bu yerda java kursi dars jadvali keladi.", reply_markup=cancel_kb(BotStatesGroup.course_choice))


@dp.message_handler(lambda message: message.text == "Orqaga" or message.text =="Boshidan boshlash",
                    state=BotStatesGroup.java_course)
async def back_java_handler(message: types.Message, state: FSMContext):
    if message.text == "Orqaga":
        return await message.answer("Java kursi dars jadvalini bilib oling yoki kursga a'zo bo'ling",
            reply_markup=get_java_kb())
    await state.finish()
    await cmd_start(message)


@dp.message_handler(Text(equals="Java kursiga a'zo bo'lish"), state=BotStatesGroup.java_course)
async def java_auth(message: types.Message, state: FSMContext):
    await message.answer("Java kursiga a'zo bolish uchun birinchi ism familiyangizni kiriting.", reply_markup=cancel_kb(BotStatesGroup.java_course))
    async with state.proxy() as data:
        data["course"] = "java"
    await BotStatesGroup.java_name.set()


@dp.message_handler(lambda message: not message.text.isalpha or message.text.count(" ") < 1,
                    state=BotStatesGroup.java_name)
async def java_name_check(message: types.Message):
    await message.answer("Bu sizning to'liq ismingiz emas yoki noto'g'ri ism kiritdingiz.")


@dp.message_handler(state=BotStatesGroup.java_name)
async def java_address_auth(message: types.Message, state: FSMContext):
    await message.answer("Ismingiz bazaga kiritildi. Endi manzilingizni kiriting.")
    async with state.proxy() as data:
        data["name"] = message.text
    await BotStatesGroup.next()


@dp.message_handler(state=BotStatesGroup.java_address)
async def java_age_auth(message: types.Message, state: FSMContext):
    await message.answer("Manzilingiz ham bazaga kiritildi. Endi yoshingizni kiriting.")
    async with state.proxy() as data:
        data["address"] = message.text
    await BotStatesGroup.next()


@dp.message_handler(lambda message: not message.text.isdigit() or float(message.text) > 100, state=BotStatesGroup.java_age)
async def java_age_check(message: types.Message):
    await message.answer("Haqiqiy yoshingizni kiriting.")


@dp.message_handler(state=BotStatesGroup.java_age)
async def end_java_auth(message: types.Message, state: FSMContext):
    await message.answer("Sizning anketangiz muvaffaqiyatli yaratildi. Quyida siz kiritgan ma'lumotlar")
    async with state.proxy() as data:
        data["age"] = message.text
        await message.answer(f"Siz yozilgan kurs:{data['course']}. Sizning to'liq ismingiz:{data['name']}. Sizning manzilingiz:{data['address']}. Sizning yoshingiz:{data['age']}")
    await update_profile(state, user_id=message.from_user.id)
    await state.finish()

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
