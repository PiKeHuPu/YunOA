# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2019-07-15 11:02
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('personal', '0006_businessapply_title'),
    ]

    operations = [
        migrations.AddField(
            model_name='businessapply',
            name='all_fee',
            field=models.CharField(blank=True, max_length=12, verbose_name='总费用'),
        ),
    ]
