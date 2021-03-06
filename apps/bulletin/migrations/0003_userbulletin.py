# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2019-10-31 11:55
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('bulletin', '0002_auto_20191024_1601'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserBulletin',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('last_time', models.DateTimeField(auto_now_add=True, verbose_name='最后查看时间')),
                ('bulletin', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bulletin.Bulletin', verbose_name='公告')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='用户')),
            ],
        ),
    ]
