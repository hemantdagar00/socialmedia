# Generated by Django 3.2.13 on 2022-07-14 08:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('newsfeed', '0018_comment_comments_on_comment'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='comment_text',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
