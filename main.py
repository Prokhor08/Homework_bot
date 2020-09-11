from aiogram import Bot, Dispatcher, executor, types
from aiogram import types
from Keyboard import keyboard, lessons_num, removeKeyboard, keyboards
from config import API_TOKEN, API_TOKEN2
from timetable import timetable, day_update
from datetime import datetime
from aiogram.utils.markdown import text, bold, italic, code, pre
from collections import deque
import pytz
import asyncio

#utils
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
        for num in range(lessons_num):
            if text_on_button('lessons', num) == text:
                return True
        return False
    
    return lambda message: message.text and check(message.text)

UPDATE_INTERVAL = 300
bot = Bot(token=API_TOKEN, parse_mode="HTML")
disp = Dispatcher(bot)

inf_bot = Bot(token = API_TOKEN2)
inf_disp = Dispatcher(bot)

state = {}
updates_by_user = {}
last_keyboard = deque()

day = now().weekday()

admins_id = [800155626]
users_ids = [800155626, 664331079, 998445492, 912050293, 652242346, 723471766, 539584923, 1249475977, 918018751, 939427187, 1035364674, 871823293, 792033308, 604117040, 892138456, 902858644 ]

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
        self.left = "Вы не из 8В 31 лицея(."
        self.have_files = "Есть прикрепленные файлы."
        self.incorrect_id = "Некорректный id."
        self.succesfully_cleared = "Успешно удалено."
        self.bad = "BAD!"
        self.incorrect_task = "Некорректное задание!"

strings = Strings()


class Hometask:
    def __init__(self):
        self.hometask = {}
        self.docs = {}
        self.photos = {}
    
    def update_task(self, subject_name, task):
        self.hometask[subject_name] = task
    
    def update_files(self, subject_name, files):
        self.docs[subject_name] = []
        for file in files:
            self.docs[subject_name].append(file)
    
    def update_photos(self, subject_name, files):
        self.photos[subject_name] = []
        for file in files:
            self.photos[subject_name].append(file)

    def clear_task(self, subject_name):
        self.hometask[subject_name] = None
    
    def clear_docs(self, subject_name):
        self.docs[subject_name] = []
    
    def clear_photos(self, subject_name):
        self.photos[subject_name] = []

    def get_task(self, subject_name):
        if (not subject_name in self.hometask) or (self.hometask[subject_name] == None):
            return strings.no_task
        return self.hometask[subject_name]
    
    def get_files(self, subject_name):
        if (not subject_name in self.docs) or (self.docs[subject_name] == None):
            return []

        return self.docs[subject_name]

    def get_photos(self, subject_name):
        if (not subject_name in self.photos) or (self.photos[subject_name] == None):
            return []

        return self.photos[subject_name]

    def get_hometask(self):
        hometask = ""
        for subject_name in timetable[day]:

            if not subject_name in self.docs:
                self.docs[subject_name] = []
            if not subject_name in self.photos:
                self.photos[subject_name] = []

            hometask += "<b>" + subject_name + "</b>" + "\n"

            if not subject_name in self.hometask or len(self.hometask[subject_name]) == 0:
                task = None
            else:
                task = self.hometask[subject_name]
            
            if task == None:
                hometask += strings.no_task
            else:
                hometask += strings.tab
                hometask += task
            
            if self.photos[subject_name] != [] or self.docs[subject_name] != []:
                hometask += strings.tab + strings.have_files + "\n"
        
        return hometask


hometask = Hometask()

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

    await message.reply(text = strings.succesfully_updated)

async def add_user(message: types.Message):
    uid = message.from_user.id

    if not uid in admins_id:
        await bot.send_message(text = strings.no_adm)
        return
    
    text = message.text
    text = text[len('/add_user ')  : len(text)]

    try:
        add_id = int(text)
        users_ids.append(add_id)
        await message.reply(text = strings.succesfully_updated)
    except:
        await message.reply(text = strings.incorrect_id)

async def del_user(message:types.Message):
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
        await message.reply(strings.left)
        return

    state[uid] = 0
    updates_by_user[uid] = {'subject_name':"", 'text':"", 'files':[], 'photos':[]}
    last_keyboard.append('main')
    await message.reply(text = strings.start_message, reply_markup=keyboard('main'))


