import json

from django.contrib.auth import get_user_model
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic.base import View

from adm.models import AssetDepartment, AssetWarehouse
from utils.mixin_utils import LoginRequiredMixin
from rbac.models import Menu, Role
from system.models import SystemSetup

User = get_user_model()


class AdmView(LoginRequiredMixin, View):
    """
    行政
    """
    def get(self, request):
        ret = Menu.getMenuByRequestUrl(url=request.path_info)
        ret.update(SystemSetup.getSystemSetupLastData())
        return render(request, 'adm/adm_index.html', ret)


class DepartmentManageView(LoginRequiredMixin, View):
    """
    资产部门管理
    """
    def get(self, request):
        ret = dict()
        assetDepartments = AssetDepartment.objects.filter(is_delete=False)
        ret["assetDepartments"] = assetDepartments
        return render(request, "adm/layer/department.html", ret)


class DepartmentCreateView(LoginRequiredMixin, View):
    """
    创建资产部门
    """
    def get(self, request):
        ret = dict()
        if request.GET.get("id"):
            assetDepartment = AssetDepartment.objects.get(id=request.GET.get("id"))
            ret['assetDepartment'] = assetDepartment
        users = User.objects.filter(is_active=1, is_staff=0)
        ret['users'] = users
        return render(request, "adm/layer/department_create.html", ret)

    def post(self, request):
        ret = dict()
        department_id = request.POST.get("id")
        name = request.POST.get("department")
        administrator = request.POST.get("operator")
        super_department = request.POST.get("admin").startswith("t")

        if name:
            if department_id:
                assetDepartment = AssetDepartment.objects.get(id=department_id)
            else:
                assetDepartment = AssetDepartment()
            assetDepartment.name = name
            assetDepartment.administrator_id = administrator
            assetDepartment.super_adm = super_department
            assetDepartment.save()

            if administrator:
                role = Role.objects.get(title="仓库管理")
                user = User.objects.get(id=administrator)
                role.userprofile_set.add(user)
            ret['result'] = True
        else:
            ret['result'] = False
        return HttpResponse(json.dumps(ret), content_type='application/json')


class DepartmentDeleteView(LoginRequiredMixin, View):
    """
    删除资产部门
    """
    def get(self, request):
        ret = dict()
        department_id = request.GET.get("id")
        assetDepartment = AssetDepartment.objects.get(id=department_id)
        assetDepartment.is_delete = True
        assetDepartment.save()
        ret['result'] = True
        return HttpResponse(json.dumps(ret), content_type='application/json')


class WarehouseView(LoginRequiredMixin, View):
    """
    资产仓库管理
    """
    def get(self, request):
        ret = dict()
        user_id = request.session.get("_auth_user_id")
        departments = AssetDepartment.objects.filter(administrator_id=user_id)
        for department in departments:
            if department.super_adm:
                department_list = AssetDepartment.objects.filter(is_delete=False)
                break
        else:
            department_list = departments

        warehouse_list = []
        for department in department_list:
            if department.assetwarehouse_set.filter(is_delete=False):
                for i in department.assetwarehouse_set.filter(is_delete=False):
                    warehouse_list.append(i)
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
        departments = AssetDepartment.objects.filter(is_delete=False, administrator_id=user_id)
        if departments:
            for department in departments:
                if department.super_adm:
                    department_list = AssetDepartment.objects.filter(is_delete=False)
                    break
            else:
                department_list = departments
        else:
            department_list = []
        ret["department_list"] = department_list
        return render(request, "adm/layer/warehouse_create.html", ret)

    def post(self, request):
        ret = dict()
        id = request.POST.get("id")
        name = request.POST.get("name")
        department_id = request.POST.get("department_id")
        remark = request.POST.get("remark")
        if name and department_id:
            if id:
                warehouse = AssetWarehouse.objects.get(id=id)
            else:
                warehouse = AssetWarehouse()
            warehouse.name = name
            warehouse.department_id = department_id
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
        warehouse.save()
        ret["result"] = True
        return HttpResponse(json.dumps(ret), content_type='application/json')