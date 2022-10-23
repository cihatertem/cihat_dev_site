# Generated by Django 4.0.3 on 2022-10-06 10:18

import blog.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0023_alter_post_hero_img'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='hero_img',
            field=models.ImageField(blank=True, default='default.jpg', null=True, upload_to=blog.models.post_directory_path, verbose_name="Post's Hero Image"),
        ),
    ]