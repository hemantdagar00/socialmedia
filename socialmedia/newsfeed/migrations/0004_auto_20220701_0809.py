# Generated by Django 3.2.13 on 2022-07-01 08:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('newsfeed', '0003_votes'),
    ]

    operations = [
        migrations.AddField(
            model_name='status',
            name='dislike',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='status',
            name='like',
            field=models.IntegerField(default=0),
        ),
        migrations.DeleteModel(
            name='Votes',
        ),
    ]
