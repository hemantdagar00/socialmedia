# Generated by Django 3.2.13 on 2022-07-18 10:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('newsfeed', '0022_userrelationdetail_user2'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userrelationdetail',
            name='user2',
        ),
    ]
