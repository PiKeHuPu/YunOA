# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2019-12-18 11:39
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('personal', '0026_auto_20191217_1423'),
    ]

    operations = [


        migrations.AddField(
            model_name='businessapply',
            name='feeid',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='personal.FeeType', verbose_name='费用id'),
        ),
    ]
