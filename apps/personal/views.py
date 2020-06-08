import json
import re
import calendar
from datetime import date, timedelta, datetime

from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import render
from django.views.generic.base import View
from django.http import HttpResponse
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.db.models import Q

from bulletin.models import Bulletin
from users.models import UserProfile, Structure
from utils.mixin_utils import LoginRequiredMixin
from rbac.models import Menu
from system.models import SystemSetup
from .forms import ImageUploadForm, UserUpdateForm
from users.forms import AdminPasswdChangeForm
from .models import WorkOrder, BusinessApply, FeeType
from adm.models import Asset, AssetType, AssetApproveDetail, AssetInfo, FileManage
from .models import WorkOrder, BusinessApply, Advise
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
        ret['work_order_lx'] = work_order.filter(next_user_id=request.user.id, status__in=['1', '0'],
                                                 type='0').count()  # 等待我审批的
        ret['work_order_cc'] = work_order.filter(next_user_id=request.user.id, status__in=['1', '0'],
                                                 type='1').count()  # 等待我审批的
        ret['start_date'] = start_date
        # 当月个人报销统计
        busin_apply = BusinessApply.objects.filter(
            Q(cretor_id=request.user.id) |
            Q(next_user_id=request.user.id))
        ret['apply_lx'] = busin_apply.filter(next_user_id=request.user.id, status__in=['1', '0'], type='0').count()
        ret['apply_cc'] = busin_apply.filter(next_user_id=request.user.id, status__in=['1', '0'], type='1').count()
        current_user_id = request.user.id
        cashier = SpecialRole.objects.filter(title='0').first()
        if cashier:
            if current_user_id == cashier.user.id:
                ret['work_order_lx'] += WorkOrder.objects.filter(status='5', type="0").count()
                ret['work_order_cc'] += WorkOrder.objects.filter(status='5', type="1").count()
                ret['apply_lx'] += BusinessApply.objects.filter(status='5', type='0').count()
                ret['apply_cc'] += BusinessApply.objects.filter(status='5', type='1').count()
        # 物资到期提醒
        three_months = today + timedelta(days=100)
        structure = request.user.department  # 用户所在部门
        user = request.user
        if user.is_dep_administrator:
            asset = AssetInfo.objects.filter(Q(department=structure), Q(due_time__range=(today, three_months)))
            ret['asset'] = asset
            ret['asset_num'] = len(asset)
            gone_asset = AssetInfo.objects.filter(Q(department=structure), Q(due_time__lt=today))
            ret['gone_asset'] = gone_asset
            ret['gone_asset_num'] = len(gone_asset)

        # 公告相关
        bulletin = Bulletin.objects.filter(status='1')
        bulletin_amount = len(bulletin)
        ret['bulletin_amount'] = bulletin_amount
        unread_bulletin_num = request.session.get('unread_bulletin_num')
        ret['unread_bulletin_num'] = unread_bulletin_num

        # 物资相关
        user_id = request.session.get("_auth_user_id")
        asset_approve_num = len(AssetApproveDetail.objects.filter(approver_id=user_id, is_pass=None, status='1'))
        ret['asset_approve_num'] = asset_approve_num

        # 报表的时间
        mon = datetime.now().month
        year = datetime.now().year
        if mon == 1:
            mon = 12
            year -= 1
        else:
            mon -= 1

        # 个人报表 Q(create_time__month=mon), Q(create_time__year=year),
        feeid = []
        manid = UserProfile.objects.filter(name=request.user)[0].id
        post = UserProfile.objects.filter(id=manid)[0].post
        exist = WorkOrder.objects.filter(Q(create_time__month=mon), Q(create_time__year=year), Q(cretor_id=manid),
                                         ~Q(status=3), ~Q(status=0), ~Q(status=1))
        if len(exist) == 0:
            ret.update({
                'status': 0,
                'errors_info': '请提交工单在使用'
            })
        else:
            for x in exist:
                if x.feeid_id not in feeid and x.feeid_id != None:
                    feeid.append(x.feeid_id)
            if len(feeid) == 0:
                ret['status'] = 1
                ret['errors_info'] = '你的工单里还没有使用费用类型的工单'
            else:
                ret['status'] = 2
                feetype = []
                allcost = []
                perdata = []
                for x in feeid:
                    li = FeeType.objects.filter(fee_id=x)
                    if li[0].fee_type not in feetype:
                        feetype.append(li[0].fee_type)
                for x in feeid:
                    cost = 0
                    li = WorkOrder.objects.filter(Q(create_time__month=mon), Q(create_time__year=year), Q(feeid_id=x),
                                                  Q(cretor_id=manid), ~Q(status=3), ~Q(status=0), ~Q(status=1))
                    for y in li:
                        cost += float(y.cost)
                    allcost.append(cost)
                for x in range(len(allcost)):
                    dic = {}
                    dic['value'] = allcost[x]
                    dic['name'] = feetype[x]
                    perdata.append(dic)
                ret.update({
                    'feetype': feetype,
                    'perdata': perdata
                })
            print(ret)

        # 部门报表

        if len(Structure.objects.filter(adm_list=manid)) != 0:
            if int(Structure.objects.filter(adm_list=manid)[0].adm_list) == int(manid):
                struid = Structure.objects.filter(adm_list=manid)[0].id
                depeople = []
                defeeid = []
                defeetype = []
                decost = []
                dedata = []
                x = WorkOrder.objects.filter(Q(create_time__month=mon), Q(create_time__year=year), ~Q(status=3),
                                             ~Q(status=0), ~Q(status=1), Q(structure_id=struid), ~Q(feeid_id=None))
                if len(x) == 0:
                    ret['m'] = 0
                else:

                    for y in x:
                        if y.feeid_id not in defeeid:
                            defeeid.append(y.feeid_id)
                    for x in defeeid:
                        li = FeeType.objects.filter(fee_id=x)
                        if li[0].fee_type not in defeetype:
                            defeetype.append(li[0].fee_type)
                    for x in defeeid:
                        cost = 0
                        li = WorkOrder.objects.filter(Q(feeid=x), ~Q(status=3), ~Q(status=0), ~Q(status=1),
                                                      Q(structure_id=struid), ~Q(feeid_id=None))
                        for y in li:
                            cost += float(y.cost)
                        decost.append(cost)
                    for x in range(len(decost)):
                        dic = {}
                        dic['value'] = decost[x]
                        dic['name'] = defeetype[x]
                        dedata.append(dic)
                    depeo = UserProfile.objects.filter(Q(department_id=struid), ~Q(id=manid))
                    for x in depeo:
                        if x.name not in depeople:
                            depeople.append(x.name)
                    ret.update({
                        'depeople': depeople,
                        'm': 1,
                        'defeetype': defeetype,
                        'dedata': dedata
                    })

        # 全体员工的报表
        if post == '董事长' or post == '总经理':
            post = UserProfile.objects.filter(name=request.user)[0].post
            ret['post'] = post
            totalfeeid = []
            totalfeetype = []
            totalcost = []
            totaldata = []
            x = WorkOrder.objects.filter(Q(create_time__month=mon), Q(create_time__year=year), ~Q(status=3),
                                         ~Q(status=0), ~Q(status=1))
            for y in x:
                if y.feeid_id not in totalfeeid and y.feeid_id != None:
                    totalfeeid.append(y.feeid_id)
            for x in totalfeeid:
                li = FeeType.objects.filter(fee_id=x)
                if li[0].fee_type not in totalfeetype:
                    totalfeetype.append(li[0].fee_type)
            for x in totalfeeid:
                cost = 0
                li = WorkOrder.objects.filter(Q(create_time__month=mon), Q(create_time__year=year), Q(feeid=x),
                                              ~Q(status=3), ~Q(status=0), ~Q(status=1))
                for y in li:
                    cost += float(y.cost)
                totalcost.append(cost)
            for x in range(len(totalcost)):
                dic = {}
                dic['value'] = totalcost[x]
                dic['name'] = totalfeetype[x]
                totaldata.append(dic)
            ret.update({
                'totalfeetype': totalfeetype,
                'totalcost': totalcost,
                'totaldata': totaldata,

            })

        return render(request, 'personal/personal_index.html', ret)

    def post(self, request):
        mon = datetime.now().month
        year = datetime.now().year
        manid = UserProfile.objects.filter(name=request.user)[0].id
        ret = {}

        # a是月份，b是年份，c是部门,---报表函数复用
        def table(a, b, c, **d):
            feeid = []
            feetype = []
            cost = []
            data = []
            # 返回部门人员
            depeople = []
            depeo = UserProfile.objects.filter(Q(department_id=c), ~Q(id=manid), Q(is_active=1))
            for x in depeo:
                if x.name not in depeople:
                    depeople.append(x.name)
            man = []
            g = ''
            for x in depeople:
                m = '<option value="' + x + '">' + x + '</option>'
                man.append(m)
                g += m
            x = '<select name="depeo" id="depeo">' + '<option value="' + c + '"></option>' + g + '</select>'
            d['man'] = x

            exist = WorkOrder.objects.filter(~Q(status=3), ~Q(status=0), ~Q(status=1), Q(structure_id=c),
                                             Q(create_time__year=b), Q(create_time__month=a))
            if len(exist) == 0:
                d['status'] = 'fail0'
                d['errors_info'] = '该部门此时间段内没有工单'
            else:
                li = WorkOrder.objects.filter(~Q(status=3), ~Q(status=0), ~Q(status=1), Q(structure_id=c),
                                              ~Q(feeid_id=None), Q(create_time__year=b), Q(create_time__month=a))
                if len(li) == 0:
                    d['status'] = 'fail0'
                    d['errors_info'] = '此时间段内该部门工单无费用类型'
                else:
                    for x in li:
                        if x.feeid_id not in feeid:
                            feeid.append(x.feeid_id)
                    for x in feeid:
                        ll = FeeType.objects.filter(fee_id=x)
                        if ll[0].fee_type not in feetype:
                            feetype.append(ll[0].fee_type)
                    for x in feeid:
                        cos = 0
                        li = WorkOrder.objects.filter(Q(create_time__year=b), Q(create_time__month=a), ~Q(status=3),
                                                      ~Q(status=0), ~Q(status=1), Q(structure_id=c), Q(feeid_id=x))
                        for y in li:
                            cos += float(y.cost)
                        cost.append(cos)
                    for x in range(len(feeid)):
                        dic = {}
                        dic['value'] = cost[x]
                        dic['name'] = feetype[x]
                        data.append(dic)
                    d.update({
                        'feetype': feetype,
                        'data': data
                    })
            return d

        # 部门人员报表
        if request.POST.get('dep'):
            if mon != 1:
                mon -= 1
            else:
                mon = 12
                year -= 1
            dep = request.POST.get('dep')
            depfeeid = []
            depfeetype = []
            depcost = []
            depdata = []
            depid = UserProfile.objects.filter(name=dep)[0].id
            exist = WorkOrder.objects.filter(~Q(status=3), ~Q(status=0), ~Q(status=1), Q(cretor_id=depid))
            if len(exist) == 0:
                ret['status'] = 'fail0'
                ret['errors_info'] = '该人员没有工单'
            else:
                li = WorkOrder.objects.filter(Q(create_time__year=year), Q(create_time__month=mon), ~Q(status=3),
                                              ~Q(status=0), ~Q(status=1), Q(cretor_id=depid), ~Q(feeid_id=None))
                if len(li) == 0:
                    ret['status'] = 'fail1'
                    ret['errors_info'] = '该人员时间段内工单无费用类型'
                else:
                    for x in li:
                        if x.feeid_id not in depfeeid:
                            depfeeid.append(x.feeid_id)
                    for x in depfeeid:
                        ll = FeeType.objects.filter(fee_id=x)
                        if ll[0].fee_type not in depfeetype:
                            depfeetype.append(ll[0].fee_type)
                    for x in depfeeid:
                        cost = 0
                        li = WorkOrder.objects.filter(~Q(status=3), ~Q(status=0), ~Q(status=1), Q(cretor_id=depid),
                                                      Q(feeid_id=x), Q(create_time__year=year),
                                                      Q(create_time__month=mon), )
                        for y in li:
                            cost += float(y.cost)
                        depcost.append(cost)
                    for x in range(len(depfeeid)):
                        dic = {}
                        dic['value'] = depcost[x]
                        dic['name'] = depfeetype[x]
                        depdata.append(dic)
                    ret.update({
                        'depfeetype': depfeetype,
                        'depdata': depdata
                    })

        # 部门人员时间段报表
        if request.POST.get('dep') and request.POST.get("start_time1") and request.POST.get("end_time1"):
            ret.clear()
            start_time = request.POST.get("start_time1")
            end_time = request.POST.get("end_time1")
            paradep = request.POST.get('dep')
            paradepid = UserProfile.objects.filter(name=paradep)[0].id
            paradepfeeid = []
            paradepfeetype = []
            paradepcost = []
            paradepdata = []
            exist = WorkOrder.objects.filter(Q(create_time__range=(start_time, end_time)), Q(cretor_id=paradepid),
                                             ~Q(status=3), ~Q(status=0), ~Q(status=1))
            if len(exist) == 0:
                ret['status'] = 'fail0'
                ret['errors_info'] = '该人员在此时间段内无工单提交'
            else:
                for x in exist:
                    if x.feeid_id not in paradepfeeid and x.feeid_id != None:
                        paradepfeeid.append(x.feeid_id)
                if len(paradepfeeid) == 0:
                    ret['status'] = 'fail1'
                    ret['errors_info'] = '该时间段内没有使用费用类型'
                else:
                    for x in paradepfeeid:
                        li = FeeType.objects.filter(fee_id=x)
                        if li[0].fee_type not in paradepfeetype:
                            paradepfeetype.append(li[0].fee_type)
                    for x in paradepfeeid:
                        cost = 0
                        li = WorkOrder.objects.filter(Q(create_time__range=(start_time, end_time)), Q(feeid=x),
                                                      Q(cretor_id=paradepid), ~Q(status=3), ~Q(status=0), ~Q(status=1))
                        for y in li:
                            cost += float(y.cost)
                        paradepcost.append(cost)
                    for x in range(len(paradepcost)):
                        dic = {}
                        dic['value'] = paradepcost[x]
                        dic['name'] = paradepfeetype[x]
                        paradepdata.append(dic)
                    ret.update({
                        'paradepdata': paradepdata,
                        'paradepfeetype': paradepfeetype
                    })

        # 董事长报表中部门人员时间段报表
        if request.POST.get('depeo') and request.POST.get("dep_start") and request.POST.get("dep_end"):
            start_time = request.POST.get("dep_start")
            end_time = request.POST.get("dep_end")
            dep = request.POST.get('depeo')
            managefeeid = []
            managefeetype = []
            managecost = []
            managedata = []
            if dep.isdigit() == True:
                exist = WorkOrder.objects.filter(Q(create_time__range=(start_time, end_time)), Q(structure_id=dep),
                                                 ~Q(status=3), ~Q(status=0), ~Q(status=1))
                if len(exist) == 0:
                    ret['status'] = 'fail0'
                    ret['errors_info'] = '该部门在此时间段内无工单提交'
                else:
                    for x in exist:
                        if x.feeid_id not in managefeeid and x.feeid_id != None:
                            managefeeid.append(x.feeid_id)
                    if len(managefeeid) == 0:
                        ret['status'] = 'fail1'
                        ret['errors_info'] = '该时间段内没有使用费用类型'
                    else:
                        for x in managefeeid:
                            li = FeeType.objects.filter(fee_id=x)
                            if li[0].fee_type not in managefeetype:
                                managefeetype.append(li[0].fee_type)
                        for x in managefeeid:
                            cost = 0
                            li = WorkOrder.objects.filter(Q(create_time__range=(start_time, end_time)), Q(feeid=x),
                                                          Q(structure_id=dep), ~Q(status=3), ~Q(status=0), ~Q(status=1))
                            for y in li:
                                cost += float(y.cost)
                            managecost.append(cost)
                        for x in range(len(managecost)):
                            dic = {}
                            dic['value'] = managecost[x]
                            dic['name'] = managefeetype[x]
                            managedata.append(dic)
                        ret.update({
                            'managedata': managedata,
                            'managefeetype': managefeetype
                        })
            else:
                manageid = UserProfile.objects.filter(name=dep)[0].id
                exist = WorkOrder.objects.filter(Q(create_time__range=(start_time, end_time)), Q(cretor_id=manageid),
                                                 ~Q(status=3), ~Q(status=0), ~Q(status=1))
                if len(exist) == 0:
                    ret['status'] = 'fail0'
                    ret['errors_info'] = '该人员在此时间段内无工单提交'
                else:
                    for x in exist:
                        if x.feeid_id not in managefeeid and x.feeid_id != None:
                            managefeeid.append(x.feeid_id)
                    if len(managefeeid) == 0:
                        ret['status'] = 'fail1'
                        ret['errors_info'] = '该时间段内没有使用费用类型'
                    else:
                        for x in managefeeid:
                            li = FeeType.objects.filter(fee_id=x)
                            if li[0].fee_type not in managefeetype:
                                managefeetype.append(li[0].fee_type)
                        for x in managefeeid:
                            cost = 0
                            li = WorkOrder.objects.filter(Q(create_time__range=(start_time, end_time)), Q(feeid=x),
                                                          Q(cretor_id=manageid), ~Q(status=3), ~Q(status=0),
                                                          ~Q(status=1))
                            for y in li:
                                cost += float(y.cost)
                            managecost.append(cost)
                        for x in range(len(managecost)):
                            dic = {}
                            dic['value'] = managecost[x]
                            dic['name'] = managefeetype[x]
                            managedata.append(dic)
                        ret.update({
                            'managedata': managedata,
                            'managefeetype': managefeetype
                        })

        # 营销中心
        if request.POST.get('saleCenter'):
            if mon != 1:
                mon -= 1
            else:
                mon = 12
                year -= 1
            sc = request.POST.get('saleCenter')
            ret = table(mon, year, sc, **ret)

        # 大数据事业部
        if request.POST.get('BigData'):
            if mon != 1:
                mon -= 1
            else:
                mon = 12
                year -= 1
            bg = request.POST.get('BigData')
            ret = table(mon, year, bg, **ret)

        # 生产中心
        if request.POST.get('production'):
            if mon != 1:
                mon -= 1
            else:
                mon = 12
                year -= 1
            pr = request.POST.get('production')
            ret = table(mon, year, pr, **ret)

        # 人事行政中心
        if request.POST.get('personal'):
            if mon != 1:
                mon -= 1
            else:
                mon = 12
                year -= 1
            pe = request.POST.get('personal')
            ret = table(mon, year, pe, **ret)

        # 运维中心
        if request.POST.get('ops'):
            if mon != 1:
                mon -= 1
            else:
                mon = 12
                year -= 1
            op = request.POST.get('ops')
            ret = table(mon, year, op, **ret)

        # 证券事务中心 Securities affairs centre
        if request.POST.get('SAC'):
            if mon != 1:
                mon -= 1
            else:
                mon = 12
                year -= 1
            sa = request.POST.get('SAC')
            ret = table(mon, year, sa, **ret)

        # 财务部
        if request.POST.get('finance'):
            if mon != 1:
                mon -= 1
            else:
                mon = 12
                year -= 1
            fi = request.POST.get('finance')
            ret = table(mon, year, fi, **ret)

        # 售后服务
        if request.POST.get('afterSale'):
            if mon != 1:
                mon -= 1
            else:
                mon = 12
                year -= 1
            af = request.POST.get('afterSale')
            ret = table(mon, year, af, **ret)

        # 物资管理
        if request.POST.get('materials'):
            if mon != 1:
                mon -= 1
            else:
                mon = 12
                year -= 1
            mm = request.POST.get('materials')
            ret = table(mon, year, mm, **ret)

        # 通信工程
        if request.POST.get('communication'):
            if mon != 1:
                mon -= 1
            else:
                mon = 12
                year -= 1
            co = request.POST.get('communication')
            ret = table(mon, year, co, **ret)

        # 电力工程
        if request.POST.get('electric'):
            if mon != 1:
                mon -= 1
            else:
                mon = 12
                year -= 1
            epp = request.POST.get('electric')
            ret = table(mon, year, epp, **ret)

        # 时间段搜索工单
        if request.POST.get("start_time") and request.POST.get("end_time"):
            parafeeid = []  # para是段落的前四个字母,表示时间段内的费用id
            parafeetype = []
            paraallcost = []
            paradata = []
            start_time = request.POST.get("start_time")
            end_time = request.POST.get("end_time")
            exist = WorkOrder.objects.filter(Q(create_time__range=(start_time, end_time)), Q(cretor_id=manid),
                                             ~Q(status=3), ~Q(status=0), ~Q(status=1))
            if len(exist) == 0:
                ret['status'] = 'fail0'
                ret['errors_info'] = '请提交工单使用'
            else:
                for x in exist:
                    if x.feeid_id not in parafeeid and x.feeid_id != None:
                        parafeeid.append(x.feeid_id)
                if len(parafeeid) == 0:
                    ret['status'] = 'fail1'
                    ret['errors_info'] = '该时间段内没有使用费用类型'
                else:
                    for x in parafeeid:
                        li = FeeType.objects.filter(fee_id=x)
                        if li[0].fee_type not in parafeetype:
                            parafeetype.append(li[0].fee_type)
                    for x in parafeeid:
                        cost = 0
                        li = WorkOrder.objects.filter(Q(create_time__range=(start_time, end_time)), Q(feeid=x),
                                                      Q(cretor_id=manid), ~Q(status=3), ~Q(status=0), ~Q(status=1))
                        for y in li:
                            cost += float(y.cost)
                        paraallcost.append(cost)
                    for x in range(len(paraallcost)):
                        dic = {}
                        dic['value'] = paraallcost[x]
                        dic['name'] = parafeetype[x]
                        paradata.append(dic)
                    ret.update({
                        'paradata': paradata,
                        'parafeetype': parafeetype
                    })
        return HttpResponse(json.dumps(ret), content_type='application/json')


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


