import json
import os

from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.
from django.views import View

from assess.models import AssessDepDetail, AssessPerDetail, AssessScore, PositionStatement
from users.models import Structure, UserProfile
from utils.mixin_utils import LoginRequiredMixin


class AssessDep(LoginRequiredMixin, View):
    """
    部门列表
    """
    def get(self, request):
        ret = dict()
        department = Structure.objects.filter(~Q(id="16"), ~Q(title="董事长"), ~Q(title="总经理"), ~Q(title="副总经理"), ~Q(title="总部"), ~Q(title="电力工程"), ~Q(title="测试"),)
        ret['department'] = department
        position_statement = PositionStatement.objects.all()
        ret['position_statement'] = position_statement
        ps_list = set()
        for ps in position_statement:
            ps_list.add(ps.department_id)
        ps_list = list(ps_list)
        ret['ps_list'] = ps_list
        return render(request, "assess/assess-dep.html", ret)


class AssessDetail(LoginRequiredMixin, View):
    """
    考核内容表格
    """
    def get(self, request):
        # 部门目标
        ret = dict()
        department_id = request.GET.get("id")
        year = request.GET.get("year")
        month = request.GET.get("month")
        department = Structure.objects.get(id=department_id)
        user_id = request.session.get("_auth_user_id")
        if (department.adm_list and user_id in department.adm_list) or department.vice_manager_id == int(user_id):
            ret["is_adm"] = "1"
        if department.userprofile_set.filter(id=user_id):
            ret["is_mem"] = "1"
        if department.vice_manager_id == int(user_id):
            ret["is_vice"] = "1"
        assess_dep_detail = AssessDepDetail.objects.filter(department_id=department_id, year=year, month=month).first()
        if assess_dep_detail:
            assess_dep_content = assess_dep_detail.content.split("\n")
            ret['assess_dep_content'] = assess_dep_content

            per_goal = AssessPerDetail.objects.filter(dep_goal_id=assess_dep_detail.id).order_by("id", "principal_id")
            ret["per_goal"] = per_goal
        ret['department'] = department
        ret['assess_dep_detail'] = assess_dep_detail

        # 判断当前是否存在个人目标
        was_submit = AssessPerDetail.objects.filter(dep_goal_id=assess_dep_detail.id)
        if was_submit:
            ret["was_submit"] = "1"

        # 分数汇总
        score_list = AssessScore.objects.filter(Q(dep_goal_id=assess_dep_detail.id), ~Q(total_score=None))
        if score_list:
            ret["score_list"] = score_list
            score_count = AssessScore.objects.filter(Q(dep_goal_id=assess_dep_detail.id))
            if len(score_list) == len(score_count):
                ret["score_done"] = "1"
                ret["dep_goal_id"] = assess_dep_detail.id

        # 判断审核完成
        if assess_dep_detail.is_done:
            ret["finish"] = "1"

        return render(request, "assess/assess-detail.html", ret)

    def post(self, request):
        """
        审核
        :param request:
        :return:
        """
        ret = dict()
        dep_goal_id = request.POST.get("dep_goal_id")
        user_id = request.session.get("_auth_user_id")
        dep_goal = AssessDepDetail.objects.filter(id=dep_goal_id).first()
        dep_goal.is_done = True
        dep_goal.verifier_id = user_id
        dep_goal.save()
        ret["success"] = "1"
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type="application/json")


class CreateGoal(LoginRequiredMixin, View):
    """
    新建部门目标
    """
    def get(self, request):
        ret = dict()
        id0 = request.GET.get("id")
        ret["id0"] = id0

        year = request.GET.get("year")
        month = request.GET.get("month")
        dep_goal = AssessDepDetail.objects.filter(department_id=id0, year=year, month=month).first()
        if dep_goal:
            ret["saved_dep_goal"] = dep_goal
        return render(request, "assess/create_goal.html", ret)

    def post(self, request):
        ret = dict()
        id0 = request.POST.get("id0")
        year = request.POST.get("year")
        month = request.POST.get("month")
        content = request.POST.get("detail")
        dep_goal = AssessDepDetail.objects.filter(department_id=id0, year=year, month=month).first()
        if dep_goal:
            assess_dep_detail = dep_goal
        else:
            assess_dep_detail = AssessDepDetail()
            assess_dep_detail.department_id = id0
            assess_dep_detail.year = year
            assess_dep_detail.month = month
        assess_dep_detail.content = content
        assess_dep_detail.is_done = False
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

        status = request.GET.get("status")
        ret["status"] = status
        if status == "0":
            department = dep_goal.department
            users = department.userprofile_set.filter(is_active="1")
            ret["users"] = users
        elif status == "1":
            user_id = request.session.get("_auth_user_id")
            ret["user_id"] = user_id
        return render(request, "assess/create_per_goal.html", ret)

    def post(self, request):
        ret = dict()
        goal_id = request.POST.get("id0")
        detail = request.POST.get("detail")
        user_id = request.POST.get("user_id")
        per_goals = AssessPerDetail.objects.filter(dep_goal_id=goal_id, principal_id=user_id)
        if per_goals:
            per_goals.delete()
        detail_list = detail.split("\n")
        for d in detail_list:
            per_goal = AssessPerDetail()
            per_goal.dep_goal_id = goal_id
            per_goal.principal_id = user_id
            per_goal.content = d
            per_goal.save()
        ret["status"] = "1"

        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type="application/json")


class EditSchedule(LoginRequiredMixin, View):
    """
    填写完成情况
    """
    def get(self, request):
        ret = dict()
        dep_goal_id = request.GET.get("id")
        dep_goal = AssessDepDetail.objects.filter(id=dep_goal_id).first()
        department = Structure.objects.filter(id=dep_goal.department_id).first()
        status = request.GET.get("st")
        ret["status"] = status
        if status == "0":
            user_list = department.userprofile_set.filter(is_active="1")
            goal_list = []
            for user in user_list:
                per_goal = AssessPerDetail.objects.filter(principal_id=user.id, dep_goal_id=dep_goal_id).order_by("id")
                if len(per_goal) != 0:
                    goal_list.append({user.name: per_goal})
            ret['goal_list'] = goal_list
        elif status == "1":
            user_id = request.session.get("_auth_user_id")
            per_goal = AssessPerDetail.objects.filter(principal_id=user_id, dep_goal_id=dep_goal_id).order_by("id")
            ret['goal_list'] = per_goal
        ret['dep_goal_id'] = dep_goal_id
        return render(request, "assess/edit_schedule.html", ret)

    def post(self, request):
        ret = dict()
        idArr = request.POST.getlist("p_goal_id")
        numArr = request.POST.getlist("numArr")
        contentArr = request.POST.getlist("contentArr")
        for i in range(len(idArr)):
            per_goal = AssessPerDetail.objects.filter(id=idArr[i]).first()
            per_goal.complete_degree = numArr[i]
            per_goal.describe = contentArr[i]
            per_goal.save()
        ret["status"] = "1"
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type="application/json")


class AssessScore0(LoginRequiredMixin, View):
    """
    评分
    """
    def get(self, request):
        ret = dict()
        dep_goal_id = request.GET.get("id")
        ret["dep_goal_id"] = dep_goal_id
        per_goal = AssessPerDetail.objects.filter(dep_goal_id=dep_goal_id)
        if per_goal:
            users = set()
            for i in per_goal:
                users.add(i.principal)
            ret["users"] = users
        else:
            ret["is_null"] = 1

        scores = AssessScore.objects.filter(dep_goal_id=dep_goal_id)
        ret["scores"] = scores
        return render(request, "assess/assess_score.html", ret)

    def post(self, request):
        ret = dict()
        targetArr = request.POST.getlist("targetArr")
        principal_id = request.POST.getlist("principal_id")
        abilityArr = request.POST.getlist("abilityArr")
        attitudeArr = request.POST.getlist("attitudeArr")
        remarkArr = request.POST.getlist("remarkArr")
        dep_goal_id = request.POST.get("dep_goal_id")
        for i in range(len(principal_id)):
            per_goal = AssessScore.objects.filter(dep_goal_id=dep_goal_id, principal_id=principal_id[i]).first()
            if per_goal:
                pass
            else:
                per_goal = AssessScore()
                per_goal.dep_goal_id = dep_goal_id
                per_goal.principal_id = principal_id[i]
            if targetArr[i]:
                per_goal.goal_score = float(targetArr[i])
            if abilityArr[i]:
                per_goal.capacity_score = float(abilityArr[i])
            if attitudeArr[i]:
                per_goal.attitude_score = float(attitudeArr[i])
            if targetArr[i] and abilityArr[i] and attitudeArr[i]:
                per_goal.total_score = float(targetArr[i]) + float(abilityArr[i]) + float(attitudeArr[i])
            per_goal.remark = remarkArr[i]
            per_goal.save()
        ret["status"] = "1"

        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type="application/json")


class YearMonth(LoginRequiredMixin, View):
    """
    选择对应年月的目标
    """
    def get(self, request):
        ret = dict()
        dep_id = request.GET.get("id")
        dep_goal = AssessDepDetail.objects.filter(department_id=dep_id)
        department = Structure.objects.filter(id=dep_id).first()
        ret["dep_goal"] = dep_goal
        ret["department"] = department
        user_id = request.session.get("_auth_user_id")
        if department.adm_list and user_id in department.adm_list:
            ret["is_adm"] = "1"
        return render(request, "assess/year_month.html", ret)


class PositionStatementList(LoginRequiredMixin, View):
    """
    部门岗位职责列表
    """
    def get(self, request):
        ret = dict()
        return render(request, "assess/position_statement_list.html", ret)

    def post(self, request):
        fields = ['id', 'name', 'department__title', 'file']
        ret = dict(data=list(PositionStatement.objects.values(*fields).all()))
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type="application/json")


class PositionStatementCreate(LoginRequiredMixin, View):
    """
    部门岗位职责创建
    """
    def get(self, request):
        ret = dict()
        departments = Structure.objects.all()
        ret["departments"] = departments
        return render(request, "assess/positon_statement_create.html", ret)

    def post(self, request):
        ret = dict()
        name = request.POST.get("title")
        department = request.POST.get("department")
        file0 = request.FILES.get("file_content", None)
        position = PositionStatement()
        position.name = name
        position.department_id = department
        position.file = file0
        position.save()
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type="application/json")


class PositionStatementAjax(LoginRequiredMixin, View):
    """
    部门岗位职责ajax
    """
    def get(self, request):
        return

    def post(self, request):
        """
        岗位职责删除
        :param request:
        :return:
        """
        ret = dict()
        id0 = request.POST.get("id")
        position = PositionStatement.objects.filter(id=id0).first()
        path = "media/" + str(position.file)
        os.remove(path)
        position.delete()
        ret["status"] = "1"
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type="application/json")


class AssessGather(LoginRequiredMixin, View):
    """
    考核汇总日期列表
    """
    def get(self, request):
        ret = dict()
        dep_goals = AssessDepDetail.objects.all()
        date_list = set()
        for d in dep_goals:
            date = (d.year, d.month)
            date_list.add(date)
        date_list = list(date_list)
        date_list.sort()
        ret["date_list"] = date_list
        return render(request, "assess/year_month_total.html", ret)


class AssessGatherList(LoginRequiredMixin, View):
    """
    考核汇总列表
    """
    def get(self, request):
        ret = dict()
        year = request.GET.get("year")
        month = request.GET.get("month")
        ret["year"] = year
        ret["month"] = month
        return render(request, "assess/gather_list.html", ret)

    def post(self, request):
        year = request.POST.get('year')
        month = request.POST.get('month')
        field = ['principal__name', 'goal_score', 'capacity_score', 'attitude_score', 'total_score', 'remark', 'dep_goal__is_done']
        ret = dict(data=list(AssessScore.objects.values(*field).filter(dep_goal__year=year, dep_goal__month=month)))
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type="application/json")


