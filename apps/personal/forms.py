# @Time   : 2018/5/6 17:22
# @Author : RobbieHan
# @File   : forms.py


from django import forms
from django.contrib.auth import get_user_model

from .models import WorkOrder, WorkOrderRecord, WorkOrderFlow, BusinessApply

User = get_user_model()


class ImageUploadForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['image']


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['name', 'gender', 'birthday', 'email', 'mobile', 'username', 'bank_card', 'bank_name', 'bank_user_name']

    def clean(self):
        cleaned_data = super(UserUpdateForm, self).clean()
        mobile = cleaned_data.get("mobile")
        email = cleaned_data.get("email")
        username = cleaned_data.get("username")
        if self.instance.mobile != mobile:
            if User.objects.filter(mobile=mobile).count():
                raise forms.ValidationError("手机号码已被其他用户使用")
        elif self.instance.email != email:
            if User.objects.filter(email=email).count():
                raise forms.ValidationError("邮箱已被其他用户使用")


class WorkOrderCreateForm(forms.ModelForm):
    # 新建审批表
    class Meta:
        model = WorkOrder
        fields = '__all__'
        error_messages = {
            "title": {"required": "请输入标题"},
            "type": {"required": "请选择类型"},
            "start_time": {"required": "请输入开始时间"},
            "end_time": {"required": "请输入结束时间"},
            "content": {"required": "请输入详情内容"},
        }

    def clean(self):
        cleaned_data = super(WorkOrderCreateForm, self).clean()
        number = cleaned_data.get("number")
        if WorkOrder.objects.filter(number=number).count():
            raise forms.ValidationError("编号已存在")


class WorkOrderUpdateForm(forms.ModelForm):
    class Meta:
        model = WorkOrder
        fields = '__all__'
        error_messages = {
            "title": {"required": "请输入工单标题"},
            "type": {"required": "请选择工单类型"},
            "status": {"required": "请选择工单状态"},
            "do_time": {"required": "请输入工单安排时间"},
            "content": {"required": "请输入工单内容"},
            "customer": {"required": "请选客户信息"},
        }

    def clean(self):
        cleaned_data = super(WorkOrderUpdateForm, self).clean()
        approver = cleaned_data.get("approver", "")
        if not approver:
            raise forms.ValidationError("请选择工单审批人")


class WorkOrderRecordForm(forms.ModelForm):
    # class Meta:
    #     model = WorkOrderRecord
    #     exclude = ['file_content', ]
    pass

class WorkOrderRecordUploadForm(forms.ModelForm):
    # class Meta:
    #     model = WorkOrderRecord
    #     fields = ['file_content']
    pass

class WorkOrderProjectUploadForm(forms.ModelForm):
    class Meta:
        model = WorkOrder
        fields = ['file_content']

class APProjectUploadForm(forms.ModelForm):
    class Meta:
        model = BusinessApply
        fields = ['file_content']

#
# class WorkOrderFlowForm(forms.ModelForm):
#     class Meta:
#         model = WorkOrderFlow
#         fields = ['structure', 'process', 'factor_type', 'factor', 'carbon', 'order_type']