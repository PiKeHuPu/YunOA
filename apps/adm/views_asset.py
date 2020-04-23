import json
import re

from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.views.generic.base import View
from django.http import HttpResponse
from django.contrib.auth import get_user_model
from django.core.serializers.json import DjangoJSONEncoder

from adm.views import department_admin, warehouse_admin
from utils.mixin_utils import LoginRequiredMixin
from rbac.models import Menu
from system.models import SystemSetup
from .models import Asset, AssetType, AssetLog, AssetUseLog, AssetFile, AssetUseAddress, AssetInfo, AssetWarehouse, \
    AssetApprove, AssetApproveDetail
from .forms import AssetCreateForm, AssetUpdateForm, AssetUploadForm
from rbac.models import Role
from datetime import datetime

User = get_user_model()


class AssetView(LoginRequiredMixin, View):
    """
    资产管理
    """

    def get(self, request):
        ret = Menu.getMenuByRequestUrl(url=request.path_info)
        ret.update(SystemSetup.getSystemSetupLastData())
        status_list = []
        for status in Asset.asset_status:
            status_dict = dict(item=status[0], value=status[1])
            status_list.append(status_dict)
        asset_types = AssetType.objects.all()
        ret['status_list'] = status_list
        ret['asset_types'] = asset_types
        return render(request, 'adm/asset/asset.html', ret)


##
class AssetListView(LoginRequiredMixin, View):
    """
    资产获取list
    """

    def get(self, request):
        user_id = request.session.get("_auth_user_id")
        user = User.objects.get(id=user_id)
        department = user.department
        warehouses = department.assetwarehouse_set.filter(is_delete=False)
        warehouse_id_list = []
        for w in warehouses:
            warehouse_id_list.append(w.id)
        all_view_warehouse = AssetWarehouse.objects.filter(is_all_view=True)
        for w in all_view_warehouse:
            warehouse_id_list.append(w.id)

        fields = ['id', 'warehouse__name', 'number', 'name', 'quantity', 'status', 'unit', 'type', 'remark']
        filters = dict()
        filters['is_delete'] = False
        filters['warehouse_id__in'] = warehouse_id_list
        if 'assetNum' in request.GET and request.GET['assetNum']:
            filters['number__icontains'] = request.GET['assetNum']
        if 'warehouse' in request.GET and request.GET['warehouse']:
            filters['warehouse_id'] = request.GET['warehouse']
        if 'model' in request.GET and request.GET['model']:
            filters['type__icontains'] = request.GET['model']
        if 'status' in request.GET and request.GET['status']:
            filters['status'] = request.GET['status']
        if 'brand' in request.GET and request.GET['brand']:
            filters['name'] = request.GET['brand']
        ret = dict(data=list(AssetInfo.objects.filter(**filters).values(*fields).order_by("status")))
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type='application/json')


class AssetCreateView(LoginRequiredMixin, View):
    """
    新建资产
    """

    def get(self, request):
        ret = dict()
        status_list = []
        for status in Asset.asset_status:
            status_dict = dict(item=status[0], value=status[1])
            status_list.append(status_dict)
        asset_type = AssetType.objects.values()
        ret['asset_type'] = asset_type
        ret['status_list'] = status_list
        return render(request, 'adm/asset/asset_create.html', ret)

    def post(self, request):
        res = dict()
        asset_create_form = AssetCreateForm(request.POST)
        if asset_create_form.is_valid():
            asset_create_form.save()
            res['status'] = 'success'
        else:
            pattern = '<li>.*?<ul class=.*?><li>(.*?)</li>'
            errors = str(asset_create_form.errors)
            asset_form_errors = re.findall(pattern, errors)
            res = {
                'status': 'fail',
                'asset_form_errors': asset_form_errors[0]
            }

        return HttpResponse(json.dumps(res), content_type='application/json')


class AssetUpdateView(LoginRequiredMixin, View):
    """更新资产"""

    def get(self, request):
        ret = dict()
        status_list = []
        if 'id' in request.GET and request.GET['id']:
            asset = get_object_or_404(Asset, pk=request.GET['id'])
            ret['asset'] = asset
        for status in Asset.asset_status:
            status_dict = dict(item=status[0], value=status[1])
            status_list.append(status_dict)
        asset_type = AssetType.objects.values()
        ret['asset_type'] = asset_type
        ret['status_list'] = status_list
        return render(request, 'adm/asset/asset_update.html', ret)

    def post(self, request):
        res = dict()
        asset = get_object_or_404(Asset, pk=request.POST['id'])
        asset_update_form = AssetUpdateForm(request.POST, instance=asset)
        if asset_update_form.is_valid():
            asset_update_form.save()
            status = asset.get_status_display()
            asset_log = AssetLog()
            asset_log.asset_id = asset.id
            asset_log.operator = request.user.name
            asset_log.desc = """
            用户信息：{}  || 责任人：{}  || 资产状态：{}""".format(
                asset_update_form.cleaned_data.get("customer"),
                asset_update_form.cleaned_data.get("owner"),
                status,
            )
            asset_log.save()
            res['status'] = 'success'
        else:
            pattern = '<li>.*?<ul class=.*?><li>(.*?)</li>'
            errors = str(asset_update_form.errors)
            asset_form_errors = re.findall(pattern, errors)
            res = {
                'status': 'fail',
                'asset_form_errors': asset_form_errors[0]
            }

        return HttpResponse(json.dumps(res), content_type='application/json')


