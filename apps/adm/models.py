import django
from django.db import models
from django.contrib.auth import get_user_model
from utils.type_constant import CHOICES
from datetime import datetime
from users.models import Structure
User = get_user_model()

class Supplier(models.Model):
    """
    分销商管理
    """
    company = models.CharField(max_length=30, verbose_name="公司名称")
    address = models.CharField(max_length=100, verbose_name="地址")
    linkname = models.CharField(max_length=20, verbose_name="联系人")
    phone = models.CharField(max_length=20, verbose_name="联系电话")
    status = models.BooleanField(default=True, verbose_name="状态")
    belongs_to = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL, verbose_name="责任人")
    desc = models.TextField(blank=True, null=True, verbose_name="备注")
    add_time = models.DateTimeField(auto_now_add=True, verbose_name="添加时间")

    class Meta:
        verbose_name = "分销商管理"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.company


class Customer(models.Model):
    """
    客户信息
    """
    unit = models.CharField(max_length=50, verbose_name="客户单位")
    address = models.CharField(max_length=100, verbose_name="地址")
    name = models.CharField(max_length=20, verbose_name="联系人")
    phone = models.CharField(max_length=30, verbose_name="联系电话")
    belongs_to = models.ForeignKey(User, blank=True, null=True , on_delete=models.SET_NULL, verbose_name="责任人")
    status = models.BooleanField(default=True, verbose_name="状态")
    desc = models.TextField(blank=True, null=True, verbose_name="备注")
    add_time = models.DateTimeField(auto_now_add=True, verbose_name="添加时间")

    class Meta:
        verbose_name = "客户管理"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.unit


class AssetType(models.Model):
    """
    资产仓库
    """
    name = models.CharField(max_length=30, verbose_name="仓库名称", help_text="仓库名称")
    structure = models.ForeignKey(Structure, related_name='assetType', blank=True, null=True, on_delete=models.SET_NULL, verbose_name='资产到期提醒部门')
    desc = models.TextField(blank=True, null=True, verbose_name="备注")


    class Meta:
        verbose_name = "资产仓库"

    def __str__(self):
        return self.name

class AssetUseAddress(models.Model):
    """
    资产使用地址
    """
    name = models.CharField(max_length=30, verbose_name="详细地址", help_text="详细地址")
    desc = models.TextField(blank=True, null=True, verbose_name="备注")

    class Meta:
        verbose_name = "资产使用地址"

    def __str__(self):
        return self.name


class Asset(models.Model):
    asset_status = (
        ("0", "闲置"),
        ("1", "在用"),
        ("2", "维修"),
        ("3", "报废"),
        ("4", "售出")
    )
    due_choices = (
        ("0", "不提醒"),
        ("1", "提醒"),
    )
    assetNum = models.CharField(max_length=128, default="", verbose_name="资产编号")
    assetType = models.ForeignKey(AssetType, blank=True, null=True, on_delete=models.SET_NULL, verbose_name="资产仓库")
    brand = models.CharField(max_length=20, blank=True, null=True, verbose_name="名称")
    model = models.CharField(max_length=30, default="", verbose_name="型号")
    # warehouse = models.CharField(choices=warehouse_choices, default="1", max_length=20, verbose_name="仓库")
    # price = models.IntegerField(blank=True, null=True, verbose_name="价格")
    # buyDate = models.DateField(verbose_name="购买日期")
    dueremind= models.CharField(choices=due_choices, max_length=20, default="0", verbose_name="到期提醒")
    dueDate = models.DateField(verbose_name="到期日期", null=True, blank=True, default=django.utils.timezone.now)
    status = models.CharField(choices=asset_status, max_length=20, default="1", verbose_name="资产状态")
    assetCount = models.IntegerField(default=1, verbose_name="资产数量")
    assetUnit = models.CharField(max_length=20, default='个', verbose_name="资产单位")
    # customer = models.CharField(max_length=80, default="", blank=True, null=True, verbose_name="客户信息")
    # owner = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL, verbose_name="使用人")
    operator = models.CharField(max_length=20, default="", verbose_name="入库人")
    add_time = models.DateTimeField(auto_now_add=True, verbose_name="添加时间", null=True, blank=True)
    desc = models.TextField(default="", blank=True, null=True, verbose_name="备注信息")

    class Meta:
        verbose_name = "资产管理"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.assetNum


