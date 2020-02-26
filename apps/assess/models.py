from django.db import models

from users.models import Structure, UserProfile


class AssessDepDetail(models.Model):
    """
    部门目标
    """
    department = models.ForeignKey(Structure, on_delete=models.CASCADE, verbose_name="部门")
    content = models.CharField(max_length=600, verbose_name="部门目标")
    year = models.CharField(max_length=4, blank=True, null=True, verbose_name="年")
    month = models.CharField(max_length=10, blank=True, null=True, verbose_name="月")
    is_done = models.BooleanField(default=False, verbose_name="是否审核完成")
    verifier = models.ForeignKey(UserProfile, on_delete=models.CASCADE, blank=True, null=True, verbose_name="审核人")


class AssessPerDetail(models.Model):
    """
    个人目标
    """
    dep_goal = models.ForeignKey(AssessDepDetail, on_delete=models.CASCADE, verbose_name="关联部门目标")
    content = models.CharField(max_length=300, verbose_name="个人目标内容")
    principal = models.ForeignKey(UserProfile, on_delete=models.DO_NOTHING, verbose_name="负责人")
    describe = models.CharField(max_length=500, blank=True, null=True, verbose_name="工作描述")
    complete_degree = models.CharField(max_length=5, blank=True, null=True, verbose_name="完成度")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")


class AssessScore(models.Model):
    """
    评分
    """
    dep_goal = models.ForeignKey(AssessDepDetail, on_delete=models.CASCADE, verbose_name="关联部门目标")
    principal = models.ForeignKey(UserProfile, on_delete=models.DO_NOTHING, verbose_name="负责人")
    goal_score = models.FloatField(blank=True, null=True, verbose_name="目标考核分数")
    capacity_score = models.FloatField(blank=True, null=True, verbose_name="能力考核分数")
    attitude_score = models.FloatField(blank=True, null=True, verbose_name="态度考核分数")
    total_score = models.FloatField(blank=True, null=True, verbose_name="总分")
    remark = models.CharField(max_length=500, blank=True, null=True, verbose_name="备注")
# Create your models here.