async def get_hometask(message: types.Message):
    uid = message.from_user.id

    if not uid in users_ids:
        await message.reply(strings.left)
        return

    if not uid in state:
        await message.reply(text = strings.send_start)
        return

    if state[uid] == 3:
        await message.reply(text = strings.bad_task)
        return

    await send_msg(user_id = uid, text = hometask.get_hometask())


async def send_lessons(message: types.Message, typ):
    uid = message.from_user.id

    if not uid in users_ids:
        await message.reply(strings.left)
        return

    if not uid in state:
        await message.reply(text=strings.send_start)
        return
    
    if state[uid] == 3:
        await message.reply(text = strings.bad_task)
        return

    state[uid] = typ

    last_keyboard.append('lessons')
    await message.reply(text = strings.choose_subject, reply_markup=keyboard('lessons'))


async def lesson_name_sended(message: types.Message):
    uid = message.from_user.id

    if not uid in users_ids:
        await message.reply(strings.left)
        return

    if not uid in state:
        await message.reply(text=strings.send_start)
        return
    
    if state[uid] == 1:
        await message.reply(text=hometask.get_task(message.text))
        for file in hometask.get_files(message.text):
            await bot.send_document(chat_id = uid, document = file)
        for file in hometask.get_photos(message.text):
            await bot.send_photo(chat_id = uid, photo = file)
    elif state[uid] == 2:
        state[uid] = 3
        updates_by_user[uid]['subject_name'] = message.text
        await message.reply(text=strings.send_task, reply_markup= keyboard('done'))
    elif state[uid] == 3:
        await message.reply(text = strings.incorrect_task)
        return
    else:
        await message.reply(text = strings.use_buttons)


async def others(message: types.Message):    
    uid = message.from_user.id

    if not uid in users_ids:
        await message.reply(strings.left)
        return

    if not uid in state:
        await message.reply(text=strings.send_start)
        return
    
    no_intresting_states = [0, 1, 2]
    if state[uid] in no_intresting_states:
        await message.reply(text = strings.use_buttons)
    else:
        if state[uid] == 3:

            log_str = ""
            if message.from_user.first_name != None:
                log_str += message.from_user.first_name
            if message.from_user.last_name != None:
                log_str += message.from_user.last_name
            log_str += '('
            if message.from_user.username != None:
                log_str += message.from_user.username
            log_str += ')'
            log_str += '(' + str(uid) + '): '
            log_str += message.text + '|' + updates_by_user[uid]['subject_name'] + "\n"

            await inf_bot.send_message(chat_id = admins_id[0], text = log_str)

            updates_by_user[uid]['text'] += (str(message.text)) + "\n"


async def back(message: types.Message):
    uid = message.from_user.id

    if not uid in users_ids:
        await message.reply(strings.left)
        return

    if not uid in state:
        await message.reply(text=strings.send_start)
        return

    if len(last_keyboard) == 0:
        await message.reply(text=strings.no_back)
        return

    last_keyboard.pop()

    if len(last_keyboard) == 0:
        await message.reply(text=strings.no_back)
        return

    state[message.from_user.id] = 0
    await message.reply(text=strings.back, reply_markup=keyboard(last_keyboard[-1]))


async def docs_handler(message: types.Message):
    uid = message.from_user.id

    if not uid in users_ids:
        await message.reply(strings.left)
        return

    if not uid in state:
        await message.reply(strings.send_start)
        return
    
    if state[uid] != 3:
        await message.reply(strings.use_buttons)
        return
    
    doc_id = message.document.file_id

    updates_by_user[uid]['files'].append(doc_id)

    log_str = ""
    if message.from_user.first_name != None:
        log_str += message.from_user.first_name
    if message.from_user.last_name != None:
        log_str += message.from_user.last_name
    log_str += '('
    if message.from_user.username != None:
        log_str += message.from_user.username
    log_str += ')'
    log_str += '(' + str(uid) + ') отправил фото|' + updates_by_user[uid]['subject_name'] + "\n"

    await inf_bot.send_message(chat_id = uid, text = log_str)