class AssetFile(models.Model):
    asset = models.ForeignKey(Asset, blank=True, null=True, on_delete=models.SET_NULL, verbose_name="资产")
    upload_user = models.CharField(max_length=20, verbose_name="上传人")
    file_content = models.ImageField(upload_to="asset_file/%Y/%m", null=True, blank=True, verbose_name="资产文件")
    add_time = models.DateTimeField(auto_now_add=True, verbose_name="上传时间")


class AssetLog(models.Model):
    asset = models.ForeignKey(Asset, verbose_name="资产")
    operator = models.CharField(max_length=20, verbose_name="操作人")
    desc = models.TextField(default="", verbose_name="备注")
    add_time = models.DateTimeField(auto_now_add=True, verbose_name="添加时间")

    class Mate:
        verbose_name = "变更记录"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.asset


class AssetUseLog(models.Model):
    """
    资产使用记录
    """
    party_choices = CHOICES['Party_type']
    back_choices = CHOICES['Asset_give']
    asset = models.ForeignKey(Asset, verbose_name="资产")
    useCount = models.IntegerField(default=1, verbose_name="领取数量")
    operator = models.CharField(max_length=20, verbose_name="领取人")
    area = models.TextField(default="", verbose_name="使用地区")
    title = models.TextField(default="", verbose_name="用途")
    add_time = models.DateTimeField(auto_now_add=True, verbose_name="添加时间")
    use_time = models.DateField(null=True, blank=True, verbose_name="预计归还日期")
    party = models.CharField(max_length=1, default="0", choices=party_choices, verbose_name="领取方")
    give_back = models.CharField(max_length=1, default="0", choices=party_choices, verbose_name="是否归回")
    back_date = models.DateField(verbose_name="归还日期", null=True, blank=True, default=django.utils.timezone.now)
    back_count = models.IntegerField(default=0, verbose_name="归还数量")
    back_creator = models.ForeignKey(User, null=True, blank=True, verbose_name="归还记录员")
    class Mate:
        verbose_name = "使用记录"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.asset


class ServiceInfo(models.Model):
    content = models.TextField(verbose_name="记录内容")
    writer = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL, verbose_name="记录人")
    is_reminding = models.BooleanField(default=False, verbose_name="邮件消息提醒")
    add_time = models.DateTimeField(auto_now_add=True, verbose_name="添加时间")

    class Mate:
        verbose_name = "服务记录"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.content


class EquipmentType(models.Model):
    """
    设备类型
    """
    name = models.CharField(max_length=30, verbose_name="类型名称", help_text="类型名称")
    desc = models.TextField(blank=True, null=True, verbose_name="备注")

    class Meta:
        verbose_name = "设备类型"
        verbose_name_plural = verbose_name
        ordering = ['id']

    def __str__(self):
        return self.name


class Equipment(models.Model):
    number = models.CharField(max_length=30, default="", verbose_name="设备编号")
    equipment_type = models.ForeignKey(EquipmentType, blank=True, null=True, on_delete=models.SET_NULL, verbose_name="设备类型")
    equipment_model = models.CharField(max_length=50, default="", verbose_name="设备型号")
    buy_date = models.DateField(verbose_name="购买日期")
    warranty_date = models.DateField(verbose_name="质保日期")
    accounting = models.BooleanField(default=False, verbose_name="费用核算状态")
    config_desc = models.TextField(blank=True, null=True, verbose_name="配置说明")
    customer = models.ForeignKey(Customer, blank=True, null=True, on_delete=models.SET_NULL, verbose_name="客户信息")
    supplier = models.ForeignKey(Supplier, blank=True, null=True, on_delete=models.SET_NULL, verbose_name="分销商")
    service_info = models.ManyToManyField(ServiceInfo, blank=True, verbose_name="服务记录")

    class Meta:
        verbose_name = "设备管理"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.number



# class AssetDepartment(models.Model):
#     """
#     资产部门
#     """
#     name = models.CharField(max_length=20, verbose_name="名称")
#     administrator = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL, verbose_name="资产管理员")
#     super_adm = models.BooleanField(default=False, verbose_name="是否有全部部门管理权限")
#     is_delete = models.BooleanField(default=False, verbose_name="是否删除")


class AssetWarehouse(models.Model):
    """
    资产仓库
    """
    name = models.CharField(max_length=20, verbose_name="名称")
    department = models.ForeignKey(Structure, on_delete=models.CASCADE, verbose_name="所属资产部门")
    remark = models.TextField(blank=True, null=True, verbose_name="备注")
    is_delete = models.BooleanField(default=False, verbose_name="是否删除")
    is_all_view = models.BooleanField(default=False, verbose_name="是否所有人可见")
    verifier = models.ManyToManyField(User, blank=True, null=True, verbose_name="物资审批人")


