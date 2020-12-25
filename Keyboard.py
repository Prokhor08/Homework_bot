from aiogram import types
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.utils.markdown import text, bold, italic, code, pre

keyboards = {
    'main':[
        [KeyboardButton(text="📚 Получить домашнее задание 📚")],
        [KeyboardButton(text="📕 Получить дз по предмету 📕")],
        [KeyboardButton(text="✏️ Добавить домашнее задание ✏️")],
        [KeyboardButton(text="🧹 Удалить домашнее задание 🧹")]
    ],
    'lessons':[
        [KeyboardButton("Алгебра"), KeyboardButton("Геометрия")],
        [KeyboardButton("Физика"), KeyboardButton("Русский язык")],
        [KeyboardButton("История"), KeyboardButton("Литература")],
        [KeyboardButton("Химия"), KeyboardButton("Обществознание")],
        [KeyboardButton("Биология"), KeyboardButton("География")],
        [KeyboardButton("Английский язык"), KeyboardButton("ОБЖ")],
        [KeyboardButton("Информатика и ИКТ")],
        [KeyboardButton("Назад")]
    ],
    'done':[
        [KeyboardButton("Готово")],
        [KeyboardButton("Отмена")]
    ]
}

def keyboard(name):
    return ReplyKeyboardMarkup(keyboard=keyboards[name], resize_keyboard=True)

def removeKeyboard():
    return ReplyKeyboardRemove()
