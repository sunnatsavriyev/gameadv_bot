from django.db import models


class TelegramUser(models.Model):
    telegram_id = models.BigIntegerField(unique=True, verbose_name="Telegram ID", null=True)
    phone_number = models.CharField(max_length=15, verbose_name="Phone Number", unique=True)
    name = models.CharField(max_length=100, verbose_name="Name")
    
    def __str__(self):
        return self.name

class GameAdv(models.Model):
    name = models.CharField(max_length=100, verbose_name="Name")
    degree = models.CharField(max_length=100, verbose_name="Degree")
    image = models.ImageField(upload_to='media/')
    qoshimchalar = models.CharField(max_length=1000, verbose_name="Qoshimchalar")
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE, related_name='game_ads')

    def __str__(self):
        return self.name

