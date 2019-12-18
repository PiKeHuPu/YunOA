import json

from django.contrib.auth import get_user_model
from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic.base import View

from adm import migrate_asset
from adm.migrate_asset import migrate_asset_flow, create_no_back
from adm.models import AssetWarehouse, AssetInfo, AssetEditFlow, AssetApprove, AssetApproveDetail
from users.models import Structure
from utils.mixin_utils import LoginRequiredMixin
from rbac.models import Menu, Role
from system.models import SystemSetup

User = get_user_model()


def switch_date_str(str0):
    str0 = str0.replace("年", "-")
    str0 = str0.replace("月", "-")
    str0 = str0.replace("日", "")
    return str0


def department_admin(user_id):
    """
    返回用户可管理的资产部门列表
    :param user_id:
    :return:
    """
    departments = Structure.objects.filter(administrator_id=user_id)
    if departments:
        for department in departments:
            if department.super_adm:
                department_list = Structure.objects.all()
                break
        else:
            department_list = departments
    else:
        department_list = []
    return department_list


def warehouse_admin(department_list):
    """
    通过部门列表返回仓库列表
    :param department_list:
    :return:
    """
    warehouse_list = []
    for department in department_list:
        if department.assetwarehouse_set.filter(is_delete=False):
            for i in department.assetwarehouse_set.filter(is_delete=False):
                warehouse_list.append(i)
    return warehouse_list


class AdmView(LoginRequiredMixin, View):
    """
    行政
    """

    def get(self, request):
        ret = Menu.getMenuByRequestUrl(url=request.path_info)
        ret.update(SystemSetup.getSystemSetupLastData())
        return render(request, 'adm/adm_index.html', ret)


# class DepartmentManageView(LoginRequiredMixin, View):
#     """
#     资产部门管理
#     """
#
#     def get(self, request):
#         ret = dict()
#         assetDepartments = AssetDepartment.objects.filter(is_delete=False)
#         ret["assetDepartments"] = assetDepartments
#         return render(request, "adm/layer/department.html", ret)


# class DepartmentCreateView(LoginRequiredMixin, View):
#     """
#     创建资产部门
#     """
#
#     def get(self, request):
#         ret = dict()
#         if request.GET.get("id"):
#             assetDepartment = AssetDepartment.objects.get(id=request.GET.get("id"))
#             ret['assetDepartment'] = assetDepartment
#         users = User.objects.filter(is_active=1, is_staff=0)
#         ret['users'] = users
#         return render(request, "adm/layer/department_create.html", ret)
#
#     def post(self, request):
#         ret = dict()
#         department_id = request.POST.get("id")
#         name = request.POST.get("department")
#         administrator = request.POST.get("operator")
#         super_department = request.POST.get("admin").startswith("t")
#
#         if name:
#             if department_id:
#                 assetDepartment = AssetDepartment.objects.get(id=department_id)
#             else:
#                 assetDepartment = AssetDepartment()
#             assetDepartment.name = name
#             assetDepartment.administrator_id = administrator
#             assetDepartment.super_adm = super_department
#             assetDepartment.save()
#
#             if administrator:
#                 role = Role.objects.get(title="仓库管理")
#                 user = User.objects.get(id=administrator)
#                 role.userprofile_set.add(user)
#             ret['result'] = True
#         else:
#             ret['result'] = False
#         return HttpResponse(json.dumps(ret), content_type='application/json')
#
#
# class DepartmentDeleteView(LoginRequiredMixin, View):
#     """
#     删除资产部门
#     """
#
#     def get(self, request):
#         ret = dict()
#         department_id = request.GET.get("id")
#         assetDepartment = AssetDepartment.objects.get(id=department_id)
#         assetDepartment.is_delete = True
#         warehouses = assetDepartment.assetwarehouse_set.all()
#         for warehouse in warehouses:
#             warehouse.is_delete = True
#             warehouse.save()
#         assetDepartment.save()
#         ret['result'] = True
#         return HttpResponse(json.dumps(ret), content_type='application/json')


