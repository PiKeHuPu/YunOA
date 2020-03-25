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
        return render(request, 'work/worklog_show.html', ret)

    def post(self,request):
        mon = datetime.now().month
        year = datetime.now().year
        day = datetime.now().day

        fields = [ "plan", "stage", "s_time", "e_time",
                  "performance", "id", "remark", "dutyman_id__name",
                   "content_part__content", "content_part__department__title"
                   , "is_done", "content_part__is_done", "content_part__step",
                   "content_part__department__id", "content_part_id"]
        filters = dict()

        if request.POST.get('status'):
            print(request.POST.get('status'))
            filters['content_part__is_done'] = request.POST.get('status')
        if request.POST.get('department'):
            filters['content_part__department__title'] = request.POST.get('department')
        if request.POST.get("start_time"):
            start_time = request.POST.get("start_time").split("-")
            filters['s_time__year'] = start_time[0]
            filters['s_time__month'] = start_time[1]
            filters['s_time__day'] = start_time[2]

        # x = list(Worklog.objects.filter(Q(create_time__year=year, create_time__month=mon, create_time__day=day)
        #                                 | (Q(status=0) & Q(create_time__lt=datetime(year, mon, day)))
        #                                 | Q(over_time__year=year, over_time__month=mon, over_time__day=day),
        #                              **filters).values(*fields).order_by('create_time'))
        # ret =(dict(data=list(Worklog.objects.filter(Q(create_time__year=year, create_time__month=mon, create_time__day=day)
        #                                 | (Q(status=0) & Q(create_time__lt=datetime(year, mon, day)))
        #                                 | Q(over_time__year=year, over_time__month=mon, over_time__day=day),
        #                                 **filters).values(*fields).order_by('create_time'))))
        ret = (dict(data=list(WorklogPart.objects.filter(**filters).values(*fields).order_by('content_part__content'))))
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type='application/json')


class WorkLog_Create(LoginRequiredMixin, View):
    def get(self, requset):
        ret = dict()
        depart = Structure.objects.all()
        dutyman = UserProfile.objects.filter(Q(is_active=1), ~Q(username='admin'),~Q(username='admin0'))
        ret['dutyman'] = dutyman
        ret['department'] = depart
        return render(requset, 'work/worklog_create.html', ret)

    def post(self, request):
        res = dict()
        try:
            creman = request.session.get("_auth_user_id")
            list1 = []
            # adm_work_id = adm_work_list.split(",")
            # if creman in adm_work_id:
            adm_work_list = Structure.objects.values("adm_work")
            for i in adm_work_list:
                x = []
                x.append(i['adm_work'])
                if x == None:
                    pass
                else:
                    if "," in x:
                        work_id = x.split(",")
                        list1 += work_id
                    else:
                        list1 += x
            #adm_work_id = adm_work_list.split(",")
            print(list1)

            if str(creman) in list1:
                content = request.POST.get("content")
                stage = request.POST.get("stage")
                department = request.POST.get("department")
                worklog = Worklog()
                worklog.content = content
                worklog.step = stage
                worklog.department_id = department
                worklog.save()
                logid = worklog.id
                is_done = []
                for i in range(1, int(stage)+1):
                    logpart = WorklogPart()
                    logpart.plan = request.POST.get('workplan' + str(i))
                    logpart.stage = i
                    logpart.is_done = request.POST.get('is_done' + str(i))
                    logpart.s_time = request.POST.get('start_time' + str(i))
                    logpart.e_time = request.POST.get('end_time' + str(i))
                    logpart.performance = request.POST.get('complete' + str(i))
                    logpart.remark = request.POST.get('remark' + str(i))
                    logpart.content_part_id = logid
                    logpart.dutyman_id = request.POST.get('dutyman' + str(i))
                    logpart.save()
                    if int(request.POST.get('is_done' + str(i))) == 1:
                        is_done.append(request.POST.get('is_done' + str(i)))

                if len(is_done) == int(stage):
                    Worklog.objects.filter(id=logid).update(is_done=True)
                else:
                    Worklog.objects.filter(id=logid).update(is_done=False)
                res['result'] = "1"
            else:
                res['result'] = "2"
        except Exception as e:
            res['result'] = e
        return HttpResponse(json.dumps(res, cls=DjangoJSONEncoder), content_type='application/json')

class WorkLog_Edit(LoginRequiredMixin,View):
    def get(self,request):
        ret = dict()
        id = request.GET.get("id")
        logpart = WorklogPart.objects.filter(id= id)[0]
        log_id = logpart.content_part_id
        content = Worklog.objects.filter(id=log_id)[0]
        dep = content.department_id
        stage = content.step
        content = content.content
        department = Structure.objects.all()
        dutyman = UserProfile.objects.filter(Q(is_active=1), ~Q(username='admin'), ~Q(username='admin0'))
        part = WorklogPart.objects.filter(content_part_id=log_id)
        ret['part'] = part
        ret['dutyman'] = dutyman
        ret['department'] = department
        ret['dep'] = dep
        ret['stage'] = stage
        ret['content'] = content
        ret['id'] = log_id

        return render(request, "work/worklog_edit.html", ret)
    def post(self,request):
        res = dict()
        #models.UserInfo.objects.filter(user='yangmv').update(pwd='520')
        logid = request.POST.get("id")
        Worklog.objects.filter(id=logid).update(department_id=request.POST.get("department"))
        stage = len(WorklogPart.objects.filter(content_part_id=logid))
        is_done = []
        creman = request.session.get("_auth_user_id")
        list1 = []
        # adm_work_id = adm_work_list.split(",")
        # if creman in adm_work_id:
        adm_work_list = Structure.objects.values("adm_work")
        for i in adm_work_list:
            x = []
            x.append(i['adm_work'])
            if x == None:
                pass
            else:
                if "," in x:
                    work_id = x.split(",")
                    list1.append(work_id)
                else:
                    list1.append(x)
        # adm_work_id = adm_work_list.split(",")

        if str(creman) in list1:
            for i in range(1, stage+1):
                WorklogPart.objects.filter(content_part_id=logid, stage=i).update(plan=request.POST.get('workplan' + str(i)))
                WorklogPart.objects.filter(content_part_id=logid, stage=i).update(is_done=request.POST.get('is_done' + str(i)))
                WorklogPart.objects.filter(content_part_id=logid, stage=i).update(s_time=request.POST.get('start_time' + str(i)))
                WorklogPart.objects.filter(content_part_id=logid, stage=i).update(e_time=request.POST.get('end_time' + str(i)))
                WorklogPart.objects.filter(content_part_id=logid, stage=i).update(performance=request.POST.get('complete' + str(i)))
                WorklogPart.objects.filter(content_part_id=logid, stage=i).update(remark=request.POST.get('remark' + str(i)))
                WorklogPart.objects.filter(content_part_id=logid, stage=i).update(dutyman_id=request.POST.get('dutyman' + str(i)))
                if int(request.POST.get('is_done' + str(i))) == 1:
                    is_done.append(int(request.POST.get('is_done' + str(i))))
            if len(is_done) == int(stage):

                Worklog.objects.filter(id=logid).update(is_done=True)
            else:
                Worklog.objects.filter(id=logid).update(is_done=False)
            res['result'] = True
        else:
            res['result'] = False
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

#设置填写人员
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