# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2019-11-14 13:30
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('oilWear', '0002_operator'),
    ]

    operations = [
        migrations.AddField(
            model_name='vehicle',
            name='is_delete',
            field=models.BooleanField(default=False, verbose_name='是否删除'),
        ),
    ]
