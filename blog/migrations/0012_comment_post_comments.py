# Generated by Django 4.0.3 on 2022-07-19 13:54

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0011_alter_post_difficulty'),
    ]

    operations = [
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('body', models.TextField()),
                ('name', models.CharField(help_text='Your Name...', max_length=75)),
                ('email', models.EmailField(help_text='Your Email...', max_length=254)),
            ],
        ),
        migrations.AddField(
            model_name='post',
            name='comments',
            field=models.ManyToManyField(to='blog.comment'),
        ),
    ]