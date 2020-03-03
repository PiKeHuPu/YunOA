import json

from django.contrib.auth import get_user_model
from django.shortcuts import render
from django.shortcuts import get_object_or_404

User = get_user_model()

from django.views.generic.base import View
from django.http import HttpResponse
from django.core.serializers.json import DjangoJSONEncoder

from .forms import StructureUpdateForm
from utils.mixin_utils import LoginRequiredMixin
from users.models import Structure, UserProfile
from rbac.models import Menu, Role
from system.models import SystemSetup


class StructureView(LoginRequiredMixin, View):
    """
    组织架构管理
    """

    def get(self, request):
        ret = Menu.getMenuByRequestUrl(url=request.path_info)
        ret.update(SystemSetup.getSystemSetupLastData())
        return render(request, 'system/structure/structure-list.html', ret)


class StructureListView(LoginRequiredMixin, View):
    """
    获取组织架构数据列表
    """

    def get(self, request):
        fields = ['id', 'title', 'type', 'parent__title', 'adm_list', "vice_manager__name"]
        ret = dict(data=list(Structure.objects.values(*fields)))
        # print(ret)
        for data in ret["data"]:
            department = Structure.objects.get(id=data["id"])
            administrators = department.userprofile_set.filter(is_dep_administrator=True)
            administrators_str = ""
            for i in range(len(administrators)):
                if i == 3:
                    administrators_str += "..."
                    break
                administrators_str += administrators[i].name
                if i != len(administrators) - 1 and i != 2:
                    administrators_str += ","
            data["asset_adm_list"] = administrators_str

            try:
                adm_id = data["adm_list"].split(",")
            except:
                adm_id = []
            adm_name = User.objects.values("name").filter(id__in=adm_id)
            adm_list = ",".join([n["name"] for n in adm_name])
            data["adm_list"] = adm_list
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type='application/json')


class StructureDetailView(LoginRequiredMixin, View):
    """
    组织架构详情页：查看、修改、新建数据
    """

    def get(self, request):
        ret = dict()
        if 'id' in request.GET and request.GET['id']:
            structure = get_object_or_404(Structure, pk=request.GET.get('id'))
            structures = Structure.objects.exclude(id=request.GET.get('id'))
            ret['structure'] = structure

        else:
            structures = Structure.objects.all()
        ret['structures'] = structures
        return render(request, 'system/structure/structure_detail.html', ret)

    def post(self, request):
        res = dict(result=False)
        if 'id' in request.POST and request.POST['id']:
            structure = get_object_or_404(Structure, pk=request.POST.get('id'))
        else:
            structure = Structure()
        structure_update_form = StructureUpdateForm(request.POST, instance=structure)
        if structure_update_form.is_valid():
            structure_update_form.save()
            res['result'] = True
        return HttpResponse(json.dumps(res), content_type='application/json')


class StructureDeleteView(LoginRequiredMixin, View):
    """
    删除数据：支持删除单条记录和批量删除
    """

    def post(self, request):
        ret = dict(result=False)
        if 'id' in request.POST and request.POST['id']:
            id_list = map(int, request.POST.get('id').split(','))
            Structure.objects.filter(id__in=id_list).delete()
            ret['result'] = True
        return HttpResponse(json.dumps(ret), content_type='application/json')


class Structure2UserView(LoginRequiredMixin, View):
    """
    组织架构关联用户
    """

    def get(self, request):
        if 'id' in request.GET and request.GET['id']:
            structure = get_object_or_404(Structure, pk=int(request.GET.get('id')))
            added_users = structure.userprofile_set.all()
            all_users = User.objects.exclude(username='admin')
            un_add_users = set(all_users).difference(added_users)
            ret = dict(structure=structure, added_users=added_users, un_add_users=list(un_add_users))
        return render(request, 'system/structure/structure_user.html', ret)

    def post(self, request):
        res = dict(result=False)
        id_list = None
        structure = get_object_or_404(Structure, pk=int(request.POST.get('id')))
        if 'to' in request.POST and request.POST['to']:
            id_list = map(int, request.POST.getlist('to', []))
        structure.userprofile_set.clear()
        if id_list:
            for user in User.objects.filter(id__in=id_list):
                structure.userprofile_set.add(user)
        res['result'] = True
        return HttpResponse(json.dumps(res), content_type='application/json')


class StructureAdmView(LoginRequiredMixin, View):
    """
    组织架构添加部门负责人和分管副总
    """

    def get(self, request):
        if 'id' in request.GET and request.GET['id']:
            structure = get_object_or_404(Structure, pk=int(request.GET.get('id')))
            try:
                adm_list = structure.adm_list.split(",")
            except:
                adm_list = []
            added_adms = User.objects.filter(id__in=adm_list)
            all_adms = User.objects.exclude(username='admin')
            un_add_adms = set(all_adms).difference(added_adms)

            vice_managers = User.objects.filter(is_active="1")
            ret = dict(structure=structure, added_users=added_adms, un_add_users=list(un_add_adms),
                       vice_managers=vice_managers)
        else:
            ret = dict()
        return render(request, 'system/structure/structure-adm.html', ret)

    def post(self, request):
        res = dict(result=False)
        id_list = None
        structure = get_object_or_404(Structure, pk=int(request.POST.get('id')))
        if 'to' in request.POST and request.POST['to']:
            id_list = request.POST.getlist('to', [])
        if id_list:
            adm_list = ",".join(id_list)
            structure.adm_list = adm_list
        else:
            structure.adm_list = None

        vice_manager = request.POST.get("vice_manager")
        structure.vice_manager_id = vice_manager
        structure.save()
        res['result'] = True
        return HttpResponse(json.dumps(res), content_type='application/json')


class StructureAssetAdmView(LoginRequiredMixin, View):
    """
    设置物资管理员
    """

    def get(self, request):
        ret = dict()
        id0 = request.GET.get("id")
        department = Structure.objects.get(id=id0)
        added_users = department.userprofile_set.filter(is_dep_administrator=True)
        users = department.userprofile_set.filter(is_active="1")
        un_add_users = set(users).difference(added_users)
        ret['department'] = department
        ret['added_users'] = added_users
        ret['un_add_users'] = un_add_users
        return render(request, "adm/layer/department.html", ret)

    def post(self, request):
        ret = dict()
        id_list = None
        id0 = request.POST.get("id0")
        department = Structure.objects.get(id=id0)
        role = Role.objects.get(title="能力：仓库管理")
        dep_users = department.userprofile_set.filter(is_dep_administrator=True)
        for d in dep_users:
            role.userprofile_set.remove(d)

        if 'to' in request.POST and request.POST['to']:
            # print(request.POST.getlist('to', []))
            id_list = request.POST.getlist('to', [])
            users = User.objects.filter(id__in=id_list)
            for u in users:
                role.userprofile_set.add(u)

        department.userprofile_set.all().update(is_dep_administrator=False)
        if id_list:
            department.userprofile_set.filter(id__in=id_list).update(is_dep_administrator=True)
        if request.POST.get('admin') == 'on':
            department.super_adm = True
        else:
            department.super_adm = False
        department.save()
        ret['result'] = True
        return HttpResponse(json.dumps(ret), content_type='application/json')