class AssetInfo(models.Model):
    """
    资产信息
    """
    asset_status = (
        ("0", "闲置"),
        ("1", "在用"),
        ("2", "维修"),
        ("3", "报废"),
        ("4", "售出")
    )
    number = models.CharField(max_length=20, verbose_name="资产编号")
    name = models.CharField(max_length=50, verbose_name="资产名称")
    department = models.ForeignKey(Structure, on_delete=models.CASCADE, verbose_name="所属部门")
    warehouse = models.ForeignKey(AssetWarehouse, on_delete=models.CASCADE, verbose_name="所属仓库")
    quantity = models.IntegerField(verbose_name="数量")
    status = models.CharField(choices=asset_status, max_length=5, default="0", verbose_name="资产状态")
    user = models.ForeignKey(User, related_name="asset_user", on_delete=models.SET_NULL, null=True, blank=True, verbose_name="使用人")
    operator = models.ForeignKey(User, related_name="asset_operator", on_delete=models.DO_NOTHING, verbose_name="录入人")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="录入时间")
    due_time = models.DateField(null=True, blank=True, verbose_name="到期时间")
    is_delete = models.BooleanField(default=False, verbose_name="是否删除")
    unit = models.CharField(max_length=20, verbose_name="单位")
    type = models.CharField(max_length=20, verbose_name="型号")
    remark = models.TextField(max_length=500, verbose_name="备注信息")
    is_no_return = models.BooleanField(default=False, verbose_name="无需归还")
    is_no_approve = models.BooleanField(default=False, verbose_name="无需审批")


class AssetEditFlow(models.Model):
    """
    资产变更记录
    """
    asset = models.ForeignKey(AssetInfo, on_delete=models.DO_NOTHING, verbose_name='相关资产')
    operator = models.ForeignKey(User, on_delete=models.DO_NOTHING, verbose_name='操作人')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="添加时间")
    content = models.CharField(max_length=20, verbose_name='内容')


class AssetApprove(models.Model):
    """
    物资记录
    """
    proposer = models.ForeignKey(User, related_name='asset_proposer', on_delete=models.DO_NOTHING, verbose_name="申请人")
    asset = models.ForeignKey(AssetInfo, on_delete=models.DO_NOTHING, verbose_name="物资")
    quantity = models.IntegerField(verbose_name="数量")
    purpose = models.CharField(max_length=100, blank=True, null=True, verbose_name="用途")
    return_date = models.DateField(null=True, blank=True, verbose_name="预计归还时间")
    status = models.CharField(max_length=10, verbose_name="状态")  # '0': 未审批  '1': 审批中  '2': 审批通过  '3': 审批未通过
    use_status = models.CharField(max_length=10, verbose_name="使用状态")
    # '0': 未领用  '1': 未归还  '2': 已归还  '3': 无需归还  '4': 已转移  '5': 已取消
    type = models.CharField(max_length=10, verbose_name="类型")  # '0': 物资领用  '1': 资产转移
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    t_return_date = models.DateField(null=True, blank=True, verbose_name="归还日期")
    return_quantity = models.IntegerField(default=0, verbose_name="归还数量")
    return_operator = models.ForeignKey(User, related_name="return_operator", blank=True, null=True, verbose_name="归还操作人")
    transfer_department = models.ForeignKey(Structure, blank=True, null=True, verbose_name="转移部门")
    transfer_warehouse = models.ForeignKey(AssetWarehouse, blank=True, null=True, verbose_name="转移仓库")


class AssetApproveDetail(models.Model):
    """
    物资审批
    """
    status = models.CharField(max_length=4, default="0", verbose_name="审批状态")  # "0": 等待审批  “1”：审批中  “2”：审批完成
    approver = models.ForeignKey(User, on_delete=models.DO_NOTHING, verbose_name="审批人")
    asset_order = models.ForeignKey(AssetApprove, on_delete=models.DO_NOTHING, verbose_name="物资申请")
    is_pass = models.CharField(max_length=10, blank=True, null=True, verbose_name="是否通过")  # "0": 不通过  "1": 通过
    remark = models.CharField(max_length=50, blank=True, null=True, verbose_name="审批意见")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")






