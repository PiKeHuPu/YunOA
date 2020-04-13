import copy
import json
import os
import time
from datetime import datetime

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q
from django.http import HttpResponse, StreamingHttpResponse, Http404, FileResponse
from django.shortcuts import render
from django.utils.encoding import escape_uri_path
from django.views.generic.base import View

from adm import migrate_asset
from adm.migrate_asset import migrate_asset_flow, create_no_back
from adm.models import AssetWarehouse, AssetInfo, AssetEditFlow, AssetApprove, AssetApproveDetail, FileManage, FileType
from users.models import Structure
from rbac.models import Menu, Role
from system.models import SystemSetup
from utils.mixin_utils import LoginRequiredMixin

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
    user = User.objects.get(id=user_id)
    department_list = []
    if user.is_dep_administrator:
        if user.department.super_adm:
            department_list = Structure.objects.all()
        else:
            department_list.append(user.department)
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
        list1 = []
        for i in warehouse_list:
            user = i.verifier.all()
            list1.append(user)
        ret['user_list'] = list1
        return render(request, "adm/layer/warehouse.html", ret)


class WarehouseCreateView(LoginRequiredMixin, View):
    """
    新建资产仓库
    """

    def get(self, request):
        global warehouse
        ret = dict()
        id = request.GET.get("id")
        if id:
            warehouse = AssetWarehouse.objects.get(id=id)
            ret["warehouse"] = warehouse
            k = "1"
        else:
            k = "0"
        user_id = request.session.get("_auth_user_id")
        department_list = department_admin(user_id)
        ret["department_list"] = department_list

        if k == "1":
            added_users = warehouse.verifier.all()
            ret["added_users"] = added_users
        users = User.objects.filter(is_active="1")
        ret["users"] = users
        return render(request, "adm/layer/warehouse_create.html", ret)

    def post(self, request):
        ret = dict()
        id = request.POST.get("warehouse_id")
        name = request.POST.get("warehouse")
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
            if is_all_view == "on":
                warehouse.is_all_view = True
            else:
                warehouse.is_all_view = False
            warehouse.remark = remark
            warehouse.save()

            wh_ver = warehouse.verifier.all()
            warehouse.verifier.remove(*wh_ver)

            if 'to' in request.POST and request.POST['to']:
                # print(request.POST.getlist('to', []))
                id_list = request.POST.getlist('to', [])
                add_users = User.objects.filter(id__in=id_list)
                warehouse.verifier.add(*add_users)

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
        ret['warehouse_list'] = warehouse_list
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
            name = request.POST.get("name")
            unit = request.POST.get("unit")
            type0 = request.POST.get("type")
            department_id = request.POST.get("department")
            warehouse_id = request.POST.get("warehouse")
            quantity = request.POST.get("quantity")
            status = request.POST.get("status")

            if id0:
                asset = AssetInfo.objects.get(id=id0)
                if AssetInfo.objects.filter(
                        Q(number=number) & ~Q(id=id0) & Q(is_delete=False) & Q(status="0") & ~Q(name=name)):
                    ret['asset_form_errors'] = "资产编号已存在"
                    raise AttributeError
                asset.quantity = quantity
                asset_edit_flow = AssetEditFlow()
                asset_edit_flow.asset_id = asset.id
                asset_edit_flow.operator_id = user_id
                asset_edit_flow.content = '修改'
                asset_edit_flow.save()
            else:
                if AssetInfo.objects.filter(Q(number=number) & Q(is_delete=False) & ~Q(name=name)):
                    ret['asset_form_errors'] = "资产编号已存在"
                    raise AttributeError
                added_adm = AssetInfo.objects.filter(
                    Q(number=number) & Q(name=name) & Q(status="0") & Q(unit=unit) & Q(
                        type=type0) & Q(department_id=department_id) & Q(warehouse_id=warehouse_id)).first()
                if added_adm:
                    asset = added_adm
                    asset.quantity += int(quantity)
                else:
                    asset = AssetInfo()
                    asset.quantity = int(quantity)
            if number:
                asset.number = number
            else:
                asset.number = "AC" + str(int(time.time()))
            asset.name = name
            asset.department_id = department_id
            asset.warehouse_id = warehouse_id
            asset.operator_id = user_id
            if request.POST.get("due_time") and request.POST.get("due_time") != "None":
                due_time = switch_date_str(request.POST.get("due_time"))
                asset.due_time = due_time
            asset.unit = request.POST.get("unit")
            asset.type = request.POST.get("type")
            asset.status = status
            asset.remark = request.POST.get("remark")
            if request.POST.get("no_approve") == "on":
                asset.is_no_approve = True
            else:
                asset.is_no_approve = False
            if request.POST.get("no_return") == "on":
                asset.is_no_return = True
            else:
                asset.is_no_return = False
            if request.POST.get("vice_approve") == "on":
                asset.is_vice_approve = True
            else:
                asset.is_vice_approve = False
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
                  'create_time', 'due_time', 'warehouse__id']
        filter = dict()
        if request.GET.get('number'):
            filter['number'] = request.GET.get('number')
        if request.GET.get('name'):
            filter['name'] = request.GET.get('name')
        if request.GET.get("asset_warehouse"):
            filter['warehouse_id'] = request.GET.get("asset_warehouse")
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
                if asset_order.type == "1":
                    asset_order.use_status = "4"
                    asset = copy.deepcopy(asset_order.asset)
                    asset.id = None
                    asset.save()
                    asset.quantity = asset_order.quantity
                    asset.status = "0"
                    asset.is_delete = False
                    asset.operator_id = asset_order.proposer_id
                    asset.department_id = asset_order.transfer_department_id
                    asset.warehouse_id = asset_order.transfer_warehouse_id
                    asset.save()

                    use_asset = AssetInfo.objects.filter(name=asset_order.asset.name, user_id=asset_order.proposer_id,
                                                         quantity__lte=asset_order.quantity,
                                                         warehouse=asset_order.asset.warehouse)[0]
                    use_asset.delete()
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

    def post(self, request):
        """
        取消领用ajax
        :param request:
        :return:
        """
        ret = dict()
        id0 = request.POST.get("id")
        user_id = request.session.get("_auth_user_id")
        asset_log = AssetApprove.objects.filter(id=id0).first()
        asset_log.use_status = "5"
        asset_log.return_quantity = asset_log.quantity
        asset_log.return_operator_id = user_id
        asset_log.t_return_date = datetime.today()
        asset_log.save()
        if asset_log.return_date != None:
            asset = asset_log.asset
            asset.quantity += asset_log.quantity
            asset.save()

            use_asset = AssetInfo.objects.filter(name=asset_log.asset.name, user_id=asset_log.proposer_id,
                                                 quantity__lte=asset_log.quantity,
                                                 warehouse=asset_log.asset.warehouse).first()
            use_asset.delete()
        ret["success"] = "1"
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type="application/json")


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
        asset_approve.status = "2"
        asset_approve.remark = content
        asset_approve.save()

        asset_order = asset_approve.asset_order
        # 当审批未通过时取消未审批人的审批
        if ps == "0":
            asset_order.status = "3"
            asset_order.save()
            asset_approve = AssetApproveDetail.objects.filter(asset_order=asset_order, is_pass=None)
            for approve in asset_approve:
                approve.delete()
            use_asset = AssetInfo.objects.filter(name=asset_order.asset.name, user_id=asset_order.proposer_id,
                                                 quantity__lte=asset_order.quantity,
                                                 warehouse=asset_order.asset.warehouse)[0]
            asset = asset_order.asset
            asset.quantity += int(use_asset.quantity)
            if asset.is_delete:
                asset.is_delete = False
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
            # 下一个审批人开始审批
            for a in asset_approve_list:
                if a.status == "0":
                    a.status = "1"
                    a.save()
                    break
        ret["success"] = True

        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type='application/json')


