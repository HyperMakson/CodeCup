import asyncio
import logging
import sqlite3
from config_reader import config
from datetime import datetime
from pytz import timezone
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram import F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

logging.basicConfig(level=logging.INFO)
bot = Bot(token=config.bot_token.get_secret_value())
dp = Dispatcher()

class InfoEmployees(StatesGroup):
    input_last_name = State()
    input_name = State()
    input_middle_name = State()
    input_post = State()
    input_project = State()
    input_avatar = State()
    del_employee = State()
    confirm_del = State()
    confirm_del_chose = State()
    edit_people = State()
    confirm_edit = State()
    input_edit = State()
    change_edit = State()
    input_search = State()

@dp.message(Command("start"))
@dp.message(F.text.lower() == "начать")
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(
        text="Добавить сотрудника",
        callback_data="add")
    )
    builder.row(types.InlineKeyboardButton(
        text="Удалить сотрудника",
        callback_data="delete")
    )
    builder.row(types.InlineKeyboardButton(
        text="Редактировать сотрудника",
        callback_data="edit")
    )
    builder.row(types.InlineKeyboardButton(
        text="Поиск сотрудника",
        callback_data="search")
    )
    await message.answer(
        "Это Telegram-бот, который может добавлять, удалять, "
        "редактировать и искать информацию о сотрудниках\n"
        "Чтобы начать заново напишите 'Начать' или нажмите /start\n"
        "Для отмены действий напишите 'Отмена' или нажмите /cancel",
        reply_markup=builder.as_markup()
    )

@dp.message(Command("cancel"))
@dp.message(F.text.lower() == "отмена")
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Действие отменено\n"
        "Чтобы начать заново напишите 'Начать' или нажмите /start",
        reply_markup=ReplyKeyboardRemove()
    )






@dp.callback_query(F.data == "add")
async def add_employee(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.reply(
        "Для того, чтобы добавить сотрудника, "
        "необходимо заполнить некоторые поля:\n"
        "Фамилия\nИмя\nОтчество\nДолжность\nПроект"
    )
    await callback.message.answer("Введите вашу фамилию")
    await state.set_state(InfoEmployees.input_last_name)
    await callback.answer()

@dp.message(InfoEmployees.input_last_name)
async def add_last_name(message: Message, state: FSMContext):
    await state.update_data(last_name=message.text.lower())
    await message.answer("Введите ваше имя")
    await state.set_state(InfoEmployees.input_name)

@dp.message(InfoEmployees.input_name)
async def add_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.lower())
    await message.answer("Введите ваше отчество")
    await state.set_state(InfoEmployees.input_middle_name)

@dp.message(InfoEmployees.input_middle_name)
async def add_middle_name(message: Message, state: FSMContext):
    await state.update_data(middle_name=message.text.lower())
    await message.answer("Введите вашу должность")
    await state.set_state(InfoEmployees.input_post)

@dp.message(InfoEmployees.input_post)
async def add_post(message: Message, state: FSMContext):
    await state.update_data(post=message.text.lower())
    await message.answer("Введите ваш проект")
    await state.set_state(InfoEmployees.input_project)

@dp.message(InfoEmployees.input_project)
async def add_project(message: Message, state: FSMContext):
    await state.update_data(project=message.text.lower())
    await message.answer("Отправьте свою аватарку")
    await state.set_state(InfoEmployees.input_avatar)

