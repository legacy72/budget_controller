# Generated by Django 3.0.3 on 2020-08-17 09:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_auto_20200611_0639'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='code_name',
            field=models.CharField(max_length=255, null=True, verbose_name='Кодовое название'),
        ),
    ]
