# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2019-11-12 16:10
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('personal', '0018_workorder_is_apply_only'),
    ]

    operations = [
        migrations.AlterField(
            model_name='workorderlog',
            name='type',
            field=models.CharField(choices=[('0', '申请'), ('1', '报销')], default='0', max_length=10, verbose_name='日志类型'),
        ),
    ]
