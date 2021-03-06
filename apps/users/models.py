from datetime import datetime

from django.db import models
from django.contrib.auth.models import AbstractUser, User


# from rbac.models import Role


class UserProfile(AbstractUser):
    """
    用户: makemigration提示错误：sers.UserProfile.user_permissions: (fields.E304)，
    需要在settings中指定自定义认证模型：AUTH_USER_MODEL = 'users.UserProfile'
    """
    name = models.CharField(max_length=20, default="", verbose_name="姓名")
    birthday = models.DateField(null=True, blank=True, verbose_name="出生日期")
    gender = models.CharField(max_length=10, choices=(("male", "男"), ("famale", "女")), default="male", verbose_name="性别")
    mobile = models.CharField(max_length=11, default="", verbose_name="电话")
    email = models.EmailField(max_length=100, verbose_name="邮箱")
    image = models.ImageField(upload_to="image/%Y/%m", default="image/default.jpg", max_length=100, null=True, blank=True)
    department = models.ForeignKey("Structure", null=True, blank=True, verbose_name="部门")
    is_dep_administrator = models.BooleanField(default=False, verbose_name="是否是部门物资管理员")
    post = models.CharField(max_length=50, null=True, blank=True, verbose_name="职位")
    superior = models.ForeignKey("self", null=True, blank=True, verbose_name="上级主管")
    roles = models.ManyToManyField("rbac.Role", verbose_name="角色", blank=True)
    joined_date = models.DateField(null=True, blank=True, verbose_name="入职日期")
    # 常用银行卡信息
    bank_card = models.CharField(max_length=35, default="", verbose_name="银行卡")
    bank_name = models.CharField(max_length=10, default="", verbose_name="银行名字")
    bank_user_name = models.CharField(max_length=10, default="", verbose_name="银行卡用户名")
    # 个人岗位职责
    personal_statement = models.TextField(default=None, blank=True, null=True, verbose_name="个人岗位职责")

    class Meta:
        verbose_name = "用户信息"
        verbose_name_plural = verbose_name
        ordering = ['id']

    def __str__(self):
        return self.name


class Structure(models.Model):
    """
    组织架构
    """
    type_choices = (("firm", "公司"), ("department", "部门"))
    title = models.CharField(max_length=60, verbose_name="名称")
    type = models.CharField(max_length=20, choices=type_choices, default="department", verbose_name="类型")
    parent = models.ForeignKey("self", null=True, blank=True, verbose_name="父类架构")
    adm_list = models.CharField(max_length=50, null=True, blank=True, verbose_name="部门负责人")
    administrator = models.ForeignKey(UserProfile, blank=True, null=True, related_name='asset_admin', on_delete=models.SET_NULL, verbose_name="部门资产管理员")
    super_adm = models.BooleanField(default=False, verbose_name="是否有全部部门管理权限")
    vice_manager = models.ForeignKey(UserProfile, related_name="vice_manager", blank=True, null=True, verbose_name="分管副总")
    adm_work = models.CharField(max_length=50, null=True, blank=True, verbose_name="日志填写员")

    class Meta:
        verbose_name = "组织架构"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.title