class AssetDetailView(LoginRequiredMixin, View):
    """
    资产管理：详情页面
    """

    def get(self, request):
        ret = dict()
        if 'id' in request.GET and request.GET['id']:
            asset = get_object_or_404(AssetInfo, pk=request.GET.get('id'))
            asset_log = asset.asseteditflow_set.all()
            ret['asset'] = asset
            ret['asset_log'] = asset_log
        return render(request, 'adm/asset/asset_detail.html', ret)


class AssetDeleteView(LoginRequiredMixin, View):
    """删除资产"""

    def post(self, request):
        ret = dict(result=False)
        if 'id' in request.POST and request.POST['id']:
            id_list = map(int, request.POST.get('id').split(','))
            Asset.objects.filter(id__in=id_list).delete()
            ret['result'] = True
        return HttpResponse(json.dumps(ret), content_type='application/json')


class AssetUseFlowView(LoginRequiredMixin, View):
    """
    查看资产领取日志
    """

    def get(self, request):
        ret = Menu.getMenuByRequestUrl(url=request.path_info)
        ret.update(SystemSetup.getSystemSetupLastData())
        status_list = []
        # 领取方, 0 自用  1 外包
        for status in AssetUseLog.party_choices:
            status_dict = dict(item=status[0], value=status[1])
            status_list.append(status_dict)
        asset_types = AssetType.objects.all()  # 仓库
        asset_status = []
        for status in Asset.asset_status:
            status_dict = dict(item=status[0], value=status[1])
            asset_status.append(status_dict)
        ret['status_list'] = status_list
        ret['asset_types'] = asset_types
        ret['asset_status'] = asset_status
        return render(request, 'adm/asset/asset_use_flow.html', ret)


class AssetUseFlowListView(LoginRequiredMixin, View):
    """
    领取资产信息获取list
    """

    def get(self, request):
        user_id = request.session.get("_auth_user_id")
        department_list = department_admin(user_id)
        warehouse_list = warehouse_admin(department_list)
        fields = ['id', 'asset__number', "asset__warehouse__id", 'asset__warehouse__name', 'asset__name', 'asset__type',
                  'quantity', 'proposer__name', 'create_time', 'return_date', 'purpose', 'use_status', 'status', 'type']
        filters = dict()
        if request.GET.get('asset_number'):
            filters['asset__number'] = request.GET['asset_number']
        if request.GET.get('asset_warehouse'):
            filters['asset__warehouse__id'] = request.GET['asset_warehouse']
        if request.GET.get('asset_name'):
            filters['asset__name'] = request.GET['asset_name']
        if request.GET.get("start_time") and request.GET.get("end_time"):
            start_time = request.GET.get("start_time")
            end_time = request.GET.get("end_time")
            filters['create_time__range'] = (start_time, end_time)
        filters['asset__warehouse__in'] = warehouse_list
        ret = dict(data=list(AssetApprove.objects.values(*fields).filter(**filters).order_by("-create_time")))
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type='application/json')


# 资产使用地址  TODO 可能是伪需求.
class AddressView(LoginRequiredMixin, View):
    """
    地址
    """

    def get(self, request):
        ret = Menu.getMenuByRequestUrl(url=request.path_info)
        ret.update(SystemSetup.getSystemSetupLastData())
        return render(request, 'adm/asset/address.html', ret)


