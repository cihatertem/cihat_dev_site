# Generated by Django 4.0.3 on 2022-10-21 13:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0027_alter_tag_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='short_description',
            field=models.CharField(blank=True, max_length=350, null=True),
        ),
    ]