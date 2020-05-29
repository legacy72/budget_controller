from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now as now_local


class Bill(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    name = models.CharField(verbose_name='Название', max_length=255)
    sum = models.DecimalField(verbose_name='Сумма', max_digits=30, decimal_places=2)
    created_date = models.DateTimeField(verbose_name='Дата создания', default=now_local)

    class Meta:
        verbose_name = 'Счет'
        verbose_name_plural = 'Счета'

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

    def __str__(self):
        return self.get_name_display()


class Category(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    operation_type = models.ForeignKey(OperationType, on_delete=models.CASCADE)
    name = models.CharField(verbose_name='Название', max_length=255)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

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


class PlannedBudget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    sum = models.DecimalField(verbose_name='Сумма', max_digits=30, decimal_places=2, default=0)
    date = models.DateField(verbose_name='Месяц и год бюджета', default=now_local)

    class Meta:
        verbose_name = 'Планируемый бюджет'
        verbose_name_plural = 'Планируемые бюджеты'
