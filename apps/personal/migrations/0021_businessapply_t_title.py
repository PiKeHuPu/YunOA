# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2019-12-02 16:08
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('personal', '0020_workorder_t_title'),
    ]

    operations = [
        migrations.AddField(
            model_name='businessapply',
            name='t_title',
            field=models.CharField(default='', max_length=30, verbose_name='申请标题'),
            preserve_default=False,
        ),
    ]
