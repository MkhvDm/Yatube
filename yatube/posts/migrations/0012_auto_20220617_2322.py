# Generated by Django 2.2.16 on 2022-06-17 20:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0011_follow'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Время публикации комментария'),
        ),
    ]
