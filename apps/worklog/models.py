from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth import get_user_model

from users.models import Structure

User = get_user_model()
# Create your models here.


class Worklog(models.Model):
    """
    工作日志字段
    """
    worklog = models.TextField(max_length=500, verbose_name="工作内容")
    status = models.IntegerField(max_length= 10, verbose_name="是否完成")
    depart = models.ForeignKey(Structure, verbose_name="部门")
    reason = models.TextField(blank=True,max_length=300, verbose_name="未完成原因")
    # is_delete = models.BooleanField(default=False, verbose_name="是否删除")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    over_time = models.DateTimeField(blank=True, null=True, verbose_name="任务完成时间")
    plan_status = models.BooleanField(default=False,verbose_name="是否含有日志进度描述")
    cre_man = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, verbose_name="创建人")


class WorklogPart(models.Model):
    """
        未完成工作日志日志
    """
    worklog_part = models.ForeignKey(Worklog,verbose_name="原日志信息")
    change_time = models.DateTimeField(auto_now_add=True,verbose_name="修改时间")
    task_detail = models.TextField(max_length=500, verbose_name="进度描述")