#
# class AddressListView(LoginRequiredMixin, View):
#     """
#     资产使用地址列表
#     """
#     def get(self, request):
#         fields = ['id', 'name', 'desc']
#         ret = dict(data=list(AssetUseAddress.objects.values(*fields)))
#         return HttpResponse(json.dumps(ret), content_type='application/json')
#
#
# class AddressDetailView(LoginRequiredMixin, View):
#     """
#     资产类型：查看、修改、新建数据
#     """
#     def get(self, request):
#         ret=dict()
#         if 'id' in request.GET and request.GET['id']:
#             address = get_object_or_404(AssetUseAddress, pk=request.GET.get('id'))
#             ret['address'] = address
#         return render(request, 'adm/asset/address_detail.html', ret)
#
#     def post(self, request):
#         res = dict(result=False)
#         if 'id' in request.POST and request.POST['id']:
#             assettype = get_object_or_404(AssetType, pk=request.POST.get('id'))
#         else:
#             assettype = AssetType()
#         assettype_form = AssetTypeForm(request.POST, instance=assettype)
#         if assettype_form.is_valid():
#             assettype_form.save()
#             res['result'] = True
#         return HttpResponse(json.dumps(res), content_type='application/json')
#
#
# class AssetTypeDeleteView(LoginRequiredMixin, View):
#
#     def post(self, request):
#         ret = dict(result=False)
#         if 'id' in request.POST and request.POST['id']:
#             id_list = map(int, request.POST.get('id').split(','))
#             AssetType.objects.filter(id__in=id_list).delete()
#             ret['result'] = True
#         return HttpResponse(json.dumps(ret), content_type='application/json')
#
#
class AssetUploadView(LoginRequiredMixin, View):
    """
    上传配置资料：工单执行记录配置资料上传
    """

    def get(self, request):
        ret = dict()
        asset = get_object_or_404(Asset, pk=request.GET['id'])
        ret['asset'] = asset
        return render(request, 'adm/asset/asset_upload.html', ret)

    def post(self, request):
        res = dict(status='fail')
        asset_file = AssetFile()
        asset_upload_form = AssetUploadForm(request.POST, request.FILES, instance=asset_file)
        if asset_upload_form.is_valid():
            asset_upload_form.save()
            res['status'] = 'success'
        return HttpResponse(json.dumps(res, cls=DjangoJSONEncoder), content_type='application/json')


# 领取物料API
class AssetUseView(View):
    """领取更新资产"""

    def get(self, request):
        res = dict()
        if request.GET.get('assetNum'):
            asset = Asset.objects.filter(assetNum=request.GET.get('assetNum')).first()
            if asset:
                res['name'] = asset.brand
                res['id'] = asset.id
                res['model'] = asset.model
                res['count'] = asset.assetCount
                res['unit'] = asset.assetUnit
                res['status'] = 'success'
            # role = get_object_or_404(Role, title="没有权限")  # TODO 权限
            # user_info = role.userprofile_set.all()
            else:
                res = {
                    'status': 'fail',
                    'errors': '没有该物品信息，请检查条码是否正确'
                }
        else:
            res = {
                'status': 'fail',
                'errors': '参数错误'
            }
        return HttpResponse(json.dumps(res), content_type='application/json')

    def post(self, request):
        res = dict()
        ret_info = json.loads(request.body)
        if ret_info.get('id'):
            asset = Asset.objects.filter(id=ret_info.get('id')).first()
            use_count = ret_info.get('useCount')
            if use_count:
                if int(use_count) <= int(asset.assetCount):
                    asset_use = AssetUseLog()
                    asset_use.asset_id = asset.id
                    asset_use.operator = ret_info.get('operator')
                    asset_use.useCount = use_count
                    asset_use.area = ret_info.get('area')
                    asset_use.party = ret_info.get('party')
                    asset.assetCount = int(asset.assetCount) - int(use_count)
                    asset_use.save()
                    asset.save()
                    res['status'] = 'success'
                    res['assetCount'] = asset.assetCount
                else:
                    res = {
                        'status': 'fail',
                        'errors': '仓库没有这么多数量， 请与物资联系'
                    }
        else:
            res = {
                'status': 'fail',
                'errors': '登记失败， 请重试'
            }
        return HttpResponse(json.dumps(res), content_type='application/json')


##
class AssetUseHtmlView(LoginRequiredMixin, View):
    """
    物资领用页面
    """

    def get(self, request):
        ret = dict()
        user_id = request.session.get('_auth_user_id')
        user = User.objects.get(id=user_id)
        department = user.department
        warehouses = department.assetwarehouse_set.filter(is_delete=False)
        all_view_warehouses = AssetWarehouse.objects.filter(is_all_view=True, is_delete=False)
        warehouses = warehouses | all_view_warehouses
        status_list = []
        for status in Asset.asset_status:
            status_dict = dict(item=status[0], value=status[1])
            status_list.append(status_dict)
        ret['warehouses'] = warehouses
        ret['status_list'] = status_list
        return render(request, 'adm/asset/asset_use.html', ret)


