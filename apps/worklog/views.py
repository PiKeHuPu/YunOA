import json

from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q
from django.http import HttpResponse, request
from django.shortcuts import render, get_object_or_404

# Create your views here.
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View

from users.models import UserProfile, Structure
from .models import Worklog, WorklogPart, User, WorkRecordTem, WorkRecord

from datetime import datetime


class WorkLog_Show(LoginRequiredMixin, View):
    def get(self, request):
        ret = dict()
        department = Structure.objects.all()
        ret['departments'] = department
        users = UserProfile.objects.filter(is_active="1")
        ret['users'] = users
        user_id = request.session.get("_auth_user_id")
        ret["user_id"] = user_id
        return render(request, 'work/worklog_show.html', ret)

    def post(self, request):
        fields = ["plan", "stage", "s_time", "e_time",
                  "performance", "id", "remark", "dutyman_id__name",
                  "content_part__content", "department__title"
            , "is_done", "content_part__is_done", "content_part__step",
                  "department__id", "content_part_id", "content_part__cre_man_id"]
        filters = dict()

        if request.POST.get('status'):
            filters['content_part__is_done'] = request.POST.get('status')
        if request.POST.get('department'):
            filters['department__id'] = request.POST.get('department')
        if request.POST.get('duty_officer'):
            filters['dutyman_id'] = request.POST.get('duty_officer')
        if request.POST.get("start_time"):
            filters['s_time__gte'] = request.POST.get('start_time')
        if request.POST.get("end_time"):
            filters['s_time__lte'] = request.POST.get('end_time')

        # x = list(Worklog.objects.filter(Q(create_time__year=year, create_time__month=mon, create_time__day=day)
        #                                 | (Q(status=0) & Q(create_time__lt=datetime(year, mon, day)))
        #                                 | Q(over_time__year=year, over_time__month=mon, over_time__day=day),
        #                              **filters).values(*fields).order_by('create_time'))
        # ret =(dict(data=list(Worklog.objects.filter(Q(create_time__year=year, create_time__month=mon, create_time__day=day)
        #                                 | (Q(status=0) & Q(create_time__lt=datetime(year, mon, day)))
        #                                 | Q(over_time__year=year, over_time__month=mon, over_time__day=day),
        #                                 **filters).values(*fields).order_by('create_time'))))
        ret = (dict(data=list(WorklogPart.objects.filter(**filters).values(*fields).order_by('-content_part__id'))))
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type='application/json')


class WorkLog_Create(LoginRequiredMixin, View):
    """
    看板工作创建
    """

    def get(self, requset):
        ret = dict()
        depart = Structure.objects.all()
        dutyman = UserProfile.objects.filter(Q(is_active=1), ~Q(username='admin'), ~Q(username='admin0'))
        ret['dutyman'] = dutyman
        ret['department'] = depart
        return render(requset, 'work/worklog_create.html', ret)

    def post(self, request):
        res = dict()
        creman = request.session.get("_auth_user_id")
        list1 = []
        # adm_work_id = adm_work_list.split(",")
        # if creman in adm_work_id:
        adm_work_list = Structure.objects.values("adm_work").filter(~Q(adm_work=None))
        for i in adm_work_list:
            if "," in i["adm_work"]:
                work_id = i["adm_work"].split(",")
                list1 += work_id
            else:
                list1.append(i["adm_work"])
        # adm_work_id = adm_work_list.split(",")

        if str(creman) in list1:
            content = request.POST.get("content")
            stage = request.POST.get("stage")
            worklog = Worklog()
            worklog.content = content
            worklog.step = stage
            worklog.cre_man_id = creman
            worklog.save()
            logid = worklog.id
            is_done = []
            for i in range(1, int(stage) + 1):
                logpart = WorklogPart()
                logpart.plan = request.POST.get('workplan' + str(i))
                logpart.stage = i
                logpart.is_done = request.POST.get('is_done' + str(i))
                logpart.s_time = request.POST.get('start_time' + str(i))
                logpart.e_time = request.POST.get('end_time' + str(i))
                logpart.performance = request.POST.get('complete' + str(i))
                logpart.remark = request.POST.get('remark' + str(i))
                logpart.department_id = request.POST.get('department' + str(i))
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

        return HttpResponse(json.dumps(res, cls=DjangoJSONEncoder), content_type='application/json')


