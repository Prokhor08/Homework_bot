from aiogram import types
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.utils.markdown import text, bold, italic, code, pre

def kb(text):
    return KeyboardButton(text = text)

lessons_num = 13

keyboards = {
    'main':[
        [KeyboardButton(text = "Получить домашнее задание")], 
        [KeyboardButton(text = "Получить дз по предмету")],
        [KeyboardButton(text = "Добавить домашнее задание")]
    ],
    'lessons':[
        [kb("Алгебра"), kb("Геометрия")],
        [kb("Физика"), kb("Русский язык")],
        [kb("История"), kb("Литература")],
        [kb("Химия"), kb("Обществознание")],
        [kb("Биология"), kb("География")],
        [kb("Английский язык"), kb("ОБЖ")],
        [kb("Информатика и ИКТ")],
        [kb("Назад")]
    ],
    'done':[
        [kb("Готово")]
    ]
}

def keyboard(name):
    return ReplyKeyboardMarkup(keyboard=keyboards[name], resize_keyboard=True)

def removeKeyboard():
    return ReplyKeyboardRemove()