class AssetApproveView(LoginRequiredMixin, View):
    """
    物资审批页面
    """

    def get(self, request):
        ret = dict()
        user_id = request.session.get("_auth_user_id")
        approve_list = AssetApproveDetail.objects.filter(approver_id=user_id, is_pass=None, status="1")
        ret['approve_list'] = approve_list
        return render(request, "adm/layer/asset_approve.html", ret)


class AssetApproveHistoryView(LoginRequiredMixin, View):
    """
    审批历史页面
    """

    def get(self, request):
        ret = dict()
        user_id = request.session.get("_auth_user_id")
        asset_approve_history_list = AssetApproveDetail.objects.filter(
            ~Q(is_pass=None) & Q(approver_id=user_id)).order_by("-create_time")
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


class AssetTransferView(LoginRequiredMixin, View):
    """
    资产转移
    """

    def get(self, request):
        ret = dict()
        asset_id = request.GET.get("id")
        asset = AssetInfo.objects.get(id=asset_id)
        ret["asset"] = asset
        user_id = request.session.get("_auth_user_id")
        department_list = department_admin(user_id)
        ret["department_list"] = department_list
        return render(request, "adm/layer/asset_transfer.html", ret)

    def post(self, request):
        ret = dict()
        user_id = request.session.get('_auth_user_id')
        asset_id = request.POST.get("id0")
        asset = AssetInfo.objects.get(id=asset_id)
        department0 = asset.department
        warehouse0 = asset.warehouse
        department1 = Structure.objects.get(id=int(request.POST.get("department1")))
        warehouse1 = AssetWarehouse.objects.get(id=int(request.POST.get("warehouse1")))

        # 创建相应的在用物资
        use_quantity = request.POST.get('quantity')
        asset.quantity = int(asset.quantity) - int(use_quantity)
        if int(asset.quantity) == 0:
            asset.is_delete = True
        asset.save()
        use_asset = asset
        use_asset.id = None
        use_asset.save()
        use_asset.create_time = asset.create_time
        use_asset.quantity = int(use_quantity)
        use_asset.status = '1'
        use_asset.user_id = request.session.get('_auth_user_id')
        use_asset.is_delete = False
        use_asset.save()

        # 创建记录单
        asset_order = AssetApprove()
        asset_order.proposer_id = user_id
        asset_order.asset_id = asset_id
        asset_order.quantity = use_quantity
        asset_order.purpose = "将" + use_quantity + asset.unit + " '" + asset.name + "' 由 '" + asset.department.title + " - " + asset.warehouse.name + "' 仓库转移至 '" + department1.title + " - " + warehouse1.name + "' 仓库"
        asset_order.return_date = request.POST.get('use_time')
        asset_order.status = '0'
        asset_order.use_status = '0'
        asset_order.type = "1"
        asset_order.transfer_department = department1
        asset_order.transfer_warehouse = warehouse1
        asset_order.save()

        # 添加审批
        approver_list = department1.adm_list.split(",")
        for i in range(len(approver_list)):
            approver_list[i] = int(approver_list[i])
        verifier_list = warehouse0.verifier.all()
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
        ret['status'] = "success"
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type="application/json")


