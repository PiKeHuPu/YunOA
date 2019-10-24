import json
import re

from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.views.generic.base import View
from django.http import HttpResponse
from django.contrib.auth import get_user_model
from django.core.serializers.json import DjangoJSONEncoder

from utils.mixin_utils import LoginRequiredMixin
from rbac.models import Menu
from system.models import SystemSetup
from .models import Asset, AssetType, AssetLog, AssetUseLog, AssetFile, AssetUseAddress
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


class AssetListView(LoginRequiredMixin, View):
    """
    资产获取list
    """

    def get(self, request):
        fields = ['assetNum', 'assetType__name', 'brand', 'model', 'status', 'assetCount', 'assetUnit', 'operator',
                  'add_time', 'id']
        filters = dict()

        if 'assetNum' in request.GET and request.GET['assetNum']:
            filters['assetNum__icontains'] = request.GET['assetNum']
        if 'assetType' in request.GET and request.GET['assetType']:
            filters['assetType'] = request.GET['assetType']
        if 'model' in request.GET and request.GET['model']:
            filters['model__icontains'] = request.GET['model']
        if 'status' in request.GET and request.GET['status']:
            filters['status'] = request.GET['status']
        ret = dict(data=list(Asset.objects.filter(**filters).values(*fields)))
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
            asset = get_object_or_404(Asset, pk=request.GET.get('id'))
            asset_log = asset.assetlog_set.all()
            asset_file = asset.assetfile_set.all()
            ret['asset'] = asset
            ret['asset_log'] = asset_log
            ret['asset_file'] = asset_file
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
        fields = ['asset__assetNum', 'asset__assetType__name', 'asset__brand', 'asset__model', 'asset__status',
                  'useCount', 'asset__assetUnit', 'operator', 'add_time', 'area','title', 'id', 'party', 'give_back',
                  'back_date']
        filters = dict()

        if request.GET.get('assetNum'):
            filters['asset__assetNum__icontains'] = request.GET['assetNum']
        if request.GET.get('assetType'):
            filters['asset__assetType'] = request.GET['assetType']
        if request.GET.get('party'):
            filters['party__icontains'] = request.GET['party']
        if request.GET.get('status'):
            filters['asset__status'] = request.GET['status']
        ret = dict(data=list(AssetUseLog.objects.filter(**filters).values(*fields)))
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
                    # status = asset.get_status_display()  # TODO 状态是否修改
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


class AssetUseHtmlView(LoginRequiredMixin, View):
    """
    物资领用页面
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
        return render(request, 'adm/asset/asset_use.html', ret)

class AssetUseInfoView(LoginRequiredMixin, View):
    """
    领用弹窗填写信息
    """

    def get(self, request):
        ret = Menu.getMenuByRequestUrl(url=request.path_info)
        if 'id' in request.GET and request.GET['id']:
            asset = get_object_or_404(Asset, pk=request.GET.get('id'))
            ret['asset'] = asset
        return render(request, 'adm/asset/asset_detail_use.html', ret)

    def post(self, request):
        res = dict()
        ret_info = json.loads(request.body)
        if ret_info.get('id'):
            asset = Asset.objects.filter(id=ret_info.get('id')).first()
            use_count = ret_info.get('useCount')
            if use_count:
                if int(use_count) <= int(asset.assetCount):
                    # status = asset.get_status_display()  # TODO 状态是否修改
                    asset_use = AssetUseLog()
                    asset_use.asset_id = asset.id
                    asset_use.operator = request.user.name
                    asset_use.useCount = use_count
                    asset_use.title = ret_info.get('title', '')
                    asset.assetCount = int(asset.assetCount) - int(use_count)
                    asset_use.save()
                    asset.save()
                    res['status'] = 'success'
                    res['assetCount'] = asset.assetCount
                else:
                    res = {
                        'status': 'fail',
                        'errors': '仓库没有这么多数量， 请与仓库部门人联系'
                    }
        else:
            res = {
                'status': 'fail',
                'errors': '登记失败， 请重试'
            }
        return HttpResponse(json.dumps(res), content_type='application/json')

class AssetBackView(LoginRequiredMixin, View):
    """
    物资归还
    """

    def get(self, request):
        ret = Menu.getMenuByRequestUrl(url=request.path_info)
        if 'id' in request.GET and request.GET['id']:
            asset_use = get_object_or_404(AssetUseLog, pk=request.GET.get('id'))
            ret['asset_use'] = asset_use
            ret['asset'] = asset_use.asset
        return render(request, 'adm/asset/asset_back_use_info.html', ret)

    def post(self, request):
        res = dict()
        ret_info = json.loads(request.body)
        if ret_info.get('id'):
            asset_use = AssetUseLog.objects.filter(id=ret_info.get('id')).first()
            back_count = ret_info.get('backCount')
            if back_count:
                if int(back_count) <= int(asset_use.useCount):
                    # status = asset.get_status_display()  # TODO 状态是否修改
                    asset_use.back_creator = request.user
                    asset_use.back_count = back_count
                    asset_use.back_date = datetime.now()
                    asset_use.give_back = "1"
                    asset = asset_use.asset
                    asset.assetCount = int(asset.assetCount) + int(back_count)
                    asset_use.save()
                    asset.save()
                    res['status'] = 'success'
                    res['assetCount'] = asset.assetCount
                else:
                    res = {
                        'status': 'fail',
                        'errors': '领取数量比归还数量少， 请仔细检查'
                    }
        else:
            res = {
                'status': 'fail',
                'errors': '登记失败， 请稍后重试'
            }
        return HttpResponse(json.dumps(res), content_type='application/json')
