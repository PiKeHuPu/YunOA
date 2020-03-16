import json
from datetime import datetime

from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q
from django.http import HttpResponse, request
from django.shortcuts import render, get_object_or_404

# Create your views here.
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View

from users.models import UserProfile, Structure
from .models import Worklog, WorklogPart, User


class WorkLog_Show(LoginRequiredMixin, View):
    def get(self, request):
        ret = dict()
        department = Structure.objects.all()
        ret['department'] = department
        id = request.session.get("_auth_user_id")
        return render(request, 'work/worklog_show.html', ret)

    def post(self,request):
        mon = datetime.now().month
        year = datetime.now().year
        day = datetime.now().day

        fields = [ "worklog", "status", "reason", "create_time",
                  "depart_id__title", "id", "plan_status"]
        filters = dict()

        if request.POST.get('status'):
            filters['status'] = request.POST.get('status')
        if request.POST.get('department'):
            filters['depart_id__title'] = request.POST.get('department')
        if request.POST.get("start_time"):
            start_time = request.POST.get("start_time").split("-")
            filters['create_time__year'] = start_time[0]
            filters['create_time__month'] = start_time[1]
            filters['create_time__day'] = start_time[2]
            ret = (dict(data=list(Worklog.objects.filter(**filters).values(*fields))))
        else:
            ret = (dict(data=list(Worklog.objects.filter(Q(create_time__year=year, create_time__month=mon, create_time__day=day)
                                                 | (Q(status=0) & Q(create_time__lt=datetime(year, mon, day)))
                                                 | Q(over_time__year=year, over_time__month=mon, over_time__day=day),
                                                 **filters).values(*fields).order_by('create_time'))))
        # x = list(Worklog.objects.filter(Q(create_time__year=year, create_time__month=mon, create_time__day=day)
        #                                 | (Q(status=0) & Q(create_time__lt=datetime(year, mon, day)))
        #                                 | Q(over_time__year=year, over_time__month=mon, over_time__day=day),
        #                              **filters).values(*fields).order_by('create_time'))
        #今天创建的日志
        # x = list(Worklog.objects.filter(create_time__year=year, create_time__month=mon, create_time__day=day,
        #                                 **filters).values(*fields).order_by('create_time'))
        # # 创建日期早于今天的未完成日志
        # y = list(Worklog.objects.filter(Q(status=0), Q(create_time__lt=datetime(year, mon, day)), **filters).values(
        #     *fields).order_by('create_time'))
        # # 今天完成之前未完成的日志
        # z = list(
        #     Worklog.objects.filter(Q(over_time__year=year, over_time__month=mon, over_time__day=day),
        #                            **filters).values(*fields).order_by('create_time'))
        # ret = (dict(data=x + y + z))
        # ret =(dict(data=list(Worklog.objects.filter(Q(create_time__year=year, create_time__month=mon, create_time__day=day)
        #                                 | (Q(status=0) & Q(create_time__lt=datetime(year, mon, day)))
        #                                 | Q(over_time__year=year, over_time__month=mon, over_time__day=day),
        #                                 **filters).values(*fields).order_by('create_time'))))
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type='application/json')


class WorkLog_Create(LoginRequiredMixin, View):
    def get(self, requset):
        ret = dict()

        return render(requset, 'work/worklog_create.html', ret)

    def post(self, request):
        res = dict()

        worklog = request.POST.get("worklog")
        status = request.POST.get("status")
        reason = request.POST.get("reason")
        creman = request.session.get("_auth_user_id")
        depart_id = UserProfile.objects.filter(id=creman)[0].department_id
        adm_work_list = Structure.objects.filter(id = depart_id)[0].adm_work
        adm_work_id = adm_work_list.split(",")
        if creman in adm_work_id:

            worklg = Worklog()
            # if status == 0:
            #     worklg.reason = ''
            # else:
            #     worklg.reason = reason

            worklg.reason = reason
            worklg.worklog = worklog
            worklg.status = status
            worklg.cre_man_id = creman
            worklg.depart_id = depart_id
            worklg.save()
            res["result"] = True
        else:
            res["result"] = False
        return HttpResponse(json.dumps(res), content_type='application/json')

