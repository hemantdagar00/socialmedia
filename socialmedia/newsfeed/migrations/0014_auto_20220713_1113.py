# Generated by Django 3.2.13 on 2022-07-13 11:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('newsfeed', '0013_photo'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Photo',
        ),
        migrations.AddField(
            model_name='status',
            name='photo',
            field=models.ImageField(blank=True, null=True, upload_to='upload_image/'),
        ),
    ]