@dp.message(InfoEmployees.input_avatar, F.photo)
async def add_avatar(message: Message, state: FSMContext, bot: Bot):
    await bot.download(message.photo[-1])
    await state.update_data(avatar=message.photo[-1].file_id)
    time_now = datetime.now(timezone('Europe/Moscow')).strftime("%d/%m/%Y %H:%M:%S")
    await state.update_data(date=time_now)
    user_data = await state.get_data()
    try:
        connection = sqlite3.connect('employees.db')
        cursor = connection.cursor()
        add_info = cursor.execute(
            "INSERT INTO Info (`Фамилия`, `Имя`, `Отчество`, `Должность`, `Проект`, `Аватарка`, `Дата прихода`) "
            "VALUES (?, ?, ?, ?, ?, ?, ?);",
            (
                user_data['last_name'], user_data['name'], user_data['middle_name'],
                user_data['post'], user_data['project'], user_data['avatar'], user_data['date']
            )
        )
        connection.commit()
        connection.close()
        await message.answer(
            "Данные сотрудника были добавлены\n\n"
            "Если вы хотите выполнить другие действия, то "
            "напишите 'Начать' или нажмите /start",
            reply_markup=ReplyKeyboardRemove()
        )
    except sqlite3.Error:
        await message.answer(
            "Произошла ошибка\n"
            "Попробуйте сначала, написав 'Начать' или нажав /start"
        )
    await state.clear()