class WorkLog_Edit(LoginRequiredMixin, View):
    """
    看板工作修改
    """

    def get(self, request):
        ret = dict()
        id = request.GET.get("id")
        logpart = WorklogPart.objects.filter(id=id)[0]
        log_id = logpart.content_part_id
        content = Worklog.objects.filter(id=log_id)[0]
        content = content.content
        ret['content'] = content
        ret['id'] = id
        ret['logpart'] = logpart
        return render(request, "work/worklog_edit.html", ret)

    def post(self, request):
        res = dict()
        try:
            # #models.UserInfo.objects.filter(user='yangmv').update(pwd='520')
            # logid = request.POST.get("id")
            # Worklog.objects.filter(id=logid).update(department_id=request.POST.get("department"))
            # stage = len(WorklogPart.objects.filter(content_part_id=logid))
            # is_done = []
            creman = request.session.get("_auth_user_id")
            list1 = []
            # adm_work_id = adm_work_list.split(",")
            # if creman in adm_work_id:
            adm_work_list = Structure.objects.values("adm_work").filter(~Q(adm_work=None))
            for i in adm_work_list:
                if "," in i["adm_work"]:
                    work_id = i["adm_work"].split(",")
                    list1 += work_id
                else:
                    list1.append(i["adm_work"])
            if str(creman) in list1:
                #     for i in range(1, stage+1):
                #         WorklogPart.objects.filter(content_part_id=logid, stage=i).update(plan=request.POST.get('workplan' + str(i)))
                #         WorklogPart.objects.filter(content_part_id=logid, stage=i).update(is_done=request.POST.get('is_done' + str(i)))
                #         WorklogPart.objects.filter(content_part_id=logid, stage=i).update(s_time=request.POST.get('start_time' + str(i)))
                #         WorklogPart.objects.filter(content_part_id=logid, stage=i).update(e_time=request.POST.get('end_time' + str(i)))
                #         WorklogPart.objects.filter(content_part_id=logid, stage=i).update(performance=request.POST.get('complete' + str(i)))
                #         WorklogPart.objects.filter(content_part_id=logid, stage=i).update(remark=request.POST.get('remark' + str(i)))
                #         WorklogPart.objects.filter(content_part_id=logid, stage=i).update(dutyman_id=request.POST.get('dutyman' + str(i)))
                #         if int(request.POST.get('is_done' + str(i))) == 1:
                #             is_done.append(int(request.POST.get('is_done' + str(i))))
                #     if len(is_done) == int(stage):
                #
                #         Worklog.objects.filter(id=logid).update(is_done=True)
                #     else:
                #         Worklog.objects.filter(id=logid).update(is_done=False)
                #     res['result'] = True
                # else:
                #     res['result'] = False

                part_id = request.POST.get("part_id")
                end_time = request.POST.get("end_time")
                is_done = request.POST.get("is_done")
                complete = request.POST.get("complete")
                remark = request.POST.get("remark")
                log_part = WorklogPart.objects.filter(id=part_id).first()
                log_part.e_time = end_time
                if is_done == "1":
                    log_part.is_done = True
                if log_part == "" or log_part == None:
                    log_part.performance = complete
                else:
                    log_part.performance += "\n" + complete
                log_part.remark = remark
                log_part.save()
                work_log = log_part.content_part
                is_done_num = len(WorklogPart.objects.filter(content_part=work_log, is_done=True))
                if is_done_num == work_log.step:
                    work_log.is_done = True
                    work_log.save()
                res['result'] = "1"
            else:
                res['result'] = "0"
        except Exception as e:
            res['result'] = str(e)
        return HttpResponse(json.dumps(res), content_type='application/json')


class WorkLog_Detail(LoginRequiredMixin, View):

    def get(self, request):
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

    def post(self, request):
        """
        看板删除
        :param request:
        :return:
        """
        ret = dict()
        part_id = request.POST.get("id")
        log_part = WorklogPart.objects.filter(id=part_id).first()
        log = log_part.content_part
        log_parts = log.worklogpart_set.all()
        log_parts.delete()
        log.delete()
        ret['status'] = "1"
        return HttpResponse(json.dumps(ret), content_type='application/json')


# 设置填写人员
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


class WorkRecordDep(LoginRequiredMixin, View):
    """
    日志部门列表
    """

    def get(self, request):
        ret = dict()
        department = Structure.objects.filter(~Q(id="16"), ~Q(title="董事长"), ~Q(title="总经理"), ~Q(title="副总经理"),
                                              ~Q(title="总部"), ~Q(title="电力工程"), ~Q(title="测试"), )
        ret['department'] = department
        return render(request, "work/work_record_dep.html", ret)


class WorkRecordUser(LoginRequiredMixin, View):
    """
    日志部门人员列表
    """

    def get(self, request):
        ret = dict()
        dep_id = request.GET.get("id")
        department = Structure.objects.filter(id=dep_id).first()
        users = department.userprofile_set.filter(is_active="1")
        ret["department"] = department
        ret["users"] = users
        return render(request, "work/dep_user.html", ret)

    def post(self, request):
        """
        日志模板删除
        :param request:
        :return:
        """
        ret = dict()
        try:
            id0 = request.POST.get("id")
            tem = WorkRecordTem.objects.filter(id=id0).first()
            tem.is_delete = True
            tem.save()
            ret["result"] = True
        except Exception as e:
            ret["e"] = str(e)
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type='application/json')


# 与上方datetime有冲突  重新导入
import datetime