class FileUpload(LoginRequiredMixin, View):
    """
    档案上传
    """
    def get(self, request):
        ret = dict()
        type0 = request.GET.get("type")
        ret["type0"] = type0
        users = User.objects.filter(is_active="1")
        ret["users"] = users
        return render(request, "adm/files/file_upload.html", ret)

    def post(self, request):
        file0 = request.FILES.get("file_content", None)
        user_id = request.session.get("_auth_user_id")
        type0 = request.POST.get("type0")
        type1 = FileType.objects.filter(id=type0).first()
        if not file0:
            return HttpResponse("没有上传文件")
        number = request.POST.get("number", None)
        preserver = request.POST.get("preserver")
        file_manage = FileManage()
        file_manage.name = file0.name
        file_manage.content = file0
        if type1:
            file_manage.type = type1
        else:
            file_manage.type = None
        file_manage.uploader_id = user_id
        if number:
            file_manage.number = number
        file_manage.preserver_id = preserver
        file_manage.save()
        return HttpResponse("上传成功")


class FileList(LoginRequiredMixin, View):
    """
    文件列表
    """
    def get(self, request):
        ret = dict()
        type0 = request.GET.get("type")
        if type0:
            ret["type0"] = type0
            ret["type1"] = type0
        else:
            ret["type0"] = ""
            ret["type1"] = "-1"
        return render(request, "adm/files/file_list.html", ret)

    def post(self, request):
        # 获取资产列表
        fields = ['id', 'name', 'upload_time', 'content', 'number', 'preserver__name']
        type0 = request.POST.get("type0")
        if type0:
            ret = dict(data=list(FileManage.objects.values(*fields).filter(is_delete=False, type_id=type0).order_by("-upload_time")))
        else:
            ret = dict(data=list(FileManage.objects.values(*fields).filter(is_delete=False, type_id=None).order_by("-upload_time")))
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type="application/json")


