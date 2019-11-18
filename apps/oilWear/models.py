from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()
# Create your models here.


class Vehicle(models.Model):
    """
    载具
    """
    license_plate = models.CharField(max_length=10, verbose_name="车牌号")
    department = models.CharField(max_length=20, verbose_name="所属部门")
    type = models.CharField(max_length=30, verbose_name="车型")
    is_delete = models.BooleanField(default=False, verbose_name="是否删除")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    creator = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, verbose_name="创建人")


class OilWear(models.Model):
    """
    油耗表
    """
    vehicle = models.ForeignKey(Vehicle, verbose_name="载具")
    operator = models.ForeignKey(User, verbose_name="提交人")
    refuel_time = models.DateField(verbose_name="加油时间")
    operate_time = models.DateTimeField(auto_now_add=True, verbose_name="操作时间")
    mileage = models.FloatField(verbose_name="加油前公里数")
    weight = models.FloatField(verbose_name="加油量(升)")
    price = models.FloatField(verbose_name="油量单价(升)")
    amount = models.FloatField(verbose_name="金额")
    remark = models.CharField(max_length=50, null=True, blank=True, verbose_name="备注")


class Operator(models.Model):
    """
    载具管理员
    """
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, verbose_name="载具")
    operator = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="管理员")
