# -*- coding: utf_8 -*-
from aiogram import Bot, Dispatcher, executor, types
from Keyboard import keyboard, removeKeyboard, keyboards
from timetable import timetable, day_update
from datetime import datetime, timedelta
from aiogram.utils.markdown import text, bold, italic, code, pre
from collections import deque
from SGClient import SGClient
import pytz
import sqlite3
import asyncio
import config


#utils

def date_to_str(date):
    return str(date.year) + '-' + str(date.month) + '-' + str(date.day)


def holiday_date(date, sg):
    if date.weekday == 6:
        return True

    formDate = date_to_str(date)
    day = sg.getHomework(formDate, formDate)

    if not 'weekDays' in day:
        return True
    if len(day['weekDays']) == 0:
        return True

    return False

async def send_msg(user_id, text):
    await bot.send_message(chat_id=user_id, text=text)


def now():
    noww = datetime.now(pytz.timezone('Europe/Moscow'))
    return noww


def text_on_button(keyboard_name, button_num):

    curnum = -1
    text = ''
    for row in keyboards[keyboard_name]:
        for button in row:
            curnum += 1
            if(curnum == button_num):
                text = button['text']

    return text


def text_in_msg(keyboard_name, button_num):
    text = text_on_button(keyboard_name, button_num)
    return lambda message: message.text and text in message.text


def text_is_lesson_name():
    def check(text):
        for num in range(13):
            if text_on_button('lessons', num) == text:
                return True
        return False

    return lambda message: message.text and check(message.text)


def send_info(message):
    bot.send_message(chat_id=INFOCHATID, text='.')


def info_message(message: types.Message, typ: str):
    log_str = ""
    if message.from_user.first_name != None:
        log_str += message.from_user.first_name
    if message.from_user.last_name != None:
        log_str += message.from_user.last_name
    log_str += '('
    if message.from_user.username != None:
        log_str += message.from_user.username
    log_str += ')'

    uid = message.from_user.id
    log_str += '(' + str(uid) + '):\n'

    if(typ == 'text'):
        log_str += message.text + '\n'
    elif typ == 'docs':
        log_str += "Отправил документ"
    elif typ == 'photos':
        log_str += "Отправил фото"

    log_str += updates_by_user[uid]['subject_name'] + "\n"
    return log_str


#constants
UPDATE_INTERVAL = 300
INFOCHATID = -1001293904791

#bot
bot = Bot(token=config.API_TOKEN, parse_mode="HTML")
disp = Dispatcher(bot)

#data
db_connection = sqlite3.connect("database.db")
cur = db_connection.cursor()

sg = SGClient()
sg.login(config.LOGIN, config.PASSWORD)

state = {}
updates_by_user = {}
del_subject_name = {}
day = now().weekday()
admins_id = [800155626]
users_ids = [800155626, 664331079, 998445492, 912050293, 652242346, 723471766, 539584923, 1249475977,
             918018751, 939427187, 1035364674, 871823293, 792033308, 604117040, 892138456, 902858644, 1232287987]


class Strings:
    def __init__(self):
        self.start_message = "Привет"
        self.tab = "    "
        self.no_task = "Нет информации о домашнем задании.\n"
        self.no_adm = "Вы не администратор здесь."
        self.choose_subject = "Выберите предмет"
        self.send_task = "Отправьте задние. Вы также можете прикрепить файлы.\nНажмите Готово, когда закончите."
        self.use_buttons = "Используйте кнопки для общения со мной."
        self.back = "Назад"
        self.no_back = "Назад больше некуда"
        self.succesfully_updated = "Успешно обновлено"
        self.succesfully = "Успешно"
        self.bad_task = "Некорректно!"
        self.send_start = "Пожалуйста, пришлите /start для корректной работы."
        self.done = "Готово"
        self.left = "Вы не можете пользовать сей бот("
        self.have_files = "Есть прикрепленные файлы."
        self.incorrect_id = "Некорректный id."
        self.succesfully_cleared = "Успешно удалено."
        self.bad = "BAD!"
        self.incorrect_task = "Некорректное задание!"
        self.sure = "Вы уверены? Если да, нажмите готово."
        self.cancel = "Отменил"