##
class AssetUseInfoView(LoginRequiredMixin, View):
    """
    领用弹窗填写信息
    """

    def get(self, request):
        ret = dict()
        id = request.GET.get("id")
        asset = AssetInfo.objects.get(id=id)
        ret['asset'] = asset
        if asset.warehouse.is_no_return:
            ret["no_return"] = "1"
        return render(request, 'adm/asset/asset_detail_use.html', ret)

    def post(self, request):
        is_out = request.POST.get("is_out")
        res = dict()
        try:
            # 如外带则创建相应的在用物资
            asset_id = request.POST.get('id0')
            use_quantity = request.POST.get('useCount')
            asset = AssetInfo.objects.get(id=asset_id)
            if is_out == "1":
                asset.quantity = int(asset.quantity) - int(use_quantity)
                asset.save()
                if asset.warehouse.is_no_return:
                    pass
                else:
                    use_asset = asset
                    use_asset.id = None
                    use_asset.save()
                    use_asset.quantity = int(use_quantity)
                    use_asset.create_time = asset.create_time
                    use_asset.status = '1'
                    use_asset.user_id = request.session.get('_auth_user_id')
                    use_asset.save()
            else:
                if asset.warehouse.is_no_return:
                    asset.quantity = int(asset.quantity) - int(use_quantity)
                    asset.save()
            user_id = request.session.get('_auth_user_id')
            asset_order = AssetApprove()
            asset_order.proposer_id = user_id
            asset_order.asset_id = asset_id
            asset_order.quantity = use_quantity
            asset_order.purpose = request.POST.get('title')
            if is_out == "0":
                pass
            elif is_out == "1":
                asset_order.return_date = request.POST.get('use_time')
            asset_order.status = '0'
            asset_order.use_status = '0'
            asset_order.type = "0"
            asset_order.save()

            # 创建审批流程
            if asset.is_no_approve:
                pass
            else:
                user = User.objects.filter(id=user_id).first()
                department = user.department
                approver_list = department.adm_list
                if approver_list:
                    approver_list = approver_list.split(",")
                    for i in range(len(approver_list)):
                        approver_list[i] = int(approver_list[i])
                else:
                    approver_list = []
                if asset.is_vice_approve:
                    vice_manager_id = department.vice_manager_id
                    if vice_manager_id:
                        approver_list.append(int(vice_manager_id))
                warehouse = asset.warehouse
                verifier_list = warehouse.verifier.all()
                if verifier_list:
                    for i in verifier_list:
                        approver_list.append(int(i.id))
                approver_list2 = []
                for i in approver_list:
                    if i not in approver_list2:
                        approver_list2.append(i)
                if int(user_id) in approver_list2:
                    approver_list2.remove(int(user_id))
                for id0 in approver_list2:
                    approve = AssetApproveDetail()
                    approve.approver_id = int(id0)
                    if id0 == approver_list2[0]:
                        approve.status = "1"
                    approve.asset_order_id = asset_order.id
                    approve.save()
            if AssetApproveDetail.objects.filter(asset_order=asset_order):
                pass
            else:
                asset_order.status = "2"
                asset_order.save()
            res['status'] = 'success'
        except Exception as e:
            res['e'] = str(e)
        return HttpResponse(json.dumps(res), content_type='application/json')


##
class AssetBackView(LoginRequiredMixin, View):
    """
    物资归还
    """

    def get(self, request):
        ret = dict()
        id = request.GET.get("id")
        asset_order = AssetApprove.objects.filter(id=id)[0]
        ret['asset_order'] = asset_order
        back_count = int(asset_order.quantity) - int(asset_order.return_quantity)
        ret["back_count"] = back_count
        return render(request, 'adm/asset/asset_back_use_info.html', ret)

    def post(self, request):
        ret = dict()
        user_id = request.session.get("_auth_user_id")
        id = request.POST.get("id")
        back_count = request.POST.get("backCount")
        asset_order = AssetApprove.objects.filter(id=id)[0]
        if int(back_count) + int(asset_order.return_quantity) == int(asset_order.quantity):
            asset_order.use_status = "2"
            asset_order.return_operator_id = user_id
            asset_order.return_quantity = back_count
            asset_order.t_return_date = datetime.today()

            if asset_order.return_date != None:
                asset = asset_order.asset
                asset.quantity += int(back_count)
                asset.save()

                use_asset = AssetInfo.objects.filter(name=asset_order.asset.name, user_id=asset_order.proposer_id, quantity__lte=asset_order.quantity, warehouse=asset_order.asset.warehouse)[0]
                use_asset.delete()
            asset_order.save()
        elif int(back_count) < int(asset_order.quantity) - int(asset_order.return_quantity):
            if asset_order.return_date != None:
                use_asset = AssetInfo.objects.filter(name=asset_order.asset.name, user_id=asset_order.proposer_id,
                                                     quantity__lte=asset_order.quantity,
                                                     warehouse=asset_order.asset.warehouse)[0]
                use_asset.quantity -= int(back_count)
                use_asset.save()

                asset = asset_order.asset
                asset.quantity += int(back_count)
                asset.save()

            asset_order.return_quantity += int(back_count)
            asset_order.return_operator_id = user_id
            asset_order.t_return_date = datetime.today()
            asset_order.save()
        ret["status"] = "success"

        return HttpResponse(json.dumps(ret), content_type='application/json')