class WarehouseView(LoginRequiredMixin, View):
    """
    资产仓库管理
    """

    def get(self, request):
        ret = dict()
        user_id = request.session.get("_auth_user_id")

        department_list = department_admin(user_id)
        warehouse_list = warehouse_admin(department_list)

        ret['warehouse_list'] = warehouse_list
        return render(request, "adm/layer/warehouse.html", ret)


class WarehouseCreateView(LoginRequiredMixin, View):
    """
    新建资产仓库
    """

    def get(self, request):
        ret = dict()
        id = request.GET.get("id")
        if id:
            warehouse = AssetWarehouse.objects.get(id=id)
            ret["warehouse"] = warehouse
        user_id = request.session.get("_auth_user_id")
        department_list = department_admin(user_id)
        ret["department_list"] = department_list
        return render(request, "adm/layer/warehouse_create.html", ret)

    def post(self, request):
        ret = dict()
        id = request.POST.get("id")
        name = request.POST.get("name")
        department_id = request.POST.get("department_id")
        remark = request.POST.get("remark")
        is_all_view = request.POST.get("is_all_view")
        if name and department_id:
            if id:
                warehouse = AssetWarehouse.objects.get(id=id)
            else:
                warehouse = AssetWarehouse()
            warehouse.name = name
            warehouse.department_id = department_id
            warehouse.is_all_view = is_all_view.startswith('t')
            warehouse.remark = remark
            warehouse.save()
            ret["result"] = True
        else:
            ret["result"] = False
        return HttpResponse(json.dumps(ret), content_type='application/json')


class WarehouseDeleteView(LoginRequiredMixin, View):
    """
    删除仓库
    """

    def get(self, request):
        ret = dict()
        id = request.GET.get("id")
        warehouse = AssetWarehouse.objects.get(id=id)
        warehouse.is_delete = True
        assets = warehouse.assetinfo_set.all()
        for asset in assets:
            asset.is_delete = True
            asset.save()
        warehouse.save()
        ret["result"] = True
        return HttpResponse(json.dumps(ret), content_type='application/json')


class AssetView(LoginRequiredMixin, View):
    """
    资产信息
    """

    def get(self, request):
        # migrate_asset.migrate_asset()
        ret = dict()
        user_id = request.session.get("_auth_user_id")
        department_list = department_admin(user_id)
        # 获取可管理资产的id
        asset_id_list = []
        warehouse_list = warehouse_admin(department_list)
        for warehouse in warehouse_list:
            id_list = warehouse.assetinfo_set.filter(is_delete=False).values("id")
            asset_id_list += id_list
        asset_id_list = [int(i["id"]) for i in asset_id_list]
        ret['asset_id_list'] = asset_id_list
        return render(request, "adm/layer/asset.html", ret)

    def post(self, request):
        """
        资产删除
        :param request:
        :return:
        """
        ret = dict()
        try:
            asset_id = request.POST.get("id")
            asset = AssetInfo.objects.get(id=asset_id)
            asset.is_delete = True
            asset.save()
            ret["result"] = True
        except:
            ret["result"] = False
        return HttpResponse(json.dumps(ret), content_type="application/json")