class Hometask:
    def __init__(self):
        cur.execute(
            "CREATE TABLE IF NOT EXISTS text_task (lesson_name TEXT, task TEXT)")
        cur.execute(
            "CREATE TABLE IF NOT EXISTS docs_task (lesson_name TEXT, task TEXT)")
        cur.execute(
            "CREATE TABLE IF NOT EXISTS photo_task (lesson_name TEXT, task TEXT)")
        db_connection.commit()

    def update_task(self, subject_name, task):
        cur.execute(
            "SELECT lesson_name FROM text_task WHERE lesson_name = ?", [subject_name])

        if not cur.fetchall():
            cur.executemany("INSERT INTO text_task VALUES (?,?)", [
                            (subject_name, task)])
            db_connection.commit()

        sql = """UPDATE text_task
        SET task = ?
        WHERE lesson_name = ?
        """

        cur.executemany(sql, [(task, subject_name)])
        db_connection.commit()

    def update_docs(self, subject_name, docs):
        cur.execute(
            "DELETE FROM docs_task WHERE lesson_name = ?", [subject_name])
        db_connection.commit()

        for doc in docs:
            cur.executemany("INSERT INTO docs_task VALUES (?, ?)", [
                (subject_name, docs)])
            db_connection.commit()

    def update_photos(self, subject_name, photos):
        cur.execute(
            "DELETE FROM photo_task WHERE lesson_name = ?", [subject_name])
        db_connection.commit()

        for photo in photos:
            cur.executemany("INSERT INTO photo_task VALUES (?, ?)", [
                (subject_name, photo)])
            db_connection.commit()

    def clear_task(self, subject_name):
        cur.execute(
            "DELETE FROM text_task WHERE lesson_name = ?", [subject_name])
        db_connection.commit()

    def clear_docs(self, subject_name):
        cur.execute(
            "DELETE FROM docs_task WHERE lesson_name = ?", [subject_name])
        db_connection.commit()

    def clear_photos(self, subject_name):
        cur.execute(
            "DELETE FROM photo_task WHERE lesson_name = ?", [subject_name])
        db_connection.commit()

    def get_task(self, subject_name):
        cur.execute(
            "SELECT * FROM text_task WHERE lesson_name = ?", [subject_name])
        if not cur.fetchall():
            return strings.no_task

        cur.execute(
            "SELECT task FROM text_task WHERE lesson_name = ?", [subject_name])
        ans = cur.fetchall()
        ans = [i[0] for i in ans]

        return ans[0]

    def get_docs(self, subject_name):
        cur.execute(
            "SELECT * FROM docs_task WHERE lesson_name = ?", [subject_name])
        if not cur.fetchall():
            return []

        cur.execute(
            "SELECT task FROM docs_task WHERE lesson_name = ?", [subject_name])

        ans = cur.fetchall()
        ans = [i[0] for i in ans]
        return ans

    def get_photos(self, subject_name):
        cur.execute(
            "SELECT * FROM photo_task WHERE lesson_name = ?", [subject_name])
        if not cur.fetchall():
            return []

        cur.execute(
            "SELECT task FROM photo_task WHERE lesson_name = ?", [subject_name])
        ans = cur.fetchall()
        ans = [i[0] for i in ans]
        return ans

    def get_hometask(self):
        hometask = ""
        for subject_name in timetable[day]:

            hometask += "<b>" + subject_name + "</b>" + "\n"
            hometask += strings.tab + self.get_task(subject_name) + "\n"

            if self.get_docs(subject_name) or self.get_photos(subject_name):
                hometask += strings.tab + strings.have_files + "\n"

        return hometask


class Users:

    def __init__(self):
        cur.execute(
            "CREATE TABLE IF NOT EXISTS states (user_id int, state text)")
        db_connection.commit()

    def set_state(self, user_id: int, state: str):
        cur.execute(
            "SELECT * FROM states WHERE user_id = ?", [user_id])

        if not cur.fetchall():
            cur.executemany("INSERT INTO states VALUES (?,?)", [
                            (user_id, state)])
            db_connection.commit()
        else:
            cur.executemany("UPDATE states SET state = ? WHERE user_id = ?", [
                            (state, user_id)])
            db_connection.commit()

    def get_state(self, user_id):
        cur.execute("SELECT state FROM states WHERE user_id = ?", [(user_id)])

        state = cur.fetchone()
        if not state:
            return False
        return state[0]


hometask = Hometask()
strings = Strings()
users = Users()

#admin tools


