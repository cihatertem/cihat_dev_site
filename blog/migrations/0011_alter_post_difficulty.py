# Generated by Django 4.0.3 on 2022-07-19 13:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0010_remove_post_title_slug_post_slug'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='difficulty',
            field=models.CharField(choices=[(1, 'Easy'), (2, 'Medium'), (3, 'Hard')], max_length=50, null=True),
        ),
    ]