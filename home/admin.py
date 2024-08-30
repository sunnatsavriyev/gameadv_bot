from django.contrib import admin
from .models import TelegramUser, GameAdv

@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ('telegram_id', 'name', 'phone_number')
    search_fields = ('name','phone_number', 'telegram_id')


@admin.register(GameAdv)
class GameAdvAdmin(admin.ModelAdmin):
    list_display = ('name', 'degree', 'image','qoshimchalar','user')
    search_fields = ('name', 'degree', 'image', 'qoshimchalar','user')
