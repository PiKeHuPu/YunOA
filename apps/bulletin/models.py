from django.db import models
from django.contrib.auth import get_user_model
from utils.type_constant import CHOICES

User = get_user_model()
# Create your models here.


class BulletinType(models.Model):
    """
    公告类型
    """
    status_choices = CHOICES['bulletin_status']
    title = models.CharField(max_length=20, verbose_name='标题')
    status = models.CharField(max_length=10, choices=status_choices, default='1', verbose_name='状态')  # ‘0’停用， ‘1’启用


class Bulletin(models.Model):
    """
    公告
    """
    type_choices = CHOICES['bulletin_type']
    status_choices = CHOICES['bulletin_status']
    title = models.CharField(max_length=100, verbose_name='标题')
    type = models.ForeignKey(BulletinType, related_name='bulletin', verbose_name='类型')   # '0'规章， ‘1’公告
    status = models.CharField(max_length=10, choices=status_choices, default='1', verbose_name='状态')  # ‘0’停用， ‘1’启用
    file_content = models.FileField(upload_to='file/%y/%m', blank=True, null=True, verbose_name='附件')
    creator = models.ForeignKey(User, related_name='bulletin', blank=True, null=True, on_delete=models.SET_NULL,
                               verbose_name='创建人')
    create_time = create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')


class UserBulletin(models.Model):
    """
    用户读取公告记录
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户')
    bulletin = models.ForeignKey('Bulletin', on_delete=models.CASCADE, verbose_name='公告')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    last_time = models.DateTimeField(auto_now_add=True, verbose_name='最后查看时间')