class FileRename(LoginRequiredMixin, View):
    """
    文件重命名与修改类型
    """
    def get(self, request):
        ret = dict()
        id0 = request.GET.get("id")
        file = FileManage.objects.filter(id=id0).first()
        ret["file0"] = file
        types = FileType.objects.all()
        ret["types"] = types
        users = User.objects.filter(is_active="1")
        ret["users"] = users
        return render(request, "adm/files/file_rename.html", ret)

    def post(self, request):
        ret = dict()
        id0 = request.POST.get("id")
        name = request.POST.get("name0")
        type0 = request.POST.get("type0")
        number = request.POST.get("number")
        preserver = request.POST.get("preserver")
        file = FileManage.objects.filter(id=id0).first()
        path = "media/file_manage/" + str(file.name)
        new_path = "media/file_manage/" + name
        os.rename(path, new_path)
        file.name = name
        file.type_id = type0
        if number:
            file.number = number
        file.preserver_id = preserver
        file.save()
        ret["status"] = "success"
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type="application/json")


class FileDelete(LoginRequiredMixin, View):
    """
    文件删除
    """
    def post(self, request):
        ret = dict()
        user_id = request.session.get("_auth_user_id")
        id0 = request.POST.get("id")
        file = FileManage.objects.filter(id=id0).first()
        if file:
            path = "media/file_manage/" + str(file.name)
            os.remove(path)
            file.deleter_id = user_id
            file.is_delete = True
            file.delete_time = datetime.now()
            file.save()
            ret["result"] = True
        else:
            ret["result"] = False
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type="application/json")


class SetFileType(LoginRequiredMixin, View):
    """
    设置文件类型
    """
    def get(self, request):
        ret = dict()
        file_types = FileType.objects.all()
        ret["file_types"] = file_types
        return render(request, "adm/files/file_type.html", ret)

    def post(self, request):
        ret = dict()
        title = request.POST.get("title")
        file_type = FileType()
        file_type.name = title
        file_type.save()
        file_manage_menu = Menu.objects.filter(title="档案管理").first()
        menu = Menu()
        menu.title = title
        menu.parent = file_manage_menu
        menu.code = "FILE-LIST" + str(file_type.id)
        menu.url = "/adm/file_list/?type=" + str(file_type.id)
        menu.save()
        role = Role.objects.filter(title="能力：档案管理").first()
        role.permissions.add(menu.id)
        ret["status"] = "success"
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type="application/json")


class FileTypeAjax(LoginRequiredMixin, View):
    """
    文件类型ajax
    """
    def get(self, request):
        """
        文件类型重命名
        :param request:
        :return:
        """
        ret = dict()
        id0 = request.GET.get("id")
        name = request.GET.get("title")
        file_type = FileType.objects.filter(id=id0).first()
        file_type.name = name
        file_type.save()
        menu_code = "FILE-LIST" + str(id0)
        menu = Menu.objects.filter(code=menu_code).first()
        menu.title = name
        menu.save()
        ret["status"] = "success"
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type="application/json")

    def post(self, request):
        """
        文件类型删除
        :param request:
        :return:
        """
        ret = dict()
        id0 = request.POST.get("id")
        status = request.POST.get("status")
        user_id = request.session.get("_auth_user_id")
        file_list = FileManage.objects.filter(type_id=id0)
        if status == "0":
            for file in file_list:
                path = "media/file_manage/" + str(file.name)
                os.remove(path)
                file.deleter_id = user_id
                file.is_delete = True
                file.delete_time = datetime.now()
                file.save()
        elif status == "1":
            for file in file_list:
                file.type_id = None
                file.save()
        menu_code = "FILE-LIST" + str(id0)
        menu = Menu.objects.filter(code=menu_code).first()
        menu.delete()
        file_type = FileType.objects.filter(id=id0).first()
        file_type.delete()
        ret["status"] = "success"
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type="application/json")