from aiogram import Bot, Dispatcher, executor, types
from aiogram import types
from Keyboard import keyboard, lessons_num, removeKeyboard, keyboards
from config import API_TOKEN
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
    noww = datetime.now(pytz.timezone('Asia/Yekaterinburg'))
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

state = {}
updates_by_user = {}
last_keyboard = deque()

day = now().weekday()

admins_id = [800155626]

class Strings:
    def __init__(self):
        self.start_message = "Привет"
        self.tab = "    "
        self.no_task = "Нет информации о домашнем задании"
        self.no_adm = "Вы не администратор, но ачивку 'прочитай и пойми код' заработали"
        self.choose_subject = "Выберите предмет"
        self.send_task = "Отправьте задние. Вы также можете прикрепить файлы.\n Нажмите Готово, когда закончите."
        self.use_buttons = "Используйте кнопки для общения со мной"
        self.back = "Назад"
        self.no_back = "Назад больше некуда"
        self.succesfully_updated = "Успешно обновлено"
        self.bad_task = "Некорректно!"
        self.send_start = "Пришлите /start для корректной работы"
        self.done = "Готово"

strings = Strings()


class Hometask:
    def __init__(self):
        self.hometask = {}
        self.docs = {}
    
    def update_task(self, subject_name, task):
        self.hometask[subject_name] = task
    
    def update_files(self, subject_name, files):
        self.docs[subject_name] = files

    def get_task(self, subject_name):
        if (not subject_name in self.hometask) or (self.hometask[subject_name] == None):
            return strings.no_task
        return self.hometask[subject_name]
    
    def get_files(self, subject_name):
        if (not subject_name in self.docs) or (self.docs[subject_name] == None):
            return strings.no_task
        
        return self.docs[subject_name]

    def get_hometask(self):
        hometask = ""
        for subject_name in timetable[day]:
            hometask += "<b>" + subject_name + "</b>" + "\n"

            if not subject_name in self.hometask:
                task = None
            else:
                task = self.hometask[subject_name]
            
            hometask += strings.tab
            if task == None:
                hometask += strings.no_task
            else:
                hometask += task
            hometask += "\n"
        
        return hometask

hometask = Hometask()

#admin tools
async def change_timetable(message: types.Message):
    if not message.from_user.id in admins_id:
        await message.reply(strings.not_adm)
        return

    text = message.text


    text = text[len('/change_timetable ') : len(text)]

    if len(text) < 5:
        message.reply("BAD!")
        return

    day_num = int(text[0])

    text = text[2:len(text)]

    lessons = list(text.split('.'))

    timetable[day_num].clear()
    for lesson in lessons:
        timetable[day_num].append(lesson)

    await message.reply("successfully updated")


#for all users
async def start(message: types.Message):
    uid = message.from_user.id
    state[uid] = 0
    updates_by_user[uid] = {'subject_name':"", 'text':[], 'files':[]}
    last_keyboard.append('main')
    await message.reply(text = strings.start_message, reply_markup=keyboard('main'))


async def get_hometask(message: types.Message):
    uid = message.from_user.id

    if not uid in state:
        await message.reply(text = strings.send_start)
        return

    if state[uid] == 3:
        await message.reply(text = strings.bad_task)
        return

    await send_msg(user_id = uid, text = hometask.get_hometask())


async def send_lessons(message: types.Message):
    uid = message.from_user.id

    if not uid in state:
        await message.reply(text=strings.send_start)
        return

    last_keyboard.append('lessons')
    await message.reply(text = strings.choose_subject, reply_markup=keyboard('lessons'))


async def lesson_name_sended(message: types.Message):
    uid = message.from_user.id

    if not uid in state:
        await message.reply(text=strings.send_start)
        return
    
    if state[uid] == 1:
        await message.reply(text=hometask.get_task(message.text))
        for file in hometask.get_files(message.text):
            await bot.send_document(chat_id = uid, document = file)
    elif state[uid] == 2:
        state[uid] = 3
        updates_by_user[uid]['subject_name'] = message.text
        await message.reply(text=strings.send_task, reply_markup= keyboard('done'))
    elif state[uid] == 3:
        hometask.update_task(update_lesson_name[uid], str(message.text))
        await message.reply(text = strings.succesfully_updated)
        state[uid] = 2
    else:
        await message.reply(text = strings.use_buttons)


async def others(message: types.Message):
    uid = message.from_user.id

    if not uid in state:
        await message.reply(text=strings.send_start)
        return
    
    no_intresting_states = [0, 1, 2]
    if state[uid] in no_intresting_states:
        await message.reply(text = strings.use_buttons)
    else:
        if state[uid] == 3:

            with open("updates_hometasks.txt", "w") as file_name:
                log_str = ""
                if message.from_user.first_name != None:
                    log_str += message.from_user.first_name
                if message.from_user.last_name != None:
                    log_str += message.from_user.last_name
                log_str += '('
                if message.from_user.username != None:
                    log_str += message.from_user.username
                log_str += '):'
                log_str += message.text + "\n"
                print(log_str)
                file_name.write(log_str)

            updates_by_user[uid]['text'].append(str(message.text))


async def back(message: types.Message):
    uid = message.from_user.id

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

    if not uid in state:
        message.reply(strings.send_start)
        return
    
    if state[uid] != 3:
        message.reply(strings.use_buttons)
        return
    
    doc_id = message.document.file_id

    updates_by_user[uid]['files'].append(doc_id)


async def done(message: types.Message):
    uid = message.from_user.id

    if not uid in state:
        await message.reply(strings.send_start)
        return
    
    if state[uid] != 3:
        await message.reply(strings.use_buttons)
        return
    
    text = ""
    for paragraph in updates_by_user[uid]['text']:
        text += paragraph + "\n"

    if len(text) != 0:
        hometask.update_task(updates_by_user[uid]['subject_name'], text)

    files = updates_by_user[uid]['files']     
    if len(files) != 0:
        hometask.update_files(updates_by_user[uid]['subject_name'], files)
    
    state[uid] = 2
    await bot.send_message(chat_id = uid, text = strings.done, reply_markup=keyboard('lessons'))


async def updating():
        
    def update_timetable():
        if now().hour == 7 and now().day != 6:
            day = day_update(day)
            hometask.update_timetable(timetable[day])
    
    while True:
        update_timetable()

        await asyncio.sleep(UPDATE_INTERVAL)


def Bot():

    @disp.message_handler(commands = ['change_timetable'])
    async def change_timetablee(message: types.Message):
        await change_timetable(message)

    @disp.message_handler(commands=['start'])
    async def startt(message: types.Message):
        await start(message)
    
    @disp.message_handler(text_in_msg('main', 0))
    async def get_hometaskk(message: types.Message):
        await get_hometask(message)
    
    @disp.message_handler(text_in_msg('main', 1) )
    async def send_lessonss(message: types.Message):
        if state[message.from_user.id] == 3:
            await message.reply(text = strings.bad_task)
            return
        
        state[message.from_user.id] = 1
        
        await send_lessons(message)
    
    @disp.message_handler(text_in_msg('main', 2))
    async def send_lessonss(message: types.Message):
        if state[message.from_user.id] == 3:
            await message.reply(text=strings.bad_task)
            return

        state[message.from_user.id] = 2

        await send_lessons(message)

    @disp.message_handler(text_in_msg('done', 0))
    async def donee(message: types.Message):
        await done(message)

    @disp.message_handler(text_is_lesson_name())
    async def lesson_namee(message: types.Message):
        await lesson_name_sended(message)
    
    @disp.message_handler(text_in_msg('lessons', 13))
    async def backk(message: types.Message):
        await back(message)

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
