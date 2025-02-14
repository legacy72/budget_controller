from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now as now_local

from budget_controller.utils.date_utils import increase_datetime_now_for_10_minutes


class AuthCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(verbose_name='Код', max_length=255)
    start_date = models.DateTimeField(verbose_name='Дата генерации', auto_now=True)
    end_date = models.DateTimeField(
        verbose_name='Дата окончания действия',
        default=increase_datetime_now_for_10_minutes,
    )

    class Meta:
        verbose_name = 'Код'
        verbose_name_plural = 'Коды'
        ordering = ['-id']


class Bill(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    name = models.CharField(verbose_name='Название', max_length=255)
    TYPE_CHOICES = (
        ('cash', 'наличные'),
        ('non_cash', 'безналичные'),
    )
    type = models.CharField(verbose_name='Название', max_length=50, choices=TYPE_CHOICES, default='cash')
    sum = models.DecimalField(verbose_name='Сумма', max_digits=30, decimal_places=2)
    created_date = models.DateTimeField(verbose_name='Дата создания', default=now_local)

    class Meta:
        verbose_name = 'Счет'
        verbose_name_plural = 'Счета'
        ordering = ['-id']

    def __str__(self):
        return self.name


class OperationType(models.Model):
    ACTION_CHOICES = (
        ('income', 'доход'),
        ('expense', 'расход'),
    )
    name = models.CharField(verbose_name='Название', max_length=50, choices=ACTION_CHOICES, unique=True)

    class Meta:
        verbose_name = 'Вид операции'
        verbose_name_plural = 'Виды операции'
        ordering = ['-id']

    def __str__(self):
        return self.get_name_display()


class Category(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    operation_type = models.ForeignKey(OperationType, on_delete=models.CASCADE)
    name = models.CharField(verbose_name='Название', max_length=255)
    code_name = models.CharField(verbose_name='Кодовое название', max_length=255, null=True)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['-id']

    def __str__(self):
        return self.name


class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE)

    date = models.DateTimeField(verbose_name='Дата операции', default=now_local)
    sum = models.DecimalField(verbose_name='Сумма', max_digits=30, decimal_places=2)
    tag = models.CharField(verbose_name='Тег', max_length=255, null=True, blank=True)
    comment = models.TextField(verbose_name='Комментарий', null=True, blank=True)

    class Meta:
        verbose_name = 'Операция'
        verbose_name_plural = 'Операции'
        ordering = ['-date']


class PlannedBudget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    sum = models.DecimalField(verbose_name='Сумма', max_digits=30, decimal_places=2, default=0)
    date = models.DateField(verbose_name='Месяц и год бюджета', default=now_local)

    class Meta:
        verbose_name = 'Планируемый бюджет'
        verbose_name_plural = 'Планируемые бюджеты'
        ordering = ['-id']