class ChangeStatement(LoginRequiredMixin, View):
    """
    修改岗位职责
    """

    def get(self, request):
        ret = dict()
        user_id = request.session.get("_auth_user_id")
        user = User.objects.filter(id=user_id).first()
        ret["user"] = user
        return render(request, "personal/userinfo/create_statement.html", ret)

    def post(self, request):
        ret = dict()
        personal_statement = request.POST.get("detail")
        user_id = request.session.get("_auth_user_id")
        user = User.objects.filter(id=user_id).first()
        user.personal_statement = personal_statement
        user.save()
        ret["status"] = "1"
        return HttpResponse(json.dumps(ret), content_type='application/json')


class ShowStatement(LoginRequiredMixin, View):
    """
    展示个人职责
    """

    def get(self, request):
        ret = dict()
        id0 = request.GET.get("id")
        user = User.objects.get(id=id0)
        ret["user"] = user
        return render(request, "personal/phonebook/show_statement.html", ret)


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
    """
    个人中心
    """

    def get(self, request):
        fields = ['id', 'name', 'mobile', 'email', 'post', 'department__title', 'image', 'personal_statement']
        ret = dict(linkmans=list(User.objects.exclude(username='admin').filter(is_active=1).values(*fields)))
        return render(request, 'personal/phonebook/phonebook.html', ret)