async def change_timetable(message: types.Message):
    if not message.from_user.id in admins_id:
        await message.reply(strings.not_adm)
        return

    text = message.text

    text = text[len('/change_timetable '): len(text)]

    if len(text) < 5:
        await message.reply(strings.bad)
        return

    day_num = int(text[0])

    text = text[2:len(text)]

    lessons = list(text.split('.'))

    timetable[day_num].clear()
    for lesson in lessons:
        timetable[day_num].append(lesson)

    await message.reply(text=strings.succesfully_updated)


async def add_user(message: types.Message):
    uid = message.from_user.id

    if not uid in admins_id:
        await bot.send_message(text=strings.no_adm)
        return

    text = message.text
    text = text[len('/add_user '): len(text)]

    try:
        add_id = int(text)
        users_ids.append(add_id)
        await message.reply(text=strings.succesfully_updated)
    except:
        await message.reply(text=strings.incorrect_id)


async def del_user(message: types.Message):
    uid = message.from_user.id

    if not uid in admins_id:
        await bot.send_message(text=strings.no_adm)
        return

    text = message.text
    text = text[len('/add_user '): len(text)]

    try:
        clear_id = int(text)
        users_ids.remove(clear_id)
        await message.reply(text=strings.succesfully_cleared)
    except ValueError:
        await message.reply(text=strings.incorrect_id)


async def add_admin(message: types.Message):
    uid = message.from_user.id

    if not uid in admins_id:
        await bot.send_message(text=strings.no_adm)
        return

    text = message.text
    text = text[len('/add_admin '): len(text)]

    try:
        add_id = int(text)
        admins_id.append(add_id)
        await message.reply(text=strings.succesfully_updated)
    except:
        await message.reply(text=strings.incorrect_id)


async def clear_hometask(message):
    uid = message.from_user.id

    if not uid in admins_id:
        message.reply(strings.no_adm)
        return

    text = message.text
    text = text[len('/clear_hometask '):len(text)]

    if len(text) < 3:
        await message.reply(strings.bad)
        return

    hometask.clear_task(text)
    hometask.clear_docs(text)
    hometask.clear_photos(text)

    await message.reply(strings.succesfully_cleared)


#for all users
async def start(message: types.Message):
    uid = message.from_user.id

    if not uid in users_ids:
        return

    users.set_state(uid, 'main_menu')

    await message.reply(text=strings.start_message, reply_markup=keyboard('main'))


async def get_hometask(message: types.Message):
    uid = message.from_user.id

    if not uid in users_ids:
        await message.reply(strings.left)
        return

    await send_msg(user_id=uid, text=hometask.get_hometask())


async def send_lessons(message: types.Message, typ: str):
    uid = message.from_user.id

    if not uid in users_ids:
        await message.reply(strings.left)
        return

    if not users.get_state(uid):
        await message.reply(strings.send_start)
        return

    user_state = users.get_state(uid)

    if user_state != 'main_menu':
        await message.reply(text=strings.use_buttons)
        return

    users.set_state(uid, typ)

    await message.reply(text=strings.choose_subject, reply_markup=keyboard('lessons'))


async def lesson_name_sended(message: types.Message):
    uid = message.from_user.id

    if not uid in users_ids:
        await message.reply(strings.left)
        return

    if not users.get_state(uid):
        await message.reply(strings.send_start)
        return

    user_state = users.get_state(uid)

    if user_state == 'get_subject_task':
        await message.reply(text=hometask.get_task(message.text))

        for doc in hometask.get_docs(message.text):
            await bot.send_document(chat_id=uid, document=doc)
        for photo in hometask.get_photos(message.text):
            await bot.send_photo(chat_id=uid, photo=photo)

    elif user_state == 'add_task':
        users.set_state(uid, 'adding_task')
        updates_by_user[uid]['subject_name'] = message.text
        await message.reply(text=strings.send_task, reply_markup=keyboard('done'))

    elif user_state == 'adding_task':
        await message.reply(text=strings.incorrect_task)
        return

    elif user_state == 'clear_task':
        del_subject_name[uid] = message.text
        await message.reply(text=strings.sure, reply_markup=keyboard('done'))
        return

    else:
        await message.reply(text=strings.use_buttons)