class WorkRecordTemList(LoginRequiredMixin, View):
    """
    日志模板列表
    """

    def get(self, request):
        ret = dict()
        user_id = request.GET.get("id")
        user = UserProfile.objects.filter(id=user_id).first()
        ret["user_id"] = user_id
        ret["user"] = user

        # 判断是否是本人或部门负责人
        c_user_id = request.session.get("_auth_user_id")
        if c_user_id == user_id:
            ret["key1"] = "1"
        else:
            ret["key1"] = "0"
        adm_list = user.department.adm_list
        if adm_list:
            adm_list = adm_list.split(",")
        else:
            adm_list = []
        if c_user_id in adm_list:
            ret["key2"] = "1"
        else:
            ret["key2"] = "0"

        # 判断今日日志是否提交
        today = datetime.date.today()
        tem = WorkRecordTem.objects.filter(user_id=user_id, is_delete=False).first()
        if tem:
            record = WorkRecord.objects.filter(tem_id=tem.id, date=today).first()
            if record:
                if record.is_submit:
                    ret["is_submit"] = "1"
                else:
                    ret["is_submit"] = "0"
            else:
                ret["is_submit"] = "0"
        else:
            ret["is_submit"] = "0"
        return render(request, "work/tem_list.html", ret)

    def post(self, request):
        user_id = request.POST.get("user_id")
        fields = ["id", "content", "remark", "type"]
        today = datetime.date.today()
        tem = WorkRecordTem.objects.values(*fields).filter(user_id=user_id, is_delete=False)
        record_list = []
        for i in range(len(tem)):
            record = WorkRecord.objects.filter(tem_id=tem[i]["id"], date=today).first()
            if record:
                if record.is_done:
                    is_done = {"is_done": "是 √"}
                else:
                    is_done = {"is_done": "否"}
            else:
                is_done = {"is_done": "否"}
            record_list.append(dict(tem[i], **is_done))
        ret = dict(data=record_list)
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type='application/json')


class WorkRecordCreate(LoginRequiredMixin, View):
    """
    日志模板新增
    """

    def get(self, request):
        ret = dict()
        user_id = request.GET.get("id0")
        ret["user_id"] = user_id
        tem_id = request.GET.get("tem_id")
        if tem_id:
            tem = WorkRecordTem.objects.filter(id=tem_id).first()
            ret["tem"] = tem
        return render(request, "work/workrecord_tem_create.html", ret)

    def post(self, request):
        ret = dict()
        try:
            user_id = request.POST.get("id0")
            type0 = request.POST.get("type")
            content = request.POST.get("content")
            remark = request.POST.get("remark")
            tem_id = request.POST.get("tem_id")
            if tem_id:
                tem = WorkRecordTem.objects.filter(id=tem_id).first()
            else:
                tem = WorkRecordTem()
            tem.user_id = user_id
            tem.type = type0
            tem.content = content
            tem.remark = remark
            tem.save()
            ret["status"] = "success"
        except Exception as e:
            ret["e"] = str(e)
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type='application/json')


class WorkRecordAjax(LoginRequiredMixin, View):
    """
    日志ajax
    """

    def get(self, request):
        """
        当日完成情况ajax
        :param request:
        :return:
        """
        ret = dict()
        tem_id = request.GET.get("id")
        status = request.GET.get("status")
        today = datetime.date.today()
        if status == "1":
            record = WorkRecord()
            record.tem_id = tem_id
            record.is_submit = False
            record.is_done = True
            record.save()
        if status == "0":
            record = WorkRecord.objects.filter(tem_id=tem_id, date=today, is_done=True).first()
            record.delete()
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type='application/json')

    def post(self, request):
        """
        日志提交ajax
        :param request:
        :return:
        """
        ret = dict()
        try:
            user_id = request.session.get("_auth_user_id")
            today = datetime.date.today()
            tem_list = WorkRecordTem.objects.filter(user_id=user_id, is_delete=False)
            for tem in tem_list:
                record = WorkRecord.objects.filter(tem_id=tem.id, date=today).first()
                if record:
                    record.is_submit = True
                    record.save()
                else:
                    record = WorkRecord()
                    record.tem_id = tem.id
                    record.is_done = False
                    record.is_submit = True
                    record.save()
            ret["status"] = "1"
        except Exception as e:
            ret["e"] = str(e)
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type='application/json')


class WorkRecordHistory(LoginRequiredMixin, View):
    """
    日志记录历史
    """

    def get(self, request):
        ret = dict()
        user_id = request.GET.get("id")
        user = UserProfile.objects.filter(id=user_id).first()
        ret["user_id"] = user_id
        ret["user"] = user
        return render(request, "work/record_list.html", ret)

    def post(self, request):
        user_id = request.POST.get("user_id")
        fields = ["id", "tem__content", "tem__type", "date", "tem__remark", "is_done"]
        filters = dict()
        if request.POST.get("date"):
            filters["date"] = request.POST.get("date")
        ret = dict(data=list(
            WorkRecord.objects.values(*fields).filter(is_submit=True, tem__user_id=user_id, **filters).order_by(
                "-date")))
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type='application/json')
