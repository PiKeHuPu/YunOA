import json

from django.contrib.auth import get_user_model
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic.base import View

from adm.models import AssetDepartment
from utils.mixin_utils import LoginRequiredMixin
from rbac.models import Menu
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