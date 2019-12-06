import django
from django.db import models

from users.models import Structure

from django.contrib.auth import get_user_model

from adm.models import Customer


from utils.type_constant import CHOICES

User = get_user_model()


# class WorkOrder2(models.Model):
#     """
#     审批申请
#     """
#     type_choices = CHOICES['WorkOrder_type']
#     status_choices = CHOICES['WorlOrder_status']
#     number = models.CharField(max_length=10, verbose_name='工单号')
#     title = models.CharField(max_length=50, verbose_name='标题')
#     type = models.CharField(max_length=10, choices=type_choices, default='0', verbose_name='工单类型')
#     status = models.CharField(max_length=10, choices=status_choices, default='0', verbose_name='工单状态')
#     do_time = models.DateTimeField(default='', verbose_name='安排时间')
#     add_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
#     content = models.CharField(max_length=300, verbose_name='工单内容')
#     file_content = models.FileField(upload_to='file/%Y/%m', blank=True, null=True, verbose_name='项目资料')
#     customer = models.ForeignKey(Customer, verbose_name='客户信息')
#     proposer = models.ForeignKey(User, related_name='proposer', blank=True, null=True, on_delete=models.SET_NULL, verbose_name='申请人')
#     approver = models.ForeignKey(User, related_name='approver', blank=True, null=True, on_delete=models.SET_NULL, verbose_name='审批人')
#     receiver = models.ForeignKey(User, related_name='receiver', blank=True, null=True, on_delete=models.SET_NULL, verbose_name='接单人')
# 
#     class Meta:
#         verbose_name = '申报信息'
#         verbose_name_plural = verbose_name
# 
#     def __str__(self):
#         return self.title


class WorkOrder(models.Model):
    """
    审批申请
    """
    type_choices = CHOICES['WorkOrder_type']
    status_choices = CHOICES['WorlOrder_status']
    invoice_choices = CHOICES['invoice_choices']
    advance_choices = CHOICES['advance_choices']
    transport_choices = CHOICES['transport_choices']
    advance_choices = CHOICES['advance_choices']
    payment_choices = CHOICES['payment_choices']
    number = models.CharField(max_length=20, verbose_name='审批单号')   # 自动生成
    t_title = models.CharField(max_length=30, verbose_name="申请标题")
    title = models.TextField(verbose_name='工作内容')
    type = models.CharField(max_length=10, choices=type_choices, default='0', verbose_name='审批类型')
    status = models.CharField(max_length=10, choices=status_choices, default='0', verbose_name='审批状态')  # TODO 这个逻辑，被退回3，申请是重建
    start_time = models.DateTimeField(verbose_name='开始时间', null=True, blank=True, default=django.utils.timezone.now)
    end_time = models.DateTimeField( verbose_name='结束时间', null=True, blank=True, default=django.utils.timezone.now)
    # content = models.CharField(max_length=300, verbose_name='详情内容')
    thing = models.CharField(max_length=300, blank=True, verbose_name='事件')
    cost = models.CharField(max_length=12, blank=True, verbose_name='费用')
    # 费用详情----立项审批 0
    invoice_type = models.CharField(max_length=10, choices=invoice_choices, default='0', blank=True, null=True, verbose_name='发票类型')
    payee = models.CharField(max_length=300, blank=True, null=True, verbose_name='收款方')
    bank_account = models.CharField(max_length=30, blank=True, null=True, verbose_name='银行账户')
    bank_info = models.CharField(max_length=300, blank=True, null=True, verbose_name='开户行')
    advance = models.CharField(max_length=10, choices=advance_choices, default='0', verbose_name='是否预支') # 0 否， 1 预
    adv_payment = models.CharField(max_length=10, choices=payment_choices, default='0', verbose_name='完成预付款') # 0 否， 1 预
    is_apply_only = models.BooleanField(default=False, verbose_name="是否无需报销")
    # 出差审批 1
    people = models.CharField(max_length=300, blank=True, null=True, verbose_name='随行人员')
    transport = models.CharField(max_length=300, blank=True, null=True, choices=transport_choices, verbose_name='交通工具')
    becity = models.CharField(max_length=300, blank=True, null=True, verbose_name='出发地点')
    destination = models.CharField(max_length=300, blank=True, null=True, verbose_name='目标地点')

    next_user = models.ForeignKey(User, related_name='next_order', blank=True, null=True, on_delete=models.SET_NULL,
                                  verbose_name='当前审批人')
    cretor = models.ForeignKey(User, related_name='proposer', blank=True, null=True, on_delete=models.SET_NULL,
                               verbose_name='申请人')
    structure = models.ForeignKey(Structure, related_name='workorder', blank=True, null=True, on_delete=models.SET_NULL,
                                  verbose_name='申请时所在部门')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    file_content = models.FileField(upload_to='file/%Y/%m', blank=True, null=True, verbose_name='附件')

    class Meta:
        verbose_name = '申报信息'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.title