@dp.callback_query(F.data == "delete")
async def delete_employee(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.reply(
        "Чтобы удалить сотрудника, необходимо ввести его фамилию"
    )
    await callback.message.answer("Введите фамилию")
    await state.set_state(InfoEmployees.del_employee)
    await callback.answer()

@dp.message(InfoEmployees.del_employee)
async def del_record(message: Message, state: FSMContext):
    await state.update_data(delete_record=message.text.lower())
    last_name_data = await state.get_data()
    try:
        connection = sqlite3.connect('employees.db')
        cursor = connection.cursor()
        select_for_del = cursor.execute(
            "SELECT * FROM Info WHERE `Фамилия` = ?",
            (last_name_data['delete_record'],)
        )
        record = cursor.fetchall()
        length = len(record)
        name_col = cursor.execute("SELECT * FROM Info")
        columns = [desc[0] for desc in name_col.description]
        col = 0
        for column in select_for_del.description:
            col += 1
        del_info = ''
        if length == 1:
            for i in record:
                for j in range(0, col):
                    if j == 6:
                        await state.update_data(id_for_ph=str(i[j]))
                    else:
                        del_info += columns[j] + ': ' + str(i[j]) + '\n'
            connection.close()
            input_data = await state.get_data()
            await message.reply_photo(
                caption=f"Был найден данный сотрудник:\n\n"
                    f"{del_info}",
                photo=input_data['id_for_ph']
            )
            kb = [
                [types.KeyboardButton(text="Да", callback_data="yes_delete")],
                [types.KeyboardButton(text="Нет", callback_data="no_delete")]
            ]
            keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
            await message.answer(
                text="Вы хотите удалить именно этого сотрудника?",
                reply_markup=keyboard
            )
            await state.set_state(InfoEmployees.confirm_del)
        elif length > 1:
            for i in record:
                for j in range(0, col):
                    if j == 6:
                        await state.update_data(id_for_ph=str(i[j]))
                    else:
                        del_info += columns[j] + ': ' + str(i[j]) + '\n'
                input_data = await state.get_data()
                await message.reply_photo(
                    caption=f"Был найден данный сотрудник:\n\n"
                        f"{del_info}",
                    photo=input_data['id_for_ph']
                )
                del_info = ''
            connection.close()
            builder = ReplyKeyboardBuilder()
            for i in record:
                for j in range(0, 1):
                    builder.add(types.KeyboardButton(text=str(i[j])))
            builder.adjust(4)
            await message.answer(
                text="Сотрудника с каким ID вы хотите удалить?",
                reply_markup=builder.as_markup(resize_keyboard=True)
            )
            await state.set_state(InfoEmployees.confirm_del_chose)
        else:
            await state.clear()
            await message.answer(
                "Данный сотрудник не был найден\n\n"
                "Если вы хотите выполнить другие действия, то "
                "напишите 'Начать' или нажмите /start",
                reply_markup=ReplyKeyboardRemove()
            )
    except sqlite3.Error:
        await message.answer(
            "Произошла ошибка\n"
            "Попробуйте сначала, написав 'Начать' или нажав /start"
        )

@dp.message(InfoEmployees.confirm_del)
async def confirm_delete(message: Message, state: FSMContext):
    await state.update_data(chose=message.text.lower())
    chose_del = await state.get_data()
    if chose_del['chose'] == 'да':
        try:
            connection = sqlite3.connect('employees.db')
            cursor = connection.cursor()
            delete = cursor.execute(
                "DELETE FROM Info WHERE `Фамилия` = ?",
                (chose_del['delete_record'],)
            )
            connection.commit()
            connection.close()
            await message.answer(
                "Данный сотрудник был удалён\n\n"
                "Если вы хотите выполнить другие действия, то "
                "напишите 'Начать' или нажмите /start",
                reply_markup=ReplyKeyboardRemove()
            )
        except sqlite3.Error:
            await message.answer(
                "Произошла ошибка\n"
                "Попробуйте сначала, написав 'Начать' или нажав /start"
            )
        await state.clear()
    else:
        await state.clear()
        await message.answer(
            "Действие отменено\n"
            "Чтобы начать заново напишите 'Начать' или нажмите /start"
        )

@dp.message(InfoEmployees.confirm_del_chose)
async def confirm_delete(message: Message, state: FSMContext):
    await state.update_data(ids=message.text.lower())
    id_del = await state.get_data()
    try:
        connection = sqlite3.connect('employees.db')
        cursor = connection.cursor()
        delete = cursor.execute(
            "DELETE FROM Info WHERE ID = ?",
            (id_del['ids'],)
        )
        connection.commit()
        connection.close()
        await message.answer(
            "Данный сотрудник был удалён\n\n"
            "Если вы хотите выполнить другие действия, то "
            "напишите 'Начать' или нажмите /start",
            reply_markup=ReplyKeyboardRemove()
        )
    except sqlite3.Error:
        await message.answer(
            "Произошла ошибка\n"
            "Попробуйте сначала, написав 'Начать' или нажав /start"
        )
    await state.clear()






@dp.callback_query(F.data == "edit")
async def edit_employee(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.reply(
        "Чтобы изменить сотрудника, необходимо ввести его фамилию"
    )
    await callback.message.answer("Введите фамилию")
    await state.set_state(InfoEmployees.edit_people)
    await callback.answer()

@dp.message(InfoEmployees.edit_people)
async def edit_record(message: Message, state: FSMContext):
    await state.update_data(ed_record=message.text.lower())
    last_name_data_ed = await state.get_data()
    try:
        connection = sqlite3.connect('employees.db')
        cursor = connection.cursor()
        select_for_ed = cursor.execute(
            "SELECT * FROM Info WHERE `Фамилия` = ?",
            (last_name_data_ed['ed_record'],)
        )
        record = cursor.fetchall()
        length = len(record)
        name_col = cursor.execute("SELECT * FROM Info")
        columns = [desc[0] for desc in name_col.description]
        col = 0
        for column in select_for_ed.description:
            col += 1
        ed_info = ''
        if length == 1:
            for i in record:
                for j in range(0, col):
                    if j == 0:
                        await state.update_data(id_for_upd=str(i[j]))
                    if j == 6:
                        await state.update_data(id_for_ph=str(i[j]))
                    else:
                        ed_info += columns[j] + ': ' + str(i[j]) + '\n'
            connection.close()
            input_data = await state.get_data()
            await message.reply_photo(
                caption=f"Был найден данный сотрудник:\n\n"
                    f"{ed_info}",
                photo=input_data['id_for_ph']
            )
            kb = [
                [types.KeyboardButton(text="Да", callback_data="yes_edit")],
                [types.KeyboardButton(text="Нет", callback_data="no_edit")]
            ]
            keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
            await message.answer(
                text="Вы хотите изменить именно этого сотрудника?",
                reply_markup=keyboard
            )
            await state.set_state(InfoEmployees.confirm_edit)
        elif length > 1:
            for i in record:
                for j in range(0, col):
                    if j == 6:
                        await state.update_data(id_for_ph=str(i[j]))
                    else:
                        ed_info += columns[j] + ': ' + str(i[j]) + '\n'
                input_data = await state.get_data()
                await message.reply_photo(
                    caption=f"Был найден данный сотрудник:\n\n"
                        f"{ed_info}",
                    photo=input_data['id_for_ph']
                )
                ed_info = ''
            connection.close()
            builder = ReplyKeyboardBuilder()
            for i in record:
                for j in range(0, 1):
                    builder.add(types.KeyboardButton(text=str(i[j])))
            builder.adjust(4)
            await message.answer(
                text="Сотрудника с каким ID вы хотите изменить?",
                reply_markup=builder.as_markup(resize_keyboard=True)
            )
            await state.set_state(InfoEmployees.confirm_edit)
        else:
            await state.clear()
            await message.answer(
                "Данный сотрудник не был найден\n\n"
                "Если вы хотите выполнить другие действия, то "
                "напишите 'Начать' или нажмите /start",
                reply_markup=ReplyKeyboardRemove()
            )
    except sqlite3.Error as err:
        print(err)
        await message.answer(
            "Произошла ошибка\n"
            "Попробуйте сначала, написав 'Начать' или нажав /start"
        )

@dp.message(InfoEmployees.confirm_edit)
async def chose_what_edit(message: Message, state: FSMContext):
    await state.update_data(chose=message.text.lower())
    chose_ed = await state.get_data()
    if chose_ed['chose'] == 'нет':
        await state.clear()
        await message.answer(
            "Действие отменено\n"
            "Чтобы начать заново напишите 'Начать' или нажмите /start"
        )
    else:
        if chose_ed['chose'] != 'да':
            await state.update_data(id_for_upd=message.text.lower())
        connection = sqlite3.connect('employees.db')
        cursor = connection.cursor()
        select_for_ed = cursor.execute("SELECT * FROM Info")
        columns = [desc[0] for desc in select_for_ed.description]
        builder = ReplyKeyboardBuilder()
        for i in columns:
            builder.add(types.KeyboardButton(text=str(i)))
        builder.adjust(4)
        await message.answer(
            "Выберите какое поле вы хотите изменить",
            reply_markup=builder.as_markup(resize_keyboard=True)
        )
        await state.set_state(InfoEmployees.input_edit)


@dp.message(InfoEmployees.input_edit)
async def input_edit_func(message: Message, state: FSMContext):
    await state.update_data(input_edit_data=message.text)
    tmp = await state.get_data()
    if tmp['input_edit_data'] == 'Дата прихода':
        await message.answer(
            "К сожалению, изменить дату присоединения нельзя",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()
    elif tmp['input_edit_data'] == 'ID':
        await message.answer(
            "К сожалению, изменить ID нельзя",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()
    else:
        await message.answer("Введите изменения")
        await state.set_state(InfoEmployees.change_edit)

@dp.message(InfoEmployees.change_edit)
async def change_edit_func(message: Message, state: FSMContext):
    temp = await state.get_data()
    if temp['input_edit_data'] == 'Аватарка':
        await bot.download(message.photo[-1])
        await state.update_data(change_edit_data=message.photo[-1].file_id)
    else:
        await state.update_data(change_edit_data=message.text.lower())
    change_ed = await state.get_data()
    try:
        connection = sqlite3.connect('employees.db')
        cursor = connection.cursor()
        if change_ed['input_edit_data'] == 'Фамилия':
            upd = cursor.execute(
                "UPDATE Info set `Фамилия` = ? WHERE ID = ?",
                (change_ed['change_edit_data'], change_ed['id_for_upd'])
            )
        elif change_ed['input_edit_data'] == 'Имя':
            upd = cursor.execute(
                "UPDATE Info set `Имя` = ? WHERE ID = ?",
                (change_ed['change_edit_data'], change_ed['id_for_upd'])
            )
        elif change_ed['input_edit_data'] == 'Отчество':
            upd = cursor.execute(
                "UPDATE Info set `Отчество` = ? WHERE ID = ?",
                (change_ed['change_edit_data'], change_ed['id_for_upd'])
            )
        elif change_ed['input_edit_data'] == 'Должность':
            upd = cursor.execute(
                "UPDATE Info set `Должность` = ? WHERE ID = ?",
                (change_ed['change_edit_data'], change_ed['id_for_upd'])
            )
        elif change_ed['input_edit_data'] == 'Проект':
            upd = cursor.execute(
                "UPDATE Info set Проект = ? WHERE ID = ?",
                (change_ed['change_edit_data'], change_ed['id_for_upd'])
            )
        elif change_ed['input_edit_data'] == 'Аватарка':
            upd = cursor.execute(
                "UPDATE Info set `Аватарка` = ? WHERE ID = ?",
                (change_ed['change_edit_data'], change_ed['id_for_upd'])
            )
        connection.commit()
        connection.close()
        await message.answer(
            "Данный сотрудник был изменён\n\n"
            "Если вы хотите выполнить другие действия, то "
            "напишите 'Начать' или нажмите /start",
            reply_markup=ReplyKeyboardRemove()
        )
    except sqlite3.Error as err:
        print(err)
        await message.answer(
            "Произошла ошибка\n"
            "Попробуйте сначала, написав 'Начать' или нажав /start"
        )
    await state.clear()






@dp.callback_query(F.data == "search")
async def add_employee(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.reply(
        "Чтобы найти сотрудника, необходимо ввести его фамилию"
    )
    await callback.message.answer("Введите вашу фамилию")
    await state.set_state(InfoEmployees.input_search)
    await callback.answer()

@dp.message(InfoEmployees.input_search)
async def input_search_func(message: Message, state: FSMContext):
    await state.update_data(search_input=message.text.lower())
    input_data = await state.get_data()
    try:
        connection = sqlite3.connect('employees.db')
        cursor = connection.cursor()
        select_for_del = cursor.execute(
            "SELECT * FROM Info WHERE `Фамилия` = ?",
            (input_data['search_input'],)
        )
        record = cursor.fetchall()
        length = len(record)
        name_col = cursor.execute("SELECT * FROM Info")
        columns = [desc[0] for desc in name_col.description]
        col = 0
        for column in select_for_del.description:
            col += 1
        search_info = ''
        if length == 1:
            for i in record:
                for j in range(0, col):
                    if j == 6:
                        await state.update_data(id_for_ph=str(i[j]))
                    else:
                        search_info += columns[j] + ': ' + str(i[j]) + '\n'
            connection.close()
            input_data = await state.get_data()
            await message.reply_photo(
                caption=f"Был найден данный сотрудник:\n\n"
                    f"{search_info}",
                photo=input_data['id_for_ph']
            )
            await message.answer(
                "Если вы хотите выполнить другие действия, то "
                "напишите 'Начать' или нажмите /start",
                reply_markup=ReplyKeyboardRemove()
            )
        elif length > 1:
            for i in record:
                for j in range(0, col):
                    if j == 6:
                        await state.update_data(id_for_ph=str(i[j]))
                    else:
                        search_info += columns[j] + ': ' + str(i[j]) + '\n'
                input_data = await state.get_data()
                await message.reply_photo(
                    caption=f"Был найден данный сотрудник:\n\n"
                        f"{search_info}",
                    photo=input_data['id_for_ph']
                )
                search_info = ''
            connection.close()
            await message.answer(
                "Если вы хотите выполнить другие действия, то "
                "напишите 'Начать' или нажмите /start",
                reply_markup=ReplyKeyboardRemove()
            )
        else:
            await state.clear()
            await message.answer(
                "Данный сотрудник не был найден\n\n"
                "Если вы хотите выполнить другие действия, то "
                "напишите 'Начать' или нажмите /start",
                reply_markup=ReplyKeyboardRemove()
            )
    except sqlite3.Error:
        await message.answer(
            "Произошла ошибка\n"
            "Попробуйте сначала, написав 'Начать' или нажав /start"
        )
    await state.clear()





async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())