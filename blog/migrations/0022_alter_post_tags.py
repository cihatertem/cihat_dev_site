# Generated by Django 4.0.3 on 2022-07-26 16:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0021_alter_comment_created_at_alter_comment_post_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='tags',
            field=models.ManyToManyField(blank=True, related_name='tags', to='blog.tag'),
        ),
    ]