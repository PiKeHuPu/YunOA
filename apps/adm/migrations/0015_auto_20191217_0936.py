# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2019-12-17 09:36
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adm', '0014_auto_20191217_0927'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assetapprove',
            name='purpose',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='用途'),
        ),
    ]