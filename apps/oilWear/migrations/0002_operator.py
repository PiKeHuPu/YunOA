# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2019-11-14 10:34
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('oilWear', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Operator',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('operator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='操作人')),
                ('vehicle', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='oilWear.Vehicle', verbose_name='载具')),
            ],
        ),
    ]
