from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Bill(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    name = models.CharField(verbose_name='Название', max_length=255)
    sum = models.DecimalField(verbose_name='Сумма', max_digits=30, decimal_places=2)
    created_date = models.DateTimeField(verbose_name='Дата создания', default=timezone.now)

    class Meta:
        verbose_name = 'Счет'
        verbose_name_plural = 'Счета'


class Action(models.Model):
    ACTION_CHOICES = (
        ('income', 'доход'),
        ('expense', 'расход'),
    )
    name = models.CharField(verbose_name='Название', max_length=50, choices=ACTION_CHOICES)

    class Meta:
        verbose_name = 'Действие с деньгами'
        verbose_name_plural = 'Действия с деньгами'


class Category(models.Model):
    action = models.ForeignKey(Action, on_delete=models.CASCADE)
    name = models.CharField(verbose_name='Название', max_length=255)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'


class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE)

    date = models.DateTimeField(verbose_name='Дата операции', default=timezone.now)
    sum = models.DecimalField(verbose_name='Сумма', max_digits=30, decimal_places=2)
    tag = models.CharField(verbose_name='Тег', max_length=255, null=True)
    comment = models.TextField(verbose_name='Комментарий', null=True)

    class Meta:
        verbose_name = 'Операция'
        verbose_name_plural = 'Операции'
