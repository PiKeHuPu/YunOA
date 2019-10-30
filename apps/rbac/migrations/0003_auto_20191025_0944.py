# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2019-10-25 09:44
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rbac', '0002_specialrole'),
    ]

    operations = [
        migrations.AlterField(
            model_name='specialrole',
            name='title',
            field=models.CharField(choices=[('0', '出纳'), ('1', '财务总监')], max_length=10, verbose_name='角色名'),
        ),
    ]