class AssetCreateView(LoginRequiredMixin, View):
    """
    录入资产
    """

    def get(self, request):
        ret = dict()
        user_id = request.session.get("_auth_user_id")
        asset_id = request.GET.get("id")
        if asset_id:
            asset = AssetInfo.objects.get(id=asset_id)
            ret['asset'] = asset
        department_list = department_admin(user_id)
        ret['department_list'] = department_list
        ret['none'] = ''
        return render(request, "adm/layer/asset_create.html", ret)

    def post(self, request):
        ret = dict()
        try:
            user_id = request.session.get("_auth_user_id")
            id0 = request.POST.get("id0")
            number = request.POST.get("number")
            if id0:
                asset = AssetInfo.objects.get(id=id0)
                if AssetInfo.objects.filter(Q(number=number) & ~Q(id=id0) & Q(is_delete=False)):
                    ret['asset_form_errors'] = "资产编号已存在"
                    raise AttributeError
                asset_edit_flow = AssetEditFlow()
                asset_edit_flow.asset_id = asset.id
                asset_edit_flow.operator_id = user_id
                asset_edit_flow.content = '修改'
                asset_edit_flow.save()
            else:
                asset = AssetInfo()
                if AssetInfo.objects.filter(Q(number=number) & Q(is_delete=False)):
                    ret['asset_form_errors'] = "资产编号已存在"
                    raise AttributeError
            asset.number = number
            asset.name = request.POST.get("name")
            asset.department_id = request.POST.get("department")
            asset.warehouse_id = request.POST.get("warehouse")
            asset.quantity = request.POST.get("quantity")
            asset.operator_id = user_id
            if request.POST.get("due_time") and request.POST.get("due_time") != "None":
                due_time = switch_date_str(request.POST.get("due_time"))
                print(due_time)
                asset.due_time = due_time
            asset.unit = request.POST.get("unit")
            asset.type = request.POST.get("type")
            asset.remark = request.POST.get("remark")
            if request.POST.get("no_approve") == "on":
                asset.is_no_approve = True
            if request.POST.get("no_return") == "on":
                asset.is_no_return = True
            asset.save()
            if id0 == "":
                asset_edit_flow = AssetEditFlow()
                asset_edit_flow.asset_id = asset.id
                asset_edit_flow.operator_id = user_id
                asset_edit_flow.content = '创建'
                asset_edit_flow.save()
            ret['status'] = "success"
        except:
            ret['status'] = "fail"
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type="application/json")


class AssetAjaxView(LoginRequiredMixin, View):
    """
    资产ajax
    """

    def get(self, request):
        ret = dict()
        # 根据所选择的部门获取相应的仓库
        department_id = request.GET.get("department_id")
        if department_id:
            department = Structure.objects.get(id=department_id)
            warehouses = department.assetwarehouse_set.filter(is_delete=False)
            warehouse_list = ""
            for warehouse in warehouses:
                option_str = "<option value=" + str(warehouse.id) + ">" + warehouse.name + "</option>"
                warehouse_list += option_str
            ret['warehouse_list'] = warehouse_list

        # 获取资产列表
        fields = ['id', 'number', 'name', 'department__title', 'warehouse__name', 'quantity', 'type', 'status', 'unit',
                  'create_time', 'due_time']
        filter = dict()
        if request.GET.get('number'):
            filter['number'] = request.GET.get('number')
        if request.GET.get('name'):
            filter['name'] = request.GET.get('name')
        user_id = request.session.get("_auth_user_id")
        department_list = department_admin(user_id)

        warehouse_list = []
        for department in department_list:
            if department.assetwarehouse_set.filter(is_delete=False, is_all_view=False):
                for i in department.assetwarehouse_set.filter(is_delete=False, is_all_view=False):
                    warehouse_list.append(i)
        ret['data'] = list()
        for w in warehouse_list:
            assets = w.assetinfo_set.filter(is_delete=False, **filter).values(*fields).order_by('-create_time')
            ret['data'] += assets

        all_view_warehouse_list = AssetWarehouse.objects.filter(is_delete=False, is_all_view=True)
        for w in all_view_warehouse_list:
            assets = w.assetinfo_set.filter(is_delete=False, **filter).values(*fields).order_by('-create_time')
            ret['data'] += assets
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type="application/json")


class AssetUseFlowView(LoginRequiredMixin, View):
    """
    领用记录页面
    """

    def get(self, request):
        ret = dict()
        user_id = request.session.get("_auth_user_id")
        department_list = department_admin(user_id)
        warehouse_list = warehouse_admin(department_list)
        ret['warehouse_list'] = warehouse_list
        return render(request, "adm/layer/asset_useflow.html", ret)

    def post(self, request):
        ret = dict()
        try:
            id = request.POST.get("id")
            asset_order = AssetApprove.objects.filter(id=id)[0]
            if asset_order.asset.is_no_return:
                asset_order.use_status = "3"
            else:
                asset_order.use_status = "1"
            asset_order.save()
            ret["success"] = True
        except:
            ret["success"] = False
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type="application/json")