async def others(message: types.Message):
    uid = message.from_user.id

    if not uid in users_ids:
        await message.reply(strings.left)
        return

    if not users.get_state(uid):
        await message.reply(strings.send_start)
        return

    user_state = users.get_state(uid)

    bad_states = ['main_menu', 'get_subject_task', 'add_task', 'clear_task']
    if user_state in bad_states:
        await message.reply(text=strings.use_buttons)
    else:
        if user_state == 'adding_task':
            infostr = info_message(message, 'text')
            await bot.send_message(chat_id=INFOCHATID, text=infostr)

            if updates_by_user[uid]['text']:
                updates_by_user[uid]['text'] += strings.tab + \
                    (str(message.text)) + "\n"
            else:
                updates_by_user[uid]['text'] += (str(message.text))


async def back(message: types.Message):
    uid = message.from_user.id

    if not uid in users_ids:
        await message.reply(strings.left)
        return

    if not users.get_state(uid):
        await message.reply(strings.send_start)
        return

    user_state = users.get_state(uid)

    if user_state == 'main_menu':
        await message.reply(text=strings.no_back)
    elif user_state == 'get_subject_task' or user_state == 'add_task' or user_state == 'clear_task':
        users.set_state(uid, 'main_menu')
        await message.reply(text=strings.back, reply_markup=keyboard('main'))
    elif user_state == 'adding_task':
        return
    else:
        await message.reply(text="0_0, send me message")


async def docs_handler(message: types.Message):
    uid = message.from_user.id

    if not uid in users_ids:
        await message.reply(strings.left)
        return

    if not users.get_state(uid):
        await message.reply(strings.send_start)
        return

    user_state = users.get_state(uid)

    if user_state != 'adding_task':
        await message.reply(strings.use_buttons)
        return

    doc_id = message.document.file_id
    updates_by_user[uid]['docs'].append(doc_id)

    info_str = info_message(message, 'docs')
    await bot.send_message(chat_id=INFOCHATID, text=info_str)
    await bot.send_document(chat_id=INFOCHATID, document=doc_id)


async def photo_handler(message: types.Message):
    uid = message.from_user.id

    if not uid in users_ids:
        await message.reply(strings.left)
        return

    if not users.get_state(uid):
        await message.reply(strings.send_start)
        return

    user_state = users.get_state(uid)

    if user_state != 'adding_task':
        await message.reply(strings.use_buttons)
        return

    doc_id = message.photo[0].file_id
    updates_by_user[uid]['photos'].append(doc_id)

    info_str = info_message(message, 'photo')
    await bot.send_message(chat_id=INFOCHATID, text=info_str)
    await bot.send_photo(chat_id=INFOCHATID, photo=doc_id)


async def done(message: types.Message):
    uid = message.from_user.id

    if not uid in users_ids:
        await message.reply(strings.left)
        return

    if not users.get_state(uid):
        await message.reply(strings.send_start)
        return

    user_state = users.get_state(uid)

    if user_state != 'adding_task' and user_state != 'clear_task':
        await message.reply(strings.use_buttons)
        return

    if user_state == 'clear_task':
        hometask.clear_photos(del_subject_name[uid])
        hometask.clear_docs(del_subject_name[uid])

        await message.reply(strings.done, reply_markup=keyboard('lessons'))
        return
    elif user_state == 'adding_task':

        text = updates_by_user[uid]['text']
        if text != "":
            hometask.update_task(updates_by_user[uid]['subject_name'], text)

        docs = updates_by_user[uid]['docs']
        if docs != []:
            hometask.update_files(updates_by_user[uid]['subject_name'], docs)

        photos = updates_by_user[uid]['photos']
        if photos != []:
            hometask.update_photos(
                updates_by_user[uid]['subject_name'], photos)

        updates_by_user[uid]['subject_name'] = ""
        updates_by_user[uid]['docs'] = []
        updates_by_user[uid]['photos'] = []
        updates_by_user[uid]['text'] = ""

        users.set_state(uid, 'add_task')

        await bot.send_message(chat_id=uid, text=strings.done, reply_markup=keyboard('lessons'))


async def cancel(message: types.Message):
    uid = message.from_user.id

    if not uid in users_ids:
        await message.reply(strings.left)
        return

    if not users.get_state(uid):
        await message.reply(strings.send_start)
        return

    user_state = users.get_state(uid)

    if user_state == 'clear_task':
        await message.reply(text=strings.cancel, reply_markup=keyboard('lessons'))
    elif user_state == 'adding_task':
        await message.reply(text=strings.cancel, reply_markup=keyboard('lessons'))
        users.set_state(uid, 'add_task')
    else:
        await message.reply(text=strings.use_buttons)
        return


