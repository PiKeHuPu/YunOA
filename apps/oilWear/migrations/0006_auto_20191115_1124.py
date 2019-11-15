# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2019-11-15 11:24
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('oilWear', '0005_auto_20191115_0936'),
    ]

    operations = [
        migrations.AlterField(
            model_name='operator',
            name='operator',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='管理员'),
        ),
        migrations.AlterField(
            model_name='operator',
            name='vehicle',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='oilWear.Vehicle', verbose_name='载具'),
        ),
    ]