class Direction(View):

    def get(self, request):
        return render(request, 'direction0.html')

    def post(self, request):
        ret = dict()
        advise = Advise()
        advise.creator = request.user
        ret_data = json.loads(request.body.decode())
        advise.back = ret_data["advise"]

        advise.create_time = datetime.now().year
        advise.save()
        return HttpResponse(json.dumps(ret), content_type='application/json')


class Catalog(View):
    """
    档案管理目录
    """
    def get(self, request):
        ret = dict()
        return render(request, 'adm/asset/file_list.html', ret)

    def post(self, request):
        fields = ['id', 'name', 'upload_time', 'content', 'number', 'preserve_dep__title', 'type__id', 'type__name']
        ret = dict(data=list(FileManage.objects.values(*fields).filter(is_delete=False).order_by("-upload_time")))
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type="application/json")


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
            asset = AssetInfo.objects.filter(Q(department=structure), Q(due_time__range=(today, three_months)))
            for a in asset:
                if len(a.name) > 10:
                    a.name = a.name[:10] + "..."
                if len(a.remark) > 20:
                    a.remark = a.remark[:20] + "..."
            ret['asset'] = asset
            ret['asset_num'] = len(asset)
        elif type0 == '1':
            asset = AssetInfo.objects.filter(Q(department=structure), Q(due_time__lt=today))
            for a in asset:
                if len(a.name) > 10:
                    a.name = a.name[:10] + "..."
                if len(a.remark) > 20:
                    a.remark = a.remark[:20] + "..."
            ret['asset'] = asset
            ret['asset_num'] = len(asset)
        return render(request, "adm/asset/due_asset.html", ret)