async def updating():
    global day

    was_update = False

    while True:

        if now().hour == 6 and not was_update:
            was_update = True

            day += 1
            day %= 7

        if now().hour == 13:
            was_update = False

        await asyncio.sleep(UPDATE_INTERVAL)


async def updates_from_sg():

    while True:        
        current_day = now()
        day_delta = timedelta(days=1)

        cnt_it2 = 0

        cnt_it = 0
        while cnt_it <= 7 and cnt_it2 < 50:
            cnt_it2 += 1

            subj_update = dict()

            current_day = current_day + day_delta

            if not holiday_date(current_day, sg):
                cnt_it += 1

                day = sg.getHomework(date_to_str(current_day), date_to_str(current_day))[
                    'weekDays'][0]['lessons']
                for lesson in day:
                    subject_name = lesson['subjectName']
                    if 'assignments' in lesson:
                        assignments = lesson['assignments']
                        for assignment in assignments:
                            if assignment['typeId'] == 3:
                                if not subject_name in subj_update:
                                    subj_update[subject_name] = [assignment['assignmentName']]
                                else:
                                    subj_update[subject_name].append(assignment['assignmentName'])

                for subj_name in subj_update:
                    task = '' 
                    for subtask in subj_update[subj_name]:
                        task += subtask + '\n'
                    hometask.update_task(subj_name, task)

        await asyncio.sleep(300)

def Bot():

    @disp.message_handler(commands=['recover'])
    async def data_recover(message: types.Message):
        await data_recovery()

    @disp.message_handler(commands=['add_user'])
    async def add_userr(message: types.Message):
        await add_user(message)

    @disp.message_handler(commands=['add_admin'])
    async def add_adminn(message: types.Message):
        await add_admin(message)

    @disp.message_handler(commands=['send_main'])
    async def send_main(message: types.Message):
        await message.reply(text="ok", reply_markup=keyboard('main'))
        users.set_state(message.from_user.id, 'main_menu')

    @disp.message_handler(commands=['change_timetable'])
    async def change_timetablee(message: types.Message):
        await change_timetable(message)

    @disp.message_handler(commands=['clear_hometask'])
    async def change_timetablee(message: types.Message):
        await clear_hometask(message)

    @disp.message_handler(commands=['start'])
    async def startt(message: types.Message):

        await start(message)

    @disp.message_handler(text_in_msg('main', 0))
    async def get_hometaskk(message: types.Message):
        await get_hometask(message)

    @disp.message_handler(text_in_msg('main', 1))
    async def send_lessonss(message: types.Message):
        await send_lessons(message, 'get_subject_task')

    @disp.message_handler(text_in_msg('main', 2))
    async def send_lessonss2(message: types.Message):
        await send_lessons(message, 'add_task')

    @disp.message_handler(text_in_msg('main', 3))
    async def send_lessonss3(message: types.Message):
        await send_lessons(message, 'clear_task')

    @disp.message_handler(text_in_msg('done', 0))
    async def donee(message: types.Message):
        await done(message)

    @disp.message_handler(text_in_msg('done', 1))
    async def cancell(message: types.Message):
        await cancel(message)

    @disp.message_handler(text_is_lesson_name())
    async def lesson_namee(message: types.Message):
        await lesson_name_sended(message)

    @disp.message_handler(text_in_msg('lessons', 13))
    async def backk(message: types.Message):
        await back(message)

    @disp.message_handler(content_types=['photo'])
    async def photo_handlerr(message: types.Message):
        await photo_handler(message)

    @disp.message_handler(content_types=['document'])
    async def docs_handlerr(message: types.Message):
        await docs_handler(message)

    @disp.message_handler()
    async def otherss(message: types.Message):
        await others(message)

    (disp.loop or asyncio.get_event_loop()).create_task(updating())
    (disp.loop or asyncio.get_event_loop()).create_task(updates_from_sg())
    executor.start_polling(disp)


if __name__ == "__main__":
    for uid in users_ids:
        updates_by_user[uid] = {'subject_name': "",
                                'text': "", 'docs': [], 'photos': []}


    Bot()
