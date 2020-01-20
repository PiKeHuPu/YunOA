import json
import re
import calendar
from datetime import date, timedelta, datetime

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
from adm.models import Asset, AssetType, AssetApproveDetail, AssetInfo
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
        ret['work_order_lx'] = work_order.filter(next_user_id=request.user.id, status__in=['1', '0'], type='0').count()  # 等待我审批的
        ret['work_order_cc'] = work_order.filter(next_user_id=request.user.id, status__in=['1', '0'], type='1').count()  # 等待我审批的
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
        structure = request.user.department    # 用户所在部门
        if structure.administrator_id == current_user_id:
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
        asset_approve_num = len(AssetApproveDetail.objects.filter(approver_id=user_id, is_pass=None))
        ret['asset_approve_num'] = asset_approve_num

        #个人报表
        feeid = []
        manid = UserProfile.objects.filter(name=request.user)[0].id
        exist = WorkOrder.objects.filter(Q(cretor_id=manid), ~Q(status=3),  ~Q(status=0), ~Q(status=1))
        if len(exist) == 0:
            ret.update({
                'status': 0,
                'errors_info': '请提交工单在使用'
            })
        else:
            for x in exist:
                if x.feeid_id not in feeid and x.feeid_id !=None:
                    feeid.append(x.feeid_id)
            if len(feeid) == 0:
                ret['status'] = 1
                ret['errors_info'] = '你的工单里还没有使用费用类型的工单'
            else:
                ret['status'] = 555
                ret['errors_info'] = '没事了'
                feetype = []
                allcost = []
                for x in feeid:
                    li = FeeType.objects.filter(fee_id=x)
                    if li[0].fee_type not in feetype:
                        feetype.append(li[0].fee_type)
                for x in feeid:
                    cost = 0
                    li = WorkOrder.objects.filter(Q(feeid_id=x), Q(cretor_id=manid), ~Q(status=3), ~Q(status=0), ~Q(status=1))
                    for y in li:
                        cost += float(y.cost)
                    allcost.append(cost)
                perdata = []
                for x in range(len(allcost)):
                    dic = {}
                    dic['value'] = allcost[x]
                    dic['name'] = feetype[x]
                    perdata.append(dic)
                ret.update({
                    'feetype': feetype,
                    'perdata': perdata
                })
        #全体员工的报表
        post = UserProfile.objects.filter(name=request.user)[0].post
        ret['post'] = post
        totalfeeid = []
        totalfeetype = []
        totalcost = []
        totaldata = []
        x = WorkOrder.objects.filter(~Q(status=3), ~Q(status=0), ~Q(status=1))
        for y in x:
            if y.feeid_id not in totalfeeid and y.feeid_id != None:
                totalfeeid.append(y.feeid_id)
        for x in totalfeeid:
            li = FeeType.objects.filter(fee_id=x)
            if li[0].fee_type not in totalfeetype:
                totalfeetype.append(li[0].fee_type)
        for x in totalfeeid:
            cost = 0
            li = WorkOrder.objects.filter(Q(feeid=x), ~Q(status=3), ~Q(status=0), ~Q(status=1))
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
            'totaldata': totaldata,

        })
        return render(request, 'personal/personal_index.html', ret)

    def post(self, request):
        mon = datetime.now().month
        year = datetime.now().year
        manid = UserProfile.objects.filter(name=request.user)[0].id
        ret = {}
        #营销中心
        if request.POST.get('saleCenter'):
            sc = request.POST.get('saleCenter')
            scfeeid = []
            scfeetype = []
            sccost = []
            scdata = []
            exist = WorkOrder.objects.filter(~Q(status=3), ~Q(status=0), ~Q(status=1), Q(structure_id=sc))
            if len(exist) == 0:
                ret['status'] = 'fail0'
                ret['errors_info'] = '该部门没有工单'
            else:
                li = WorkOrder.objects.filter(~Q(status=3), ~Q(status=0), ~Q(status=1), Q(structure_id=sc), ~Q(feeid_id=None))
                if len(li) == 0:
                    ret['status'] = 'fail0'
                    ret['errors_info'] = '该部门工单无费用类型'
                else:
                    for x in li:
                        if x.feeid_id not in scfeeid:
                            scfeeid.append(x.feeid_id)
                    for x in scfeeid:
                        ll = FeeType.objects.filter(fee_id=x)
                        if ll[0].fee_type not in scfeetype:
                            scfeetype.append(ll[0].fee_type)
                    for x in scfeeid:
                        cost = 0
                        li = WorkOrder.objects.filter(~Q(status=3), ~Q(status=0), ~Q(status=1), Q(structure_id=sc), Q(feeid_id=x))
                        for y in li:
                            cost += float(y.cost)
                        sccost.append(cost)
                    for x in range(len(scfeeid)):
                        dic = {}
                        dic['value'] = sccost[x]
                        dic['name'] = scfeetype[x]
                        scdata.append(dic)
                    ret.update({
                        'scfeetype': scfeetype,
                        'scdata': scdata
                    })
        #大数据事业部
        if request.POST.get('BigData'):
            bg = request.POST.get('BigData')
            bgfeeid = []
            bgfeetype = []
            bgcost = []
            bgdata = []
            exist = WorkOrder.objects.filter(~Q(status=3), ~Q(status=0), ~Q(status=1), Q(structure_id=bg))
            if len(exist) == 0:
                ret['status'] = 'fail0'
                ret['errors_info'] = '该部门没有工单'
            else:
                li = WorkOrder.objects.filter(~Q(status=3), ~Q(status=0), ~Q(status=1), Q(structure_id=bg), ~Q(feeid_id=None))
                if len(li) == 0:
                    ret['status'] = 'fail0'
                    ret['errors_info'] = '该部门工单无费用类型'
                else:
                    for x in li:
                        if x.feeid_id not in bgfeeid:
                            bgfeeid.append(x.feeid_id)
                    for x in bgfeeid:
                        ll = FeeType.objects.filter(fee_id=x)
                        if ll[0].fee_type not in bgfeetype:
                            bgfeetype.append(ll[0].fee_type)
                    for x in bgfeeid:
                        cost = 0
                        li = WorkOrder.objects.filter(~Q(status=3), ~Q(status=0), ~Q(status=1), Q(structure_id=bg), Q(feeid_id=x))
                        for y in li:
                            cost += float(y.cost)
                        bgcost.append(cost)
                    for x in range(len(bgfeeid)):
                        dic = {}
                        dic['value'] = bgcost[x]
                        dic['name'] = bgfeetype[x]
                        bgdata.append(dic)
                    ret.update({
                        'bgfeetype': bgfeetype,
                        'bgdata': bgdata
                    })
        #生产中心
        if request.POST.get('production'):
            pr = request.POST.get('production')
            prfeeid = []
            prfeetype = []
            prcost = []
            prdata = []
            print(pr)
            exist = WorkOrder.objects.filter(~Q(status=3), ~Q(status=0), ~Q(status=1), Q(structure_id=pr))
            if len(exist) == 0:
                ret['status'] = 'fail0'
                ret['errors_info'] = '该部门没有工单'
            else:
                li = WorkOrder.objects.filter(~Q(status=3), ~Q(status=0), ~Q(status=1), Q(structure_id=pr), ~Q(feeid_id=None))
                if len(li) == 0:
                    ret['status'] = 'fail0'
                    ret['errors_info'] = '该部门工单无费用类型'
                else:
                    for x in li:
                        if x.feeid_id not in prfeeid:
                            prfeeid.append(x.feeid_id)
                    for x in prfeeid:
                        ll = FeeType.objects.filter(fee_id=x)
                        if ll[0].fee_type not in prfeetype:
                            prfeetype.append(ll[0].fee_type)
                    for x in prfeeid:
                        cost = 0
                        li = WorkOrder.objects.filter(~Q(status=3), ~Q(status=0), ~Q(status=1), Q(structure_id=pr), Q(feeid_id=x))
                        for y in li:
                            cost += float(y.cost)
                        prcost.append(cost)
                    for x in range(len(prfeeid)):
                        dic = {}
                        dic['value'] = prcost[x]
                        dic['name'] = prfeetype[x]
                        prdata.append(dic)

                    ret.update({
                        'prfeetype': prfeetype,
                        'prdata': prdata
                    })
        #人事行政中心
        if request.POST.get('personal'):
            pe = request.POST.get('personal')
            pefeeid = []
            pefeetype = []
            pecost = []
            pedata = []
            exist = WorkOrder.objects.filter(~Q(status=3), ~Q(status=0), ~Q(status=1), Q(structure_id=pe))
            if len(exist) == 0:
                ret['status'] = 'fail0'
                ret['errors_info'] = '该部门没有工单'
            else:
                li = WorkOrder.objects.filter(~Q(status=3), ~Q(status=0), ~Q(status=1), Q(structure_id=pe),
                                              ~Q(feeid_id=None))
                if len(li) == 0:
                    ret['status'] = 'fail0'
                    ret['errors_info'] = '该部门工单无费用类型'
                else:
                    for x in li:
                        if x.feeid_id not in pefeeid:
                            pefeeid.append(x.feeid_id)
                    for x in pefeeid:
                        ll = FeeType.objects.filter(fee_id=x)
                        if ll[0].fee_type not in pefeetype:
                            pefeetype.append(ll[0].fee_type)
                    for x in pefeeid:
                        cost = 0
                        li = WorkOrder.objects.filter(~Q(status=3), ~Q(status=0), ~Q(status=1), Q(structure_id=pe),
                                                      Q(feeid_id=x))
                        for y in li:
                            cost += float(y.cost)
                        pecost.append(cost)
                    for x in range(len(pefeeid)):
                        dic = {}
                        dic['value'] = pecost[x]
                        dic['name'] = pefeetype[x]
                        pedata.append(dic)
                    ret.update({
                        'pefeetype': pefeetype,
                        'pedata': pedata
                    })
        #运维中心
        if request.POST.get('ops'):
            op = request.POST.get('ops')
            opfeeid = []
            opfeetype = []
            opcost = []
            opdata = []
            exist = WorkOrder.objects.filter(~Q(status=3), ~Q(status=0), ~Q(status=1), Q(structure_id=op))
            if len(exist) == 0:
                ret['status'] = 'fail0'
                ret['errors_info'] = '该部门没有工单'
            else:
                li = WorkOrder.objects.filter(~Q(status=3), ~Q(status=0), ~Q(status=1), Q(structure_id=op),
                                              ~Q(feeid_id=None))
                if len(li) == 0:
                    ret['status'] = 'fail0'
                    ret['errors_info'] = '该部门工单无费用类型'
                else:
                    for x in li:
                        if x.feeid_id not in opfeeid:
                            pefeeid.append(x.feeid_id)
                    for x in pefeeid:
                        ll = FeeType.objects.filter(fee_id=x)
                        if ll[0].fee_type not in opfeetype:
                            opfeetype.append(ll[0].fee_type)
                    for x in opfeeid:
                        cost = 0
                        li = WorkOrder.objects.filter(~Q(status=3), ~Q(status=0), ~Q(status=1), Q(structure_id=op),
                                                      Q(feeid_id=x))
                        for y in li:
                            cost += float(y.cost)
                        opcost.append(cost)
                    for x in range(len(pefeeid)):
                        dic = {}
                        dic['value'] = opcost[x]
                        dic['name'] = opfeetype[x]
                        opdata.append(dic)
                    ret.update({
                        'opfeetype': opfeetype,
                        'opdata': opdata
                    })
        #证券事务中心 Securities affairs centre
        if request.POST.get('SAC'):
            sa = request.POST.get('SAC')
            safeeid = []
            safeetype = []
            sacost = []
            sadata = []
            exist = WorkOrder.objects.filter(~Q(status=3), ~Q(status=0), ~Q(status=1), Q(structure_id=sa))
            if len(exist) == 0:
                ret['status'] = 'fail0'
                ret['errors_info'] = '该部门没有工单'
            else:
                li = WorkOrder.objects.filter(~Q(status=3), ~Q(status=0), ~Q(status=1), Q(structure_id=sa),
                                              ~Q(feeid_id=None))
                if len(li) == 0:
                    ret['status'] = 'fail0'
                    ret['errors_info'] = '该部门工单无费用类型'
                else:
                    for x in li:
                        if x.feeid_id not in safeeid:
                            safeeid.append(x.feeid_id)
                    for x in safeeid:
                        ll = FeeType.objects.filter(fee_id=x)
                        if ll[0].fee_type not in safeetype:
                            safeetype.append(ll[0].fee_type)
                    for x in safeeid:
                        cost = 0
                        li = WorkOrder.objects.filter(~Q(status=3), ~Q(status=0), ~Q(status=1), Q(structure_id=sa),
                                                      Q(feeid_id=x))
                        for y in li:
                            cost += float(y.cost)
                        sacost.append(cost)
                    for x in range(len(safeeid)):
                        dic = {}
                        dic['value'] = sacost[x]
                        dic['name'] = safeetype[x]
                        sadata.append(dic)
                    ret.update({
                        'safeetype': safeetype,
                        'sadata': sadata
                    })
        #财务部
        if request.POST.get('finance'):
            fi = request.POST.get('finance')
            fifeeid = []
            fifeetype = []
            ficost = []
            fidata = []
            exist = WorkOrder.objects.filter(~Q(status=3), ~Q(status=0), ~Q(status=1), Q(structure_id=fi))
            if len(exist) == 0:
                ret['status'] = 'fail0'
                ret['errors_info'] = '该部门没有工单'
            else:
                li = WorkOrder.objects.filter(~Q(status=3), ~Q(status=0), ~Q(status=1), Q(structure_id=fi),
                                              ~Q(feeid_id=None))
                if len(li) == 0:
                    ret['status'] = 'fail0'
                    ret['errors_info'] = '该部门工单无费用类型'
                else:
                    for x in li:
                        if x.feeid_id not in fifeeid:
                            fifeeid.append(x.feeid_id)
                    for x in fifeeid:
                        ll = FeeType.objects.filter(fee_id=x)
                        if ll[0].fee_type not in fifeetype:
                            fifeetype.append(ll[0].fee_type)
                    for x in fifeeid:
                        cost = 0
                        li = WorkOrder.objects.filter(~Q(status=3), ~Q(status=0), ~Q(status=1), Q(structure_id=fi),
                                                      Q(feeid_id=x))
                        for y in li:
                            cost += float(y.cost)
                        ficost.append(cost)
                    for x in range(len(fifeeid)):
                        dic = {}
                        dic['value'] = ficost[x]
                        dic['name'] = fifeetype[x]
                        fidata.append(dic)
                    ret.update({
                        'fifeetype': fifeetype,
                        'fidata': fidata
                    })
        #售后服务
        if request.POST.get('afterSale'):
            af = request.POST.get('afterSale')
            affeeid = []
            affeetype = []
            afcost = []
            afdata = []
            exist = WorkOrder.objects.filter(~Q(status=3), ~Q(status=0), ~Q(status=1), Q(structure_id=af))
            if len(exist) == 0:
                ret['status'] = 'fail0'
                ret['errors_info'] = '该部门没有工单'
            else:
                li = WorkOrder.objects.filter(~Q(status=3), ~Q(status=0), ~Q(status=1), Q(structure_id=af),~Q(feeid_id=None))
                if len(li) == 0:
                    ret['status'] = 'fail0'
                    ret['errors_info'] = '该部门工单无费用类型'
                else:
                    for x in li:
                        if x.feeid_id not in affeeid:
                            affeeid.append(x.feeid_id)
                    for x in affeeid:
                        ll = FeeType.objects.filter(fee_id=x)
                        if ll[0].fee_type not in affeetype:
                            affeetype.append(ll[0].fee_type)
                    for x in affeeid:
                        cost = 0
                        li = WorkOrder.objects.filter(~Q(status=3), ~Q(status=0), ~Q(status=1), Q(structure_id=af),
                                                      Q(feeid_id=x))
                        for y in li:
                            cost += float(y.cost)
                        afcost.append(cost)
                    for x in range(len(affeeid)):
                        dic = {}
                        dic['value'] = afcost[x]
                        dic['name'] = affeetype[x]
                        afdata.append(dic)
                    ret.update({
                        'affeetype': affeetype,
                        'afdata': afdata
                    })
        #物资管理
        if request.POST.get('materials'):
            mm = request.POST.get('materials')
            mmfeeid = []
            mmfeetype = []
            mmcost = []
            mmdata = []
            exist = WorkOrder.objects.filter(~Q(status=3), ~Q(status=0), ~Q(status=1), Q(structure_id=mm))
            if len(exist) == 0:
                ret['status'] = 'fail0'
                ret['errors_info'] = '该部门没有工单'
            else:
                li = WorkOrder.objects.filter(~Q(status=3), ~Q(status=0), ~Q(status=1), Q(structure_id=mm),~Q(feeid_id=None))
                if len(li) == 0:
                    ret['status'] = 'fail0'
                    ret['errors_info'] = '该部门工单无费用类型'
                else:
                    for x in li:
                        if x.feeid_id not in mmfeeid:
                            mmfeeid.append(x.feeid_id)
                    for x in mmfeeid:
                        ll = FeeType.objects.filter(fee_id=x)
                        if ll[0].fee_type not in mmfeetype:
                            mmfeetype.append(ll[0].fee_type)
                    for x in mmfeeid:
                        cost = 0
                        li = WorkOrder.objects.filter(~Q(status=3), ~Q(status=0), ~Q(status=1), Q(structure_id=mm),
                                                      Q(feeid_id=x))
                        for y in li:
                            cost += float(y.cost)
                        mmcost.append(cost)
                    for x in range(len(mmfeeid)):
                        dic = {}
                        dic['value'] = mmcost[x]
                        dic['name'] = mmfeetype[x]
                        mmdata.append(dic)
                    ret.update({
                        'mmfeetype': mmfeetype,
                        'mmdata': mmdata
                    })
        #通信工程
        if request.POST.get('communication'):
            co = request.POST.get('communication')
            cofeeid = []
            cofeetype = []
            cocost = []
            codata = []
            exist = WorkOrder.objects.filter(~Q(status=3), ~Q(status=0), ~Q(status=1), Q(structure_id=co))
            if len(exist) == 0:
                ret['status'] = 'fail0'
                ret['errors_info'] = '该部门没有工单'
            else:
                li = WorkOrder.objects.filter(~Q(status=3), ~Q(status=0), ~Q(status=1), Q(structure_id=co),
                                              ~Q(feeid_id=None))
                if len(li) == 0:
                    ret['status'] = 'fail0'
                    ret['errors_info'] = '该部门工单无费用类型'
                else:
                    for x in li:
                        if x.feeid_id not in cofeeid:
                            cofeeid.append(x.feeid_id)
                    for x in cofeeid:
                        ll = FeeType.objects.filter(fee_id=x)
                        if ll[0].fee_type not in cofeetype:
                            cofeetype.append(ll[0].fee_type)
                    for x in cofeeid:
                        cost = 0
                        li = WorkOrder.objects.filter(~Q(status=3), ~Q(status=0), ~Q(status=1),Q(structure_id=co),Q(feeid_id=x))
                        for y in li:
                            cost += float(y.cost)
                        cocost.append(cost)
                    for x in range(len(cofeeid)):
                        dic = {}
                        dic['value'] = cocost[x]
                        dic['name'] = cofeetype[x]
                        codata.append(dic)
                    ret.update({
                        'cofeetype': cofeetype,
                        'codata': codata
                    })
        #电力工程
        if request.POST.get('electric'):
            epp = request.POST.get('electric')
            eppfeeid = []
            eppfeetype = []
            eppcost = []
            eppdata = []
            exist = WorkOrder.objects.filter(~Q(status=3), ~Q(status=0), ~Q(status=1), Q(structure_id=epp))
            if len(exist) == 0:
                ret['status'] = 'fail0'
                ret['errors_info'] = '该部门没有工单'
            else:
                li = WorkOrder.objects.filter(~Q(status=3), ~Q(status=0), ~Q(status=1), Q(structure_id=epp),
                                              ~Q(feeid_id=None))
                if len(li) == 0:
                    ret['status'] = 'fail0'
                    ret['errors_info'] = '该部门工单无费用类型'
                else:
                    for x in li:
                        if x.feeid_id not in eppfeeid:
                            eppfeeid.append(x.feeid_id)
                    for x in eppfeeid:
                        ll = FeeType.objects.filter(fee_id=x)
                        if ll[0].fee_type not in eppfeetype:
                            eppfeetype.append(ll[0].fee_type)
                    for x in eppfeeid:
                        cost = 0
                        li = WorkOrder.objects.filter(~Q(status=3), ~Q(status=0), ~Q(status=1),Q(structure_id=epp),Q(feeid_id=x))
                        for y in li:
                            cost += float(y.cost)
                        eppcost.append(cost)
                    for x in range(len(eppfeeid)):
                        dic = {}
                        dic['value'] = eppcost[x]
                        dic['name'] = eppfeetype[x]
                        eppdata.append(dic)
                    ret.update({
                        'eppfeetype': eppfeetype,
                        'eppdata': eppdata
                    })
        #上月
        if request.POST.get('lastMonth'):
            lmfeeid = []
            lmfeetype = []
            lmallcost = []
            lmdata = []
            if mon != 1:
                mon -= 1
            else:
                mon = 12
                year -= 1
            exist = WorkOrder.objects.filter(Q(cretor_id=manid), ~Q(status=3), ~Q(status=0), ~Q(status=1))
            if len(exist) == 0:
                ret['status'] = 'fail0'
                ret['errors_info'] = '请提交工单使用'
            else:
                li = WorkOrder.objects.filter(Q(create_time__year=year), Q(create_time__month=mon), Q(cretor_id=manid), ~Q(status=3), ~Q(status=0), ~Q(status=1))
                if len(li) == 0:
                    ret['status'] = 'fail1'
                    ret['errors_info'] = '该时间段内无工单'
                else:
                    for x in li:
                        if x.feeid_id not in lmfeeid and x.feeid_id != None:
                            lmfeeid.append(x.feeid_id)
                    if len(lmfeeid) == 0:
                        ret['status'] = 'fail2'
                        ret['errors_info'] = '工单内无费用类型'
                    else:
                        for x in lmfeeid:
                            li = FeeType.objects.filter(fee_id=x)
                            if li[0].fee_type not in lmfeetype:
                                lmfeetype.append(li[0].fee_type)
                        for x in lmfeeid:
                            cost = 0
                            li = WorkOrder.objects.filter(Q(create_time__year=year), Q(create_time__month=mon),Q(cretor_id=manid), ~Q(status=3), ~Q(status=0), ~Q(status=1), Q(feeid_id= x))
                            for y in li:
                                cost += float(y.cost)
                            lmallcost.append(cost)
                        for x in range(len(lmfeeid)):
                            dic = {}
                            dic['value'] = lmallcost[x]
                            dic['name'] = lmfeetype[x]
                            lmdata.append(dic)
                        ret.update({
                            'lmdata': lmdata,
                            'lmfeetype': lmfeetype
                        })
        #前三月
        if request.POST.get('lastThree'):
            ltfeeid = []
            ltfeetype = []
            ltallcost = []
            ltdata = []
            if mon == 3:
                year1 = year -1
                mon1 = 12
                mon2 = mon -1
            elif mon ==2:
                year1 = year -1
                mon1 =11
                mon2 = mon - 1
            elif mon == 1:
                year1 = year -1
                mon1 = 10
                mon2 = 12
            else:
                mon1 = mon -3
                mon2 = mon -1
                year1 =year
            start_t = str(year1) + '-' + str(mon1) + '-' +str(1)
            end_t = str(year) + '-' + str(mon) + '-' + str(1)
            exist = WorkOrder.objects.filter(Q(create_time__range=(start_t, end_t)), Q(cretor_id=manid), ~Q(status=3), ~Q(status=0), ~Q(status=1))
            if len(exist) == 0:
                ret['status'] = 'fail0'
                ret['errors_info'] = '请提交工单使用'
            else:
                for x in exist:
                    if x.feeid_id not in ltfeeid and x.feeid_id != None:
                        ltfeeid.append(x.feeid_id)
                if len(ltfeeid) == 0:
                    ret['status'] = 'fail'
                    ret['errors_info'] = '该时间段内没有使用费用类型'
                else:
                    for x in ltfeeid:
                        li = FeeType.objects.filter(fee_id=x)
                        if li[0].fee_type not in ltfeetype:
                            ltfeetype.append(li[0].fee_type)
                    for x in ltfeeid:
                        cost = 0
                        li = WorkOrder.objects.filter(Q(create_time__range=(start_t, end_t)), Q(feeid=x), Q(cretor_id=manid), ~Q(status=3), ~Q(status=0), ~Q(status=1))
                        for y in li:
                            cost += float(y.cost)
                        ltallcost.append(cost)
                    for x in range(len(ltfeeid)):
                        dic ={}
                        dic['value'] = ltallcost[x]
                        dic['name'] = ltfeetype[x]
                        ltdata.append(dic)
                    ret.update({
                        'ltfeetype':ltfeetype,
                        'ltdata':ltdata
                    })
        #时间段搜索工单
        if request.POST.get("start_time") and request.POST.get("end_time"):
            parafeeid = []  # para是段落的前四个字母,表示时间段内的费用id
            parafeetype = []
            paraallcost = []
            paradata = []
            start_time = request.POST.get("start_time")
            end_time = request.POST.get("end_time")
            exist = WorkOrder.objects.filter(Q(create_time__range=(start_time, end_time)), Q(cretor_id=manid), ~Q(status=3), ~Q(status=0), ~Q(status=1))
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
                        li = WorkOrder.objects.filter(Q(create_time__range=(start_time, end_time)), Q(feeid=x), Q(cretor_id=manid), ~Q(status=3), ~Q(status=0), ~Q(status=1))
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


class Check(View):

    def get(self, request):
        ret = dict()
        advise = Advise.objects.all()
        ret["advice"] = advise

        # creator = []
        # create_time = []
        # back = []
        # is_done = []
        # if advise:
        #     for x in advise:
        #         creator.append(x.creator)
        #         create_time.append(x.create_time)
        #         back.append(x.back)
        #         is_done.append(x.is_done)
        # else:
        #     creator = ''
        #     create_time = ''
        #     back = ''
        #     is_done = ''
        # ret.update({
        #     'create_time': create_time,
        #     'creator': creator,
        #     'back': back,
        #     'is_done': is_done,
        # })
        return render(request, 'checkAdvise.html', ret)


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
        return render(request, "feedback.html", ret)
