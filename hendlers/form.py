from aiogram.dispatcher.filters.state import State, StatesGroup

class GameAdvForm(StatesGroup):
    name = State()
    degree = State()
    image = State()
    qoshimchalar_input = State()
    qoshimchalar = State()
    