from django.db import models

from users.models import Structure, UserProfile


class AssessDepDetail(models.Model):
    department = models.ForeignKey(Structure, on_delete=models.CASCADE, verbose_name="部门")
    content = models.CharField(max_length=600, verbose_name="部门目标")
    year = models.CharField(max_length=4, blank=True, null=True, verbose_name="年")
    month = models.CharField(max_length=10, blank=True, null=True, verbose_name="月")
    is_done = models.BooleanField(default=False, verbose_name="是否填写完成")


class AssessPerDetail(models.Model):
    dep_goal = models.ForeignKey(AssessDepDetail, on_delete=models.CASCADE, verbose_name="关联部门目标")
    content = models.CharField(max_length=300, verbose_name="个人目标内容")
    principal = models.ForeignKey(UserProfile, on_delete=models.DO_NOTHING, verbose_name="负责人")
    goal_score = models.IntegerField(blank=True, null=True, verbose_name="目标考核分数")
    capacity_score = models.IntegerField(blank=True, null=True, verbose_name="能力考核分数")
    attitude_score = models.IntegerField(blank=True, null=True, verbose_name="态度考核分数")
    describe = models.CharField(max_length=500, blank=True, null=True, verbose_name="工作描述")
    complete_degree = models.CharField(max_length=5, blank=True, null=True, verbose_name="完成度")
    remark = models.CharField(max_length=500, blank=True, null=True, verbose_name="备注")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
# Create your models here.