class FeedbackView(LoginRequiredMixin, View):
    """
    意见反馈
    """

    def get(self, request):
        ret = dict()
        # 判断是否为程序员
        user_id = request.session.get("_auth_user_id")
        user = User.objects.filter(id=user_id).first()
        department = Structure.objects.filter(title="研发中心").first()
        if department:
            if user.department_id == department.id:
                ret["is_op"] = "1"
        return render(request, "personal/feedback_list.html", ret)

    def post(self, request):
        fields = ['id', 'back', 'create_time', 'status', 'remark', 'operator__name', 'creator__name']
        user_id = request.session.get("_auth_user_id")
        user = User.objects.filter(id=user_id).first()
        department = Structure.objects.filter(title="研发中心").first()
        if department:
            if user.department_id == department.id:
                ret = dict(data=list(Advise.objects.all().values(*fields).order_by("-id")))
            else:
                ret = dict(data=list(Advise.objects.filter(creator_id=user_id).values(*fields).order_by("-id")))
        else:
            ret = dict(data=list(Advise.objects.filter(creator_id=user_id).values(*fields).order_by("-id")))
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type='application/json')


class CreateFeedback(LoginRequiredMixin, View):
    """
    创建意见反馈
    """

    def get(self, request):
        ret = dict()
        id0 = request.GET.get("id", None)
        if id0:
            advise = Advise.objects.filter(id=id0).first()
            ret["advice"] = advise
        return render(request, "feedback.html", ret)

    def post(self, request):
        ret = dict()
        back = request.POST.get("advise")
        id0 = request.POST.get("advise_id")
        user_id = request.session.get("_auth_user_id")
        if id0:
            advise = Advise.objects.filter(id=id0).first()
        else:
            advise = Advise()
        advise.creator_id = user_id
        advise.back = back
        advise.save()
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type='application/json')


class FeedbackDelete(LoginRequiredMixin, View):
    """
    删除意见反馈
    """

    def post(self, request):
        ret = dict()
        id0 = request.POST.get("id")
        advise = Advise.objects.filter(id=id0).first()
        advise.delete()
        ret["result"] = True
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type='application/json')


class FeedbackAjax(LoginRequiredMixin, View):
    """
    意见反馈ajax
    """

    def get(self, request):
        ret = dict()
        id0 = request.GET.get("id")
        user_id = request.session.get("_auth_user_id")
        advise = Advise.objects.filter(id=id0).first()
        advise.status = "1"
        advise.operator_id = user_id
        advise.save()
        ret["result"] = True
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type='application/json')


class FeedbackRemark(LoginRequiredMixin, View):
    """
    意见反馈备注
    """
    def get(self, request):
        ret = dict()
        id0 = request.GET.get("id")
        ps = request.GET.get("ps")
        ret["id"] = id0
        ret["ps"] = ps
        return render(request, "personal/feedback_remark.html", ret)

    def post(self, request):
        ret = dict()
        user_id = request.session.get("_auth_user_id")
        id0 = request.POST.get("id")
        ps = request.POST.get("ps")
        content = request.POST.get("content")
        advise = Advise.objects.filter(id=id0).first()
        if ps == "0":
            advise.status = "2"
        if ps == "1":
            advise.status = "3"
        advise.remark = content
        advise.operator_id = user_id
        advise.save()
        ret["success"] = True
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type='application/json')


class ShowCatalog(View):
    """
    首页档案管理目录
    """
    def get(self, request):
        ret = dict()
        return render(request, 'adm/asset/file_show_list.html', ret)

    def post(self, request):
        fields = ['id', 'name', 'upload_time', 'content', 'number', 'preserve_dep__title', 'type__id', 'type__name']
        ret = dict(data=list(FileManage.objects.values(*fields).filter(Q(is_delete=False), ~Q(type_id=None)).order_by("-upload_time")))
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type="application/json")