class WorkLog_Edit(LoginRequiredMixin,View):
    def get(self,request):
        ret = dict()
        id = request.GET.get("id")
        worklog = Worklog.objects.filter(id=id)[0]
        logpart = WorklogPart.objects.filter(worklog_part_id=id)
        task_detail = WorklogPart.objects.filter(worklog_part_id=id)

        ret = {
            'worklog': worklog,
            'task_detail': task_detail,
            'logpart': logpart
        }
        return render(request, "work/worklog_edit.html", ret)
    def post(self,request):
        res = dict()
        creman = request.session.get("_auth_user_id")
        id = request.POST.get("id")
        sta = request.POST.get("status")
        task_detail = request.POST.get("task_detail")
        #creman = request.session.get("_auth_user_id")
        #depart_id = UserProfile.objects.filter(id=creman)[0].department_id
        worklog = Worklog.objects.filter(id=id)[0]
        creman = request.session.get("_auth_user_id")
        depart_id = UserProfile.objects.filter(id=creman)[0].department_id
        adm_work_list = Structure.objects.filter(id=depart_id)[0].adm_work
        adm_work_id = adm_work_list.split(",")
        if creman in adm_work_id:
            if str(sta) == str(worklog.status) and int(worklog.cre_man_id) == int(creman):
                logpart = WorklogPart()
                logpart.task_detail = task_detail
                logpart.worklog_part_id = id
                logpart.save()
                Worklog.objects.filter(id=id).update(plan_status="1")
                res["result"] = True
            elif int(sta) == 1 and int(worklog.cre_man_id) == int(creman):
                #worklog = Worklog.objects.filter(id=id)[0]
                Worklog.objects.filter(id=id).update(status=sta)
                Worklog.objects.filter(id=id).update(over_time=datetime.now())
                Worklog.objects.filter(id=id).update(plan_status="1")
                logpart = WorklogPart()
                logpart.task_detail = task_detail
                logpart.worklog_part_id = id
                logpart.save()
                res["result"] = True
            elif int(sta) == 555 and int(worklog.cre_man_id) == int(creman):
                # worklog = Worklog.objects.filter(id=id)[0]
                # worklog.status = sta
                # worklog.over_time = datetime.now()
                # worklog.save()
                Worklog.objects.filter(id=id).update(status=sta)
                Worklog.objects.filter(id=id).update(over_time=datetime.now())
                Worklog.objects.filter(id=id).update(plan_status="1")
                logpart = WorklogPart()
                logpart.task_detail = task_detail
                logpart.worklog_part_id = id
                logpart.save()
                res["result"] = True
        else:
            res["result"] = False
        return HttpResponse(json.dumps(res), content_type='application/json')


class WorkLog_Detail(LoginRequiredMixin, View):
    def get(self,request):
        ret = dict()
        id = request.GET.get("id")


        worklog = Worklog.objects.filter(id=id)[0]

        logpart = WorklogPart.objects.filter(worklog_part_id=id)
        task_detail = WorklogPart.objects.filter(worklog_part_id=id)

        ret = {

            'worklog': worklog,

            'task_detail': task_detail,
            'logpart': logpart
        }
        return render(request, 'work/worklog_detail.html', ret)


class WorkLog_Set(LoginRequiredMixin, View):
    def get(self, request):
        if 'id' in request.GET and request.GET['id']:
            structure = get_object_or_404(Structure, pk=int(request.GET.get('id')))
            try:
                adm_work = structure.adm_work.split(",")
            except:
                adm_work = []
            added_adms = User.objects.filter(id__in=adm_work)
            all_adms = User.objects.exclude(username='admin')
            un_add_adms = set(all_adms).difference(added_adms)
            ret = dict(structure=structure, added_users=added_adms, un_add_users=list(un_add_adms))

        else:
            ret = dict()
        return render(request, 'work/worklog_setwrite.html', ret)

    def post(self, request):
        res = dict(result=False)
        id_list = None
        structure = get_object_or_404(Structure, pk=int(request.POST.get('id')))
        if 'to' in request.POST and request.POST['to']:
            id_list = request.POST.getlist('to', [])
        if id_list:
            adm_work = ",".join(id_list)
            structure.adm_work = adm_work
        else:
            structure.adm_work = None

        structure.save()
        res['result'] = True
        return HttpResponse(json.dumps(res), content_type='application/json')