async def photo_handler(message: types.Message):
    uid = message.from_user.id

    if not uid in users_ids:
        await message.reply(strings.left)
        return

    if not uid in state:
        await message.reply(strings.send_start)
        return

    if state[uid] != 3:
        await message.reply(strings.use_buttons)
        return

    doc_id = message.photo[0].file_id

    updates_by_user[uid]['photos'].append(doc_id)

    log_str = ""
    if message.from_user.first_name != None:
        log_str += message.from_user.first_name
    if message.from_user.last_name != None:
        log_str += message.from_user.last_name
    log_str += '('
    if message.from_user.username != None:
        log_str += message.from_user.username
    log_str += ')'
    log_str += '(' + str(uid) + ') отправил фото|' + updates_by_user[uid]['subject_name'] + "\n"

    await inf_bot.send_message(chat_id = uid, text = log_str)
    

async def done(message: types.Message):
    uid = message.from_user.id

    if not uid in users_ids:
        await message.reply(strings.left)
        return

    if not uid in state:
        await message.reply(strings.send_start)
        return
    
    if state[uid] != 3:
        await message.reply(strings.use_buttons)
        return
    
    text = updates_by_user[uid]['text']

    if len(text) != 0:
        hometask.update_task(updates_by_user[uid]['subject_name'], text)

    files = updates_by_user[uid]['files']     
    if len(files) != 0:
        hometask.update_files(updates_by_user[uid]['subject_name'], files)
    
    photos = updates_by_user[uid]['photos'] 
    if len(photos) != 0:
        hometask.update_photos(updates_by_user[uid]['subject_name'], photos)

    updates_by_user[uid]['subject_name'] = ""
    updates_by_user[uid]['files'] = []
    updates_by_user[uid]['photos'] = []
    updates_by_user[uid]['text'] = ""
    state[uid] = 2
    await bot.send_message(chat_id = uid, text = strings.done, reply_markup=keyboard('lessons'))

async def updating():
    global day

    was_update = False

    def update():
        global day
        global was_update
        if day == 6:
            day = 0
        
        if now().hour == 7 and now().day != 6 and not was_update:
            was_update = True

            day = day_update(day)
            
            for subject_name in timetable[day]:
                hometask.clear_task(subject_name)
            
            for subject_name in timetable[day]:
                hometask.clear_docs(subject_name)
            
            for subject_name in timetable[day]:
                hometask.clear_photos(subject_name)
    
    def was_update_change():
        global was_update
        if now().hour == 8:
            was_update = False

    while True:
        update()
        was_update_change()

        await asyncio.sleep(UPDATE_INTERVAL)


def Bot():

    @disp.message_handler(commands = ['add_user'])
    async def add_userr(message: types.Message):
        add_user(message)

    
    @disp.message_handler(commands = ['add_admin'])
    async def add_adminn(message: types.Message):
        add_admin(message)

    @disp.message_handler(commands = ['change_timetable'])
    async def change_timetablee(message: types.Message):
        await change_timetable(message)
    
    @disp.message_handler(commands = ['clear_hometask'])
    async def change_timetablee(message: types.Message):
        await clear_hometask(message)

    @disp.message_handler(commands=['start'])
    async def startt(message: types.Message):
        await start(message)
    
    @disp.message_handler(text_in_msg('main', 0))
    async def get_hometaskk(message: types.Message):
        await get_hometask(message)
    
    @disp.message_handler(text_in_msg('main', 1) )
    async def send_lessonss(message: types.Message):
        await send_lessons(message, 1)
    
    @disp.message_handler(text_in_msg('main', 2))
    async def send_lessonss2(message: types.Message):
        await send_lessons(message, 2)

    @disp.message_handler(text_in_msg('done', 0))
    async def donee(message: types.Message):
        await done(message)

    @disp.message_handler(text_is_lesson_name())
    async def lesson_namee(message: types.Message):
        await lesson_name_sended(message)
    
    @disp.message_handler(text_in_msg('lessons', 13))
    async def backk(message: types.Message):
        await back(message)

    @disp.message_handler(content_types=['photo'])
    async def photo_handlerr(message: types.Message):
        await photo_handler(message)

    @disp.message_handler(content_types = ['document'])
    async def docs_handlerr(message: types.Message):
        await docs_handler(message)

    @disp.message_handler()
    async def otherss(message: types.Message):
        await others(message)

    
    disp.loop.create_task(updating())
    executor.start_polling(disp)


if __name__ == "__main__":
    Bot()
