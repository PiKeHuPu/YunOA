import json
import re
import calendar
from datetime import date, timedelta

from django.shortcuts import render
from django.views.generic.base import View
from django.http import HttpResponse
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.db.models import Q

from bulletin.models import Bulletin
from utils.mixin_utils import LoginRequiredMixin
from rbac.models import Menu
from system.models import SystemSetup
from .forms import ImageUploadForm, UserUpdateForm
from users.forms import AdminPasswdChangeForm
from .models import WorkOrder, BusinessApply
from adm.models import Asset, AssetType
from rbac.models import Role, SpecialRole

from utils.toolkit import get_month_work_order_count, get_year_work_order_count

User = get_user_model()


class PersonalView(LoginRequiredMixin, View):
    """
    我的工作台
    """

    def get(self, request):
        ret = Menu.getMenuByRequestUrl(url=request.path_info)
        ret.update(SystemSetup.getSystemSetupLastData())
        # 审批内容
        today = date.today()
        # 原计划按时间长度搜索，现在不用了。呵呵
        start_date = today.replace(day=1)
        _, days_in_month = calendar.monthrange(start_date.year, start_date.month)
        end_date = start_date + timedelta(days=days_in_month)
        #  (('0', '审批提交'), ('1', '审批中'), ('2', '审批完成'), ('3', '审批被退回'))
        # 当月个人立项统计
        work_order = WorkOrder.objects.filter(
                                              Q(cretor_id=request.user.id) |
                                              Q(next_user_id=request.user.id)
                                              )
        ret['work_order_lx'] = work_order.filter(next_user_id=request.user.id, status__in = ['1', '0'], type='0').count()  # 等待我审批的
        ret['work_order_cc'] = work_order.filter(next_user_id=request.user.id, status__in = ['1', '0'], type='1').count()  # 等待我审批的
        ret['start_date'] = start_date
        # 当月个人报销统计
        busin_apply = BusinessApply.objects.filter(
                                                   Q(cretor_id=request.user.id) |
                                                   Q(next_user_id=request.user.id))
        ret['apply_lx'] = busin_apply.filter(next_user_id=request.user.id, status__in = ['1', '0'], type='0').count()
        ret['apply_cc'] = busin_apply.filter(next_user_id=request.user.id, status__in = ['1', '0'], type='1').count()
        current_user_id = request.user.id
        cashier = SpecialRole.objects.filter(title='0').first()
        if cashier:
            if current_user_id == cashier.user.id:
                ret['work_order_x'] += WorkOrder.objects.filter(status='5').count()
                ret['apply_x'] += BusinessApply.objects.filter(status='5').count()
        # 物资到期提醒
        three_months = today + timedelta(days=100)
        structure = request.user.department    # 用户所在部门
        asset = Asset.objects.filter(Q(dueremind = '1'), Q(assetType__structure=structure), Q(dueDate__range=(today, three_months)))
        ret['asset'] = asset
        ret['asset_num'] = len(asset)
        gone_asset = Asset.objects.filter(Q(dueremind='1'), Q(assetType__structure=structure), Q(dueDate__lt=today))
        ret['gone_asset'] = gone_asset
        ret['gone_asset_num'] = len(gone_asset)

        # 公告相关
        bulletin = Bulletin.objects.filter(status='1')
        bulletin_amount = len(bulletin)
        ret['bulletin_amount'] = bulletin_amount
        unread_bulletin_num = request.session.get('unread_bulletin_num')
        ret['unread_bulletin_num'] = unread_bulletin_num
        return render(request, 'personal/personal_index.html', ret)


class UserInfoView(LoginRequiredMixin, View):
    """
    个人中心：个人信息查看修改和修改
    """

    def get(self, request):
        return render(request, 'personal/userinfo/user_info.html')

    def post(self, request):
        ret = dict()
        user_id = request.POST.get("id")
        user = User.objects.get(id=user_id)
        user.name = request.POST.get("name")
        user.gender = request.POST.get("gender")
        if request.POST.get("birthday"):
            user.birthday = request.POST.get("birthday")
        else:
            user.birthday = None
        user.username = request.POST.get("username")
        user.mobile = request.POST.get("mobile")
        user.email = request.POST.get("email")
        user.bank_card = request.POST.get("bank_card")
        user.bank_name = request.POST.get("bank_name")
        user.bank_user_name = request.POST.get("bank_user_name")
        user.save()
        ret["status"] = "success"
        return HttpResponse(json.dumps(ret), content_type='application/json')


class UploadImageView(LoginRequiredMixin, View):
    """
    个人中心：上传头像
        """

    def post(self, request):
        ret = dict(result=False)
        image_form = ImageUploadForm(request.POST, request.FILES, instance=request.user)
        if image_form.is_valid():
            image_form.save()
            ret['result'] = True
        return HttpResponse(json.dumps(ret), content_type='application/json')


class PasswdChangeView(LoginRequiredMixin, View):
    """
    登陆用户修改个人密码
    """

    def get(self, request):
        ret = dict()
        user = get_object_or_404(User, pk=int(request.user.id))
        ret['user'] = user
        return render(request, 'personal/userinfo/passwd-change.html', ret)

    def post(self, request):

        user = get_object_or_404(User, pk=int(request.user.id))
        form = AdminPasswdChangeForm(request.POST)
        if form.is_valid():
            new_password = request.POST.get('password')
            user.set_password(new_password)
            user.save()
            ret = {'status': 'success'}
        else:
            pattern = '<li>.*?<ul class=.*?><li>(.*?)</li>'
            errors = str(form.errors)
            admin_passwd_change_form_errors = re.findall(pattern, errors)
            ret = {
                'status': 'fail',
                'admin_passwd_change_form_errors': admin_passwd_change_form_errors[0]
            }
        return HttpResponse(json.dumps(ret), content_type='application/json')


class PhoneBookView(LoginRequiredMixin, View):
    def get(self, request):
        fields = ['name', 'mobile', 'email', 'post', 'department__title', 'image']
        ret = dict(linkmans=list(User.objects.exclude(username='admin').filter(is_active=1).values(*fields)))
        return render(request, 'personal/phonebook/phonebook.html', ret)


class Direction(View):
    def get(self, request):
        return render(request, 'direction.html')


class DueAssetView(LoginRequiredMixin, View):
    """
    物资续期提醒页面
    """
    def get(self, request):
        ret = dict()
        # 物资到期提醒
        today = date.today()
        three_months = today + timedelta(days=100)
        structure = request.user.department  # 用户所在部门

        type0 = request.GET.get("type")

        if type0 == '0':
            asset = Asset.objects.filter(Q(dueremind='1'), Q(assetType__structure=structure),
                                         Q(dueDate__range=(today, three_months)))
            for a in asset:
                if len(a.brand) > 10:
                    a.brand = a.brand[:10] + "..."
                if len(a.desc) > 20:
                    a.desc = a.desc[:20] + "..."
            ret['asset'] = asset
            ret['asset_num'] = len(asset)
        elif type0 == '1':
            asset = Asset.objects.filter(Q(dueremind='1'), Q(assetType__structure=structure), Q(dueDate__lt=today))
            for a in asset:
                if len(a.brand) > 10:
                    a.brand = a.brand[:10] + "..."
                if len(a.desc) > 20:
                    a.desc = a.desc[:20] + "..."
            ret['asset'] = asset
            ret['asset_num'] = len(asset)
        return render(request, "adm/asset/due_asset.html", ret)
