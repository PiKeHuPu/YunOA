# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2019-11-04 09:48
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('personal', '0017_auto_20190918_1501'),
    ]

    operations = [
        migrations.AddField(
            model_name='workorder',
            name='is_apply_only',
            field=models.BooleanField(default=False, verbose_name='是否无需报销'),
        ),
    ]