# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2019-12-06 16:25
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adm', '0011_asseteditflow'),
    ]

    operations = [
        migrations.AddField(
            model_name='assetinfo',
            name='is_no_approve',
            field=models.BooleanField(default=False, verbose_name='无需审批'),
        ),
        migrations.AddField(
            model_name='assetinfo',
            name='is_no_return',
            field=models.BooleanField(default=False, verbose_name='无需归还'),
        ),
    ]