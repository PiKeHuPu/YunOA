# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2019-12-06 11:17
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adm', '0009_auto_20191205_0908'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assetinfo',
            name='number',
            field=models.CharField(max_length=20, verbose_name='资产编号'),
        ),
    ]
