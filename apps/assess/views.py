import json

from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.
from django.views import View

from assess.models import AssessDepDetail, AssessPerDetail
from users.models import Structure
from utils.mixin_utils import LoginRequiredMixin


class AssessDep(LoginRequiredMixin, View):
    """
    部门列表
    """
    def get(self, request):
        ret = dict()
        department = Structure.objects.filter(~Q(id="16"))
        ret['department'] = department
        return render(request, "assess/assess-dep.html", ret)


class AssessDetail(LoginRequiredMixin, View):
    """
    考核内容表格
    """
    def get(self, request):
        # 部门目标
        ret = dict()
        department_id = request.GET.get("id")
        department = Structure.objects.get(id=department_id)
        user_id = request.session.get("_auth_user_id")
        if department.adm_list and user_id in department.adm_list:
            ret["is_adm"] = "1"
        if department.userprofile_set.filter(id=user_id):
            ret["is_mem"] = "1"
        assess_dep_detail = AssessDepDetail.objects.filter(department_id=department_id).first()
        if assess_dep_detail:
            assess_dep_content = assess_dep_detail.content.split("\n")
            ret['assess_dep_content'] = assess_dep_content

            per_goal = AssessPerDetail.objects.filter(dep_goal_id=assess_dep_detail.id).order_by("principal_id")
            ret["per_goal"] = per_goal
        ret['department'] = department
        ret['assess_dep_detail'] = assess_dep_detail

        return render(request, "assess/assess-detail.html", ret)



class CreateGoal(LoginRequiredMixin, View):
    """
    新建部门目标
    """
    def get(self, request):
        ret = dict()
        id0 = request.GET.get("id")
        ret["id0"] = id0
        return render(request, "assess/create_goal.html", ret)

    def post(self, request):
        ret = dict()
        id0 = request.POST.get("id0")
        year = request.POST.get("year")
        month = request.POST.get("month")
        content = request.POST.get("detail")
        assess_dep_detail = AssessDepDetail()
        assess_dep_detail.department_id = id0
        assess_dep_detail.year = year
        assess_dep_detail.month = month
        assess_dep_detail.content = content
        assess_dep_detail.is_done = True
        assess_dep_detail.save()
        ret['status'] = "1"
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type="application/json")


class CreatePerGoal(LoginRequiredMixin, View):
    """
    新建个人目标
    """
    def get(self, request):
        ret = dict()
        id0 = request.GET.get("id")
        ret["id0"] = id0
        year = request.GET.get("year")
        month = request.GET.get("month")
        dep_goal = AssessDepDetail.objects.filter(id=id0, year=year, month=month).first()
        ret["dep_goal"] = dep_goal
        dep_goal_list = dep_goal.content.split("\n")
        ret["dep_goal_list"] = dep_goal_list
        return render(request, "assess/create_per_goal.html", ret)

    def post(self, request):
        ret = dict()
        goal_id = request.POST.get("id0")
        detail = request.POST.get("detail")
        user_id = request.session.get("_auth_user_id")
        detail_list = detail.split("\n")
        for d in detail_list:
            per_goal = AssessPerDetail()
            per_goal.dep_goal_id = goal_id
            per_goal.principal_id = user_id
            per_goal.content = d
            per_goal.save()
        ret["status"] = "1"

        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type="application/json")