class AssetApplyView(LoginRequiredMixin, View):
    '''
    物资申请页面
    '''

    def get(self, request):
        ret = dict()
        user_id = request.session.get('_auth_user_id')
        asset_order_list = AssetApprove.objects.filter(proposer_id=user_id).order_by('-create_time')
        ret['asset_order_list'] = asset_order_list

        return render(request, 'adm/layer/asset_order.html', ret)


class AssetApproveresultView(LoginRequiredMixin, View):
    def get(self, request):
        """
        审批意见
        :param request:
        :return:
        """
        ret = dict()
        id = request.GET.get("id")
        ps = request.GET.get("ps")
        ret["id"] = id
        ret["ps"] = ps
        return render(request, "adm/layer/approval_opinion.html", ret)

    def post(self, request):
        '''
        物资审批ajax
        '''
        ret = dict()
        id = request.POST.get("id")
        ps = request.POST.get("ps")
        content = request.POST.get("content")

        asset_approve = AssetApproveDetail.objects.get(id=id)
        asset_approve.is_pass = ps
        asset_approve.remark = content
        asset_approve.save()

        asset_order = asset_approve.asset_order
        if ps == "0":
            asset_order.status = "3"
            asset_order.save()
            asset_approve = AssetApproveDetail.objects.filter(asset_order=asset_order, is_pass=None)
            for approve in asset_approve:
                approve.delete()
            use_asset = AssetInfo.objects.filter(name=asset_order.asset.name, user_id=asset_order.proposer_id,quantity__lte=asset_order.quantity,warehouse=asset_order.asset.warehouse)[0]
            asset = asset_order.asset
            asset.quantity += int(use_asset.quantity)
            asset.save()
            use_asset.delete()
        else:
            asset_order = asset_approve.asset_order
            asset_approve_list = AssetApproveDetail.objects.filter(asset_order=asset_order)
            asset_order_1 = len(asset_approve_list)
            asset_order_2 = len(AssetApproveDetail.objects.filter(Q(asset_order=asset_order) & ~Q(is_pass=None)))
            if asset_order_2 > 0:
                asset_order.status = "1"
            if asset_order_2 == asset_order_1:
                for i in asset_approve_list:
                    if i.is_pass == "0":
                        asset_order.status = "3"
                        break
                else:
                    asset_order.status = "2"
            asset_order.save()
        ret["success"] = True

        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type='application/json')


class AssetApproveView(LoginRequiredMixin, View):
    """
    物资审批页面
    """

    def get(self, request):
        ret = dict()
        user_id = request.session.get("_auth_user_id")
        approve_list = AssetApproveDetail.objects.filter(approver_id=user_id, is_pass=None)
        ret['approve_list'] = approve_list
        return render(request, "adm/layer/asset_approve.html", ret)


class AssetApproveHistoryView(LoginRequiredMixin, View):
    """
    审批历史页面
    """

    def get(self, request):
        ret = dict()
        user_id = request.session.get("_auth_user_id")
        asset_approve_history_list = AssetApproveDetail.objects.filter(~Q(is_pass=None) & Q(approver_id=user_id))
        ret['asset_approve_history_list'] = asset_approve_history_list
        return render(request, "adm/layer/asset_approve_history.html", ret)


class AssetOrderDetailView(LoginRequiredMixin, View):
    """
    物资申请详情页面
    """

    def get(self, request):
        ret = dict()
        # user_id = request.session.get("_auth_user_id")
        id = request.GET.get("id")
        asset_order = AssetApprove.objects.get(id=id)
        ret["asset_order"] = asset_order
        asset_approve_list = asset_order.assetapprovedetail_set.all()
        ret['asset_approve_list'] = asset_approve_list
        return render(request, "adm/layer/asset_order_detail.html", ret)
