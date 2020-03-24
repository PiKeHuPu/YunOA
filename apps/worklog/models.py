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
    content = models.TextField(max_length=500, blank=True, null=True, verbose_name="工作内容")
    department = models.ForeignKey(Structure, verbose_name="部门")
    step = models.IntegerField( blank=True, null=True, verbose_name="计划步数")
    # is_delete = models.BooleanField(default=False, verbose_name="是否删除")
    is_done = models.BooleanField(default=False,  verbose_name="是否完成")
    # over_time = models.DateTimeField(blank=True, null=True, verbose_name="任务完成时间")
    # plan_status = models.BooleanField(default=False,verbose_name="是否含有日志进度描述")
    # cre_man = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, verbose_name="创建人")


class WorklogPart(models.Model):
    """
        未完成工作日志日志
    """
    content_part = models.ForeignKey(Worklog, verbose_name="工作计划")
    plan = models.TextField(max_length=500, blank=True, null=True, verbose_name="计划描述")
    stage = models.IntegerField( blank=True, null=True, verbose_name="第几步计划")
    is_done = models.BooleanField(default=False,  verbose_name="是否完成")
    s_time = models.DateTimeField(blank=True, null=True, verbose_name="任务开始时间")
    e_time = models.DateTimeField(blank=True, null=True, verbose_name="任务结束时间")
    performance = models.TextField(max_length=500, blank=True, null=True, verbose_name="完成情况")
    remark = models.TextField(max_length=500, blank=True, null=True, verbose_name="备注")
    dutyman = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, verbose_name="责任人")