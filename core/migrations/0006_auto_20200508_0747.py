# Generated by Django 3.0.3 on 2020-05-08 07:47

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_auto_20200414_1344'),
    ]

    operations = [
        migrations.AlterField(
            model_name='plannedbudget',
            name='date',
            field=models.DateField(default=django.utils.timezone.now, verbose_name='Месяц и год бюджета'),
        ),
    ]
