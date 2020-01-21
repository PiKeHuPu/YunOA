#!/user/bin/env python
# -*- coding:utf-8 -*-
'''
@author  : Evan
@desc    :  数据类型常量
'''

CHOICES = {
    #  审批类
    'WorkOrder_type': (('0', '立项审批'), ('1', '出差审批')),  # 审批类型
    'WorkOrder_type0': (('0', '立项'), ('1', '出差')),  # 审批类型
    'WorkOrder_pro_type': (('0', '立项'), ('1', '报销')),  # 审批类型
    'WorkOrderLog_record_type': (('0', '同意'), ('1', '不同意')),  # 审批意见
    'WorkOrderLog_type': (('0', '申请'), ('1', '报销')),  # 审批日志类型
    'WorlOrder_status': (('0', '等待审批'), ('1', '审批中'), ('2', '审批完成'), ('3', '审批被退回'), ('4', '预付款完成'), ('5','等待预付款'), ('6', '报销完成'), ('7', '取消预付款'), ('8', '报销中')),  # 审批状态 0：可以修改，1：不能修改
    'Apply_status': (('-1', '可以申请'), ('0', '等待审批'), ('1', '审批中'), ('2', '审批完成'), ('3', '审批被退回'), ('4', '报销完成'), ('5','等待付款')),  # 审批状态 0：可以修改，1：不能修改
    'WorkOrder_factor_type': (('0', '时间'), ('1', '金额')),  # 审批条件类型
    'invoice_choices': (('0', '增值税普通发票'), ('1', '增值税专用发票'), ('3', '手撕票')),  # 发票类型
    'advance_choices': (('0', '预支'), ('1', '未预支')),  #
    'transport_choices': (('0', '自己开车'), ('1', '大巴'), ('2', '火车'), ('3', '动车'), ('4', '飞机'), ('5', '轮船')),  # 交通工具
    'advance_choices': (('0', '不预支'), ('1', '预支')),  # 预支
    'payment_choices': (('0', '没完成预支'), ('1', '完成预支')),  # 预支

    # 领取物资
    'Party_type': (('0', '自用'), ('1', '外包方使用')),
    'Asset_give': (('0', '没有归还'), ('1', '归还')),

    # 公告分类
    'bulletin_type': (('0', '规章制度'), ('1', '公告')),
    'bulletin_status': (('0', '停用'), ('1', '启用'))
}

SPECIAL_CHOICES = {
    # 特殊角色类
    'special_role': (('0', '出纳'), ('1', '财务总监'),)
}


def to_list(dic):
    ret = []
    for i in dic:
        type_dict = dict(item=i[0], value=i[1])
        ret.append(type_dict)
    return ret

def to_dict(dic):
    ret = {}
    for i in dic:
        ret[i[0]] = i[1]
    return ret

