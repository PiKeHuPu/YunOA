# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2019-12-06 09:16
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_auto_20191205_0902'),
    ]

    operations = [
        migrations.AddField(
            model_name='structure',
            name='approver',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='asset_approver', to=settings.AUTH_USER_MODEL, verbose_name='部门资产审批人'),
        ),
        migrations.AlterField(
            model_name='structure',
            name='administrator',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='asset_admin', to=settings.AUTH_USER_MODEL, verbose_name='部门资产管理员'),
        ),
    ]