class WorkOrderCard(models.Model):
    createman = models.ForeignKey(User, related_name='cm'
                                  ,on_delete=models.CASCADE,verbose_name='银行卡信息人')
    payee = models.CharField(max_length=300, blank=True, null=True, verbose_name='收款方')
    bank_account = models.CharField(max_length=30, blank=True, null=True, verbose_name='银行账户')
    bank_info = models.CharField(max_length=300, blank=True, null=True, verbose_name='开户行')
    time = models.IntegerField(max_length=10, blank=False,null=True , verbose_name='使用次数')


class WorkOrderRecord(models.Model):
    """
    TODO 将要被取消的模型
    """
    type_choices = (('0', '退回'), ('1', "派发"), ('2', "执行"), ('3', "确认"))
    name = models.ForeignKey(User, verbose_name=u"记录人")
    work_order = models.ForeignKey(WorkOrder, verbose_name=u"工单信息")
    record_type = models.CharField(max_length=10, choices=type_choices, verbose_name=u"记录类型")
    content = models.CharField(max_length=500, verbose_name=u"记录内容", default="")
    file_content = models.FileField(upload_to='file/%Y/%m', blank=True, null=True, verbose_name='实施文档')
    add_time = models.DateTimeField(auto_now_add=True, verbose_name=u"记录时间")

    class Meta:
        verbose_name = u"执行记录"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.record_type





class WorkOrderLog(models.Model):
    """
    审批日志
    """
    record_type_choices = CHOICES['WorkOrderLog_record_type']
    type_choices = CHOICES['WorkOrderLog_type']
    item_type_choices = CHOICES['WorkOrder_type0']
    order_id = models.ForeignKey(WorkOrder, verbose_name='申报表id')
    record_type = models.CharField(max_length=10, choices=record_type_choices, verbose_name='审批意见')
    type = models.CharField(max_length=10, choices=type_choices, verbose_name='日志类型', default='0')   # ‘0’，审批， ‘1’， 报销
    desc = models.CharField(max_length=500, default='', verbose_name='审批意见详情')
    creator = models.ForeignKey(User, related_name='workorderlog', blank=True, null=True, on_delete=models.SET_NULL,
                                verbose_name='审批人')
    structure = models.ForeignKey(Structure, related_name='workorderlog', blank=True, null=True, on_delete=models.SET_NULL,
                                  verbose_name='审批时所在部门')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        verbose_name = '审批日志'
        verbose_name_plural = verbose_name


class WorkOrderFlow(models.Model):
    """
    审批流程: 用以记录审批的流程，
    """
    type_choices = CHOICES['WorkOrder_type']  # 审批类型
    factor_choices = CHOICES['WorkOrder_factor_type']  # 审批条件类型
    pro_type_choices = CHOICES['WorkOrder_pro_type']  # 报销立项分类
    process = models.CharField(max_length=300, verbose_name='审批流程')  # user_id|user_id|&user_id|  每一个|就是一级，带&这个的是条件
    factor_type = models.CharField(max_length=10, choices=factor_choices, verbose_name='审批条件类型')  # 0, 时间； 1, 金额
    factor = models.CharField(max_length=50, verbose_name='审批条件')
    carbon = models.CharField(max_length=300, verbose_name='抄送人')    # user_id|user_id
    order_type = models.CharField(max_length=10, choices=type_choices, verbose_name="审批类型")   # (('0', '立项审批'), ('1', '出差审批'))
    pro_type = models.CharField(max_length=10, choices=pro_type_choices, default='0' , verbose_name="报销立项分类") # (('0', '立项'), ('1', '报销')) 报销中用财务副总。所以在预付款的审批中。需要选1
    structure = models.ForeignKey(Structure, related_name='workorderflow', blank=True, null=True, on_delete=models.SET_NULL,
                                  verbose_name='申请部门')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updater = models.ForeignKey(User, related_name='workorderflowupdater', blank=True, null=True, 
                                on_delete=models.SET_NULL, verbose_name='更新人')
    update_time = models.DateTimeField(auto_now_add=True, verbose_name="更新时间")



    class Meta:
        verbose_name = '审批流程表'
        verbose_name_plural = verbose_name


# 报销
class BusinessApply(models.Model):
    """
    报销
    """
    transport_choices = CHOICES['transport_choices']
    type_choices = CHOICES['WorkOrder_type']  # 1.出差 ；2.立项
    status_choices = CHOICES['Apply_status']    # (('-1', '可以申请'), ('0', '等待审批'), ('1', '审批中'), ('2', '审批完成'), ('3', '审批被退回'), ('4', '付款完成'),('5','等待付款'))
    invoice_choices = CHOICES['invoice_choices']  # ('0', '增值税普通发票'), ('1', '增值税专用发票'), ('3', '增值税专用发票')
    type = models.CharField(max_length=10, choices=type_choices, default='0', verbose_name='审批类型')
    workorder = models.ForeignKey(WorkOrder, related_name='business', blank=True, null=True, on_delete=models.SET_NULL,
                               verbose_name='审批单')
    # 报销内容
    t_title = models.CharField(max_length=30, verbose_name="申请标题")
    title = models.TextField(verbose_name='工作内容')
    detail = models.TextField(blank=True, null=True, verbose_name='报销明细')
    invoice_type = models.CharField(max_length=10, choices=invoice_choices, default='0', blank=True, null=True,
                                    verbose_name='发票类型')
    # 收款信息
    payee = models.CharField(max_length=300, blank=True, null=True, verbose_name='收款方')
    bank_account = models.CharField(max_length=30, blank=True, null=True, verbose_name='银行账户')
    bank_info = models.CharField(max_length=300, blank=True, null=True, verbose_name='开户行')
    # 出差部分
    completion_info = models.TextField(null=True, verbose_name='完成情况')
    transport = models.CharField(max_length=300, blank=True, null=True, choices=transport_choices, verbose_name='交通工具')
    becity = models.CharField(max_length=300, blank=True, null=True, verbose_name='出发地点')
    destination = models.CharField(max_length=300, blank=True, null=True, verbose_name='目标地点')
    start_time = models.DateTimeField(verbose_name='开始时间', null=True)
    end_time = models.DateTimeField(verbose_name='结束时间', null=True)
    days = models.CharField(max_length=10, blank=True, null=True, verbose_name='出差天数')
    people = models.CharField(max_length=300, blank=True, null=True, verbose_name='随行人员')
    all_fee = models.CharField(max_length=12, blank=True, default=0, verbose_name='总费用')
    tran_fee = models.CharField(max_length=12, blank=True, default=0, verbose_name='交通费用')
    acco_fee = models.CharField(max_length=12, blank=True, default=0, verbose_name='住宿费用')
    food_fee = models.CharField(max_length=12, blank=True, default=0, verbose_name='餐饮费用')
    rece_fee = models.CharField(max_length=12, blank=True, default=0, verbose_name='招待费用')
    other_fee = models.CharField(max_length=12, blank=True, default=0, verbose_name='其他费用')
    # 审批属性
    status = models.CharField(max_length=10, choices=status_choices, default='-1', verbose_name='审批状态')
    next_user = models.ForeignKey(User, related_name='business_next_order', blank=True, null=True, on_delete=models.SET_NULL,
                                  verbose_name='当前审批人')
    cretor = models.ForeignKey(User, related_name='business', blank=True, null=True, on_delete=models.SET_NULL,
                               verbose_name='申请人')
    structure = models.ForeignKey(Structure, related_name='business', blank=True, null=True, on_delete=models.SET_NULL,
                                  verbose_name='申请时所在部门')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    file_content = models.FileField(upload_to='file/%Y/%m', blank=True, null=True, verbose_name='附件')



