# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2019-12-05 15:11
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('personal', '0021_businessapply_t_title'),
    ]

    operations = [
        migrations.CreateModel(
            name='WorkOrderCard',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('payee', models.CharField(blank=True, max_length=300, null=True, verbose_name='收款方')),
                ('bank_account', models.CharField(blank=True, max_length=30, null=True, verbose_name='银行账户')),
                ('bank_info', models.CharField(blank=True, max_length=300, null=True, verbose_name='开户行')),
                ('createman', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cm', to=settings.AUTH_USER_MODEL, verbose_name='银行卡信息人')),
            ],
        ),
        migrations.AlterField(
            model_name='businessapply',
            name='status',
            field=models.CharField(choices=[('-1', '可以申请'), ('0', '等待审批'), ('1', '审批中'), ('2', '审批完成'), ('3', '审批被退回'), ('4', '报销完成'), ('5', '等待付款')], default='-1', max_length=10, verbose_name='审批状态'),
        ),
    ]