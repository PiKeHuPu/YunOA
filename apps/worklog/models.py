from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth import get_user_model

from users.models import Structure

User = get_user_model()
# Create your models here.


class Worklog(models.Model):
    """
    看板工作内容
    """
    content = models.TextField(max_length=500, blank=True, null=True, verbose_name="工作内容")
    step = models.IntegerField( blank=True, null=True, verbose_name="计划步数")
    is_done = models.BooleanField(default=False,  verbose_name="是否完成")
    create_time = models.DateTimeField(auto_now_add=True, blank=True, null=True, verbose_name="创建时间")
    cre_man = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, verbose_name="创建人")


class WorklogPart(models.Model):
    """
    看板工作阶段计划
    """
    content_part = models.ForeignKey(Worklog, verbose_name="工作计划")
    plan = models.TextField(max_length=500, blank=True, null=True, verbose_name="计划描述")
    stage = models.IntegerField(blank=True, null=True, verbose_name="第几步计划")
    is_done = models.BooleanField(default=False,  verbose_name="是否完成")
    s_time = models.DateTimeField(blank=True, null=True, verbose_name="任务开始时间")
    e_time = models.DateTimeField(blank=True, null=True, verbose_name="任务结束时间")
    performance = models.TextField(max_length=500, blank=True, null=True, verbose_name="完成情况")
    remark = models.TextField(max_length=500, blank=True, null=True, verbose_name="备注")
    dutyman = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, verbose_name="责任人")
    department = models.ForeignKey(Structure, verbose_name="部门")


class WorkRecordTem(models.Model):
    """
    看板日志模板
    """
    content = models.CharField(max_length=300, verbose_name="工作内容")
    user = models.ForeignKey(User, verbose_name="责任人")
    remark = models.CharField(max_length=300, blank=True, null=True, verbose_name="备注")
    type = models.CharField(max_length=2, verbose_name="工作类型")  # "0": 常规性固定工作  "1": 临时性工作
    is_delete = models.BooleanField(default=False, verbose_name="是否删除")


class WorkRecord(models.Model):
    """
    看板日志完成情况
    """
    tem = models.ForeignKey(WorkRecordTem, verbose_name="模板关联")
    is_submit = models.BooleanField(default=False, verbose_name="是否提交")
    date = models.DateField(auto_now_add=True, verbose_name="日期")
    is_done = models.BooleanField(default=False, verbose_name="是否完成")