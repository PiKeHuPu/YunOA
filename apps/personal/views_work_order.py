import json
import re

from django.shortcuts import render, redirect
from django.db.models import Q
from django.views.generic.base import View
from django.http import HttpResponse
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.core.serializers.json import DjangoJSONEncoder

from utils.mixin_utils import LoginRequiredMixin
from rbac.models import Menu
from .models import WorkOrder, WorkOrderRecord, WorkOrderFlow, WorkOrderLog, BusinessApply
from .forms import WorkOrderCreateForm, WorkOrderUpdateForm, WorkOrderRecordForm, WorkOrderRecordUploadForm, \
    WorkOrderProjectUploadForm, APProjectUploadForm
from adm.models import Customer
from rbac.models import Role, SpecialRole
from users.models import Structure

from utils.toolkit import ToolKit, SendMessage
from utils.type_constant import to_list, to_dict
from utils.auto_create import auto_timestamp
from datetime import datetime

User = get_user_model()


def update_next_user(work_order, current_user_id, order_flow, pro_type):
    """
    获取审批流程及条件，完成work_order审批信息更新。
    :param work_order: QuerySet
    :param current_user_id: 当前用户
    :param order_flow: 审批流程
    :param pro_type: 流程类型 0，审批；1，报销
    :return:
    """

    if order_flow:
        process = order_flow.process
        users_id = process.split('|')  # 审批人
        order_user_id = ''  # 条件审批人
        if users_id == [process]:  # 审批流程是‘18&21’这种样子的 或者只有一个审批人(总经理提的，只有董事长)
            if '&' in users_id[0]:  # 包含审批流程
                tem_users_id = users_id[0].split('&')  # 所有审批人
                order_user_id = tem_users_id[-1]  # 条件审批人
                users_id = [tem_users_id[0]]  # 非条件审批人
        else:  # 审批流程不是‘18&21’这种样子的
            if '&' in users_id[-1]:
                end_users_id = users_id[-1].split('&')
                order_user_id = end_users_id[-1]  # 条件审批人
                users_id[-1] = end_users_id[0]  # 非条件审批人
        if current_user_id == order_user_id:  # 条件审批人审批同意
            work_order.status = '2'  # 审批完成
            if pro_type == '0':
                if work_order.advance == '0':
                    apply(work_order, users_id[0])
        else:  # 非条件审批人
            if current_user_id != users_id[-1]:  # 不是最后一个审批人
                if current_user_id in users_id:  # 当前用户在审批流程中，审批人为下一个
                    work_order.next_user_id = users_id[users_id.index(current_user_id) + 1]
                else:
                    work_order.next_user_id = users_id[0]
            else:  # 是最后一个审批人
                if order_flow.factor_type == '1':  # 条件为金额
                    if pro_type == '1':
                        all_cost = work_order.all_fee
                    else:
                        all_cost = work_order.cost
                    if float(all_cost) >= float(order_flow.factor):
                        work_order.next_user_id = order_user_id
                    else:
                        work_order.status = '2'  # 审批完成
                        if pro_type == '0':
                            if work_order.advance == '0':
                                apply(work_order, users_id[0])
                elif order_flow.factor_type == '0':  # 时间为条件
                    # 时间计算方法
                    d_time_value = work_order.end_time - work_order.start_time
                    d_value = d_time_value.days + (d_time_value.seconds / 3600 / 24)
                    if d_value >= int(order_flow.factor):
                        work_order.next_user_id = order_user_id
                    else:
                        work_order.status = '2'  # 审批完成
                        if pro_type == '0':
                            if work_order.advance == '0':
                                apply(work_order, users_id[0])
                else:  # 没有审批条件的。总经理--->董事长
                    work_order.status = '2'  # 审批完成
                    if pro_type == '0':
                        if work_order.advance == '0':
                            apply(work_order, users_id[0])
        return True


# 立项审批完成自动创建报销
def apply(work_order, next_user_id):
    ap = BusinessApply(workorder=work_order,
                       title=work_order.title,
                       cretor=work_order.cretor,
                       structure=work_order.structure,
                       next_user_id=next_user_id,
                       all_fee=work_order.cost,
                       file_content=work_order.file_content,
                       )
    if work_order.type == '1':  # 出差
        ap.transport = work_order.transport
        ap.becity = work_order.becity
        ap.destination = work_order.destination
        ap.people = work_order.people
        ap.start_time = work_order.start_time
        ap.end_time = work_order.end_time
        ap.type = work_order.type
    elif work_order.type == '0':  # 立项
        ap.payee = work_order.payee
        ap.bank_account = work_order.bank_account
        ap.bank_info = work_order.bank_info
        ap.invoice_type = work_order.invoice_type
    ap.save()


class WorkOrderView2(LoginRequiredMixin, View):
    """
    申请视图：根据前端请求的URL 分为个视图：我创建的申请、我审批的申请和我收到的申请
    """

    def get(self, request):
        ret = Menu.getMenuByRequestUrl(url=request.path_info)
        status_list = []
        filters = dict()
        for work_order_status in WorkOrder.status_choices:
            status_dict = dict(item=work_order_status[0], value=work_order_status[1])
            status_list.append(status_dict)
        if request.user.department_id == 9:  # 销售部门只能看自己的设备信息
            filters['belongs_to_id'] = request.user.id
        customers = Customer.objects.filter(**filters).order_by('unit')  # TODO 客户单位
        ret['status_list'] = status_list
        ret['customers'] = customers
        return render(request, 'personal/workorder/workorder.html', ret)


class WorkOrderView(LoginRequiredMixin, View):
    """
    申请视图：根据前端请求的URL 分为视图：我的申请和我收到的申请
    toDO 开始改动
    """

    def get(self, request):
        ret = Menu.getMenuByRequestUrl(url=request.path_info)
        status_list = to_list(WorkOrder.status_choices)
        filters = dict()
        type_list = to_list(WorkOrder.type_choices)
        ret['type_list'] = type_list
        ret['status_list'] = status_list
        return render(request, 'personal/workorder/workorder.html', ret)


class WorkOrderListView(LoginRequiredMixin, View):
    """
    申请列表：通过前端Ajxi传递回来的url来区分不同视图，返回相应列表数据
    """

    def get(self, request):
        fields = ['id', 'number', 'title', 'type', 'status', 'start_time', 'end_time', 'structure__title',
                  'create_time', 'advance', 'adv_payment', 'cretor__name', 'cost']
        filters = dict()
        if request.GET.get('number'):
            filters['number__contains'] = request.GET.get('number')
        if request.GET.get('workorder_status'):
            filters['status'] = request.GET.get('workorder_status')
        if request.GET.get('customer'):
            filters['type'] = request.GET.get('customer')
        if request.GET.get('cretor__name'):
            filters['cretor__name'] = request.GET.get('cretor__name')
        if 'main_url' in request.GET and request.GET['main_url'] == '/personal/workorder_Icrt/':
            filters['cretor_id'] = request.user.id
            ret = dict(data=list(WorkOrder.objects.filter(**filters).values(*fields).order_by('-create_time')))
        if 'main_url' in request.GET and request.GET['main_url'] == '/personal/workorder_app/':
            request_user_id = request.user.id
            filters['next_user_id'] = request_user_id
            filters['status__in'] = ['0', '1']  # 状态为等待和审批中
            ret = dict(data=list(WorkOrder.objects.filter(**filters).values(*fields).order_by('-create_time')))
            cashier = SpecialRole.objects.filter(title='0').first()
            if request_user_id == cashier.user.id:
                adv_workorder = list(
                    WorkOrder.objects.filter(status='5').values(*fields).order_by(
                        '-create_time'))
                ret['data'] += adv_workorder

        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type='application/json')


class WorkOrderCreateView(LoginRequiredMixin, View):
    """
    （用户自己操作自己的申请）创建/更新审批
    """

    def get(self, request):
        ret = dict()
        type_list = to_list(WorkOrder.type_choices)  # 审批类型
        invoice_list = to_list(WorkOrder.invoice_choices)  # 发票类型
        advance_list = to_list(WorkOrder.advance_choices)  # 是否预支
        users = User.objects.values('name', 'department__title', 'id')
        transport = to_list(WorkOrder.transport_choices)
        if request.GET.get('id'):
            work_order = get_object_or_404(WorkOrder, pk=request.GET['id'])
            ret['work_order'] = work_order
            people = work_order.people
            if people:
                ret['people'] = [people]
                if '|' in people:
                    tem_people = people.split('|')
                    ret['people'] = tem_people
        # 查询最后一位
        # try:
        #     number = WorkOrder.objects.latest('number').number
        # except WorkOrder.DoesNotExist:
        #     number = ""
        # new_number = ToolKit.bulidNumber('SX', 9, number)
        ret.update({
            'type_list': type_list,
            'invoice_list': invoice_list,
            'users_dict': users,
            'transport': transport,
            'advance_list': advance_list,
        })
        return render(request, 'personal/workorder/workorder_create.html', ret)

    def post(self, request):
        res = dict(result=False)
        ret_data = json.loads(request.body.decode())
        work_order_id = ret_data.get('id')
        if work_order_id:
            work_order = get_object_or_404(WorkOrder, pk=work_order_id)
        else:
            work_order = WorkOrder()
            work_order.number = auto_timestamp('WO')
        work_order.title = ret_data.get('title')
        work_order.type = ret_data.get('type')
        work_order.status = '0'  # 等待审批
        work_order.cost = ret_data.get('cost')
        work_order.cretor = request.user
        work_order.structure = request.user.department
        advance = ret_data.get('advance')
        work_order.advance = advance
        if ret_data.get('type') == '0' or advance == '1':  # 立项审批
            work_order.invoice_type = ret_data.get('invoice_type')
            work_order.payee = ret_data.get('payee')
            work_order.bank_account = ret_data.get('bank_account')
            work_order.bank_info = ret_data.get('bank_info')

        if ret_data.get('type') == '1':  # 出差审批
            work_order.people = ret_data.get('people')
            work_order.transport = ret_data.get('transport')
            work_order.becity = ret_data.get('becity')
            work_order.destination = ret_data.get('destination')
            work_order.start_time = ret_data.get('start_time')
            work_order.end_time = ret_data.get('end_time')
        current_user_id = request.user.id
        # 如果是预付款，流程走报销流程
        pro_type = '0'
        if advance == '0':
            pro_type = '0'
        elif advance == '1':
            pro_type = '1'
        order_flow = WorkOrderFlow.objects.filter(order_type=ret_data.get('type'), pro_type=pro_type,
                                                  structure=request.user.department).first()
        bool_info = update_next_user(work_order, str(current_user_id), order_flow, '0')  # 更新审批人信息
        if bool_info:
            work_order.save()
            res['status'] = 'success'
            res['workorder_id'] = work_order.id
        else:
            res['status'] = 'fail'
            res['errors_info'] = '还没有建立审批人，请联系人事部门'
        return HttpResponse(json.dumps(res), content_type='application/json')

    # def post(self, request):
    #     res = dict()
    #     work_order = WorkOrder()
    #     work_order_form = WorkOrderCreateForm(request.POST, instance=work_order)
    #     if work_order_form.is_valid():
    #         work_order_form.save()
    #         res['status'] = 'success'
    #         if work_order.status == "2":
    #             res['status'] = 'submit'
    #             # 发送邮件功能
    #             # try:
    #             #     SendMessage.send_workorder_email(request.POST['number'])
    #             #     res['status'] = 'submit_send'
    #             # except Exception:
    #             #     pass
    #     else:
    #         pattern = '<li>.*?<ul class=.*?><li>(.*?)</li>'
    #         errors = str(work_order_form.errors)
    #         work_order_form_errors = re.findall(pattern, errors)
    #         res = {
    #             'status': 'fail',
    #             'work_order_form_errors': work_order_form_errors[0]
    #         }
    # return HttpResponse(json.dumps(res), content_type='application/json')


class WorkOrderDetailView(LoginRequiredMixin, View):
    # 审批详情
    def get(self, request):
        ret = dict()

        user_id = request.user.id  # 获取当前访问用户id
        ret['user_id'] = user_id

        admin_user_list = []
        if 'id' in request.GET and request.GET['id']:
            work_order = get_object_or_404(WorkOrder, pk=request.GET['id'])
            work_order_log = work_order.workorderlog_set.filter(type='0').order_by('create_time')  # 关联表查询方法
            people = work_order.people
            if people:
                ret['people'] = [people]
                if '|' in people:
                    tem_people = people.split('|')
                    people_obj = User.objects.filter(id__in=tem_people).values('id', 'name')
                    ret['people'] = people_obj

            try:
                role = Role.objects.get(title="管理")
                admin_user_ids = role.userprofile_set.values('id')
                for admin_user_id in admin_user_ids:
                    admin_user_list.append(admin_user_id['id'])
            except Exception:
                pass
            user_list = [x.creator.id for x in work_order_log]  # 审批过的人
            user_list += [work_order.cretor_id, work_order.next_user_id]  # 自己和当前审批人
            cashier = SpecialRole.objects.filter(title__in = ['0','1']) # 出纳0, CFO1
            if cashier:
                for i in cashier:
                    user_list.append(i.user.id)
            user_list.extend(admin_user_list)

            # 和工单无关联的用户禁止通过手动指定ID的形式非法获取数据
            if request.user.id in user_list:
                ret['work_order'] = work_order
                # ret['work_order_record'] = work_order_record
                ret['work_order_log'] = work_order_log
            else:
                ret['ban'] = 'ban'
        return render(request, 'personal/workorder/workorder_detail.html', ret)


class WorkOrderDeleteView(LoginRequiredMixin, View):

    def post(self, request):
        ret = dict(result=False)
        if 'id' in request.POST and request.POST['id']:
            status = get_object_or_404(WorkOrder, pk=request.POST['id']).status
            if int(status) <= 1:
                id_list = map(int, request.POST.get('id').split(','))
                WorkOrder.objects.filter(id__in=id_list).delete()
                ret['result'] = True
        return HttpResponse(json.dumps(ret), content_type='application/json')


class WorkOrderAppView(LoginRequiredMixin, View):
    """
    审批项目页面
    """

    def get(self, request):
        ret = Menu.getMenuByRequestUrl(url=request.path_info)
        status_list = to_list(WorkOrder.status_choices)
        type_list = to_list(WorkOrder.type_choices)
        ret['type_list'] = type_list
        ret['status_list'] = status_list
        return render(request, 'personal/workorder/workorder_app.html', ret)


class WorkOrderAppUpdateView(LoginRequiredMixin, View):
    """
    审批立项(弹窗里的)
    """

    def get(self, request):
        ret = dict()
        users = User.objects.values('name', 'department__title', 'id')
        if request.GET.get('id'):
            request_user_id = request.user.id
            work_order = get_object_or_404(WorkOrder, pk=request.GET['id'])
            work_order_log = work_order.workorderlog_set.filter(type='0').order_by('create_time')
            ret['work_order'] = work_order
            people = work_order.people
            if people:
                ret['people'] = [people]
                if '|' in people:
                    tem_people = people.split('|')
                    people_obj = User.objects.filter(id__in=tem_people).values('id', 'name')
                    ret['people'] = people_obj
            ret.update({
                'users_dict': users,
                'work_order_log': work_order_log,
                'cashier': '0'
            })
            cashier = SpecialRole.objects.filter(title='0').first()
            if request_user_id == cashier.user.id:
                ret['cashier'] = '1'

            # 获取申请人近十条申请记录
            user_id = work_order.cretor_id
            user_orders = WorkOrder.objects.filter(Q(cretor_id=user_id) & ~Q(id=request.GET.get('id'))).order_by("-create_time")[:10]
            for i in user_orders:
                if len(i.title) >= 10:
                    i.title = i.title[:10] + "..."
            ret['user_orders'] = user_orders

        return render(request, 'personal/workorder/workorder_app_update.html', ret)

    def post(self, request):
        res = dict()
        ret_data = json.loads(request.body.decode())
        work_order = get_object_or_404(WorkOrder, pk=str(ret_data.get('id')))
        advance = work_order.advance
        current_user_id = request.user.id
        if current_user_id == work_order.next_user_id:  # TODO
            if ret_data.get('opinion') == 'agree':
                # 完成审批， 并写入下一个审批人
                work_order.status = '1'
                # 如果是预付款，流程走报销流程
                pro_type = '0'
                if advance == '0':
                    pro_type = '0'
                elif advance == '1':
                    pro_type = '1'
                order_flow = WorkOrderFlow.objects.filter(order_type=str(ret_data.get('type')), pro_type=pro_type,
                                                          structure_id=str(ret_data.get('structure'))).first()
                update_next_user(work_order, str(current_user_id), order_flow, '0')
                # 记录审批log
                if work_order.status == '2' and work_order.advance == '1' and work_order.adv_payment == '0':
                    work_order.status = '5'  # 等待付款
                order_log = WorkOrderLog(order_id=work_order,
                                         record_type='0',
                                         desc=ret_data.get('desc', ''),
                                         creator=request.user,
                                         structure=request.user.department
                                         )
                print(order_log.desc)
            elif ret_data.get('opinion') == 'disagree':
                # 审批不同意， 标记结果
                work_order.status = '3'
                order_log = WorkOrderLog(order_id=work_order,
                                         record_type='1',
                                         desc=ret_data.get('desc', ''),
                                         creator=request.user,
                                         structure=request.user.department
                                         )
            order_log.save()
            work_order.save()
            res['status'] = 'success'
        elif work_order.status == '5':  # 等待预付款
            cashier = SpecialRole.objects.filter(title='0').first()
            if cashier:
                if current_user_id == cashier.user.id:  # 当前用户是出纳
                    if ret_data.get('opinion') == 'agree':
                        # 记录审批log
                        order_log = WorkOrderLog(order_id=work_order,
                                                 record_type='0',
                                                 desc=ret_data.get('desc', ''),
                                                 creator=request.user,
                                                 structure=request.user.department
                                                 )
                        work_order.adv_payment = '1'
                        work_order.status = '4'  # 付款完成
                        apply(work_order, current_user_id)
                    order_log.save()
                    work_order.save()
                    res['status'] = 'success'
        else:
            res['error'] = '当前项目还没到你审批，请等待'
        return HttpResponse(json.dumps(res), content_type='application/json')


class WorkOrderUpdateView(LoginRequiredMixin, View):
    """
    修改申请  TODO已废弃,
    """

    def get(self, request):
        type_list = []
        ret = dict()

        type_list = to_list(WorkOrder.type_choices)  # 审批类型
        invoice_list = to_list(WorkOrder.invoice_choices)  # 发票类型
        role = get_object_or_404(Role, title='审批')
        users = User.objects.values('name', 'department__title', 'id')
        transport = to_list(WorkOrder.transport_choices)
        if request.GET.get('id'):
            work_order = get_object_or_404(WorkOrder, pk=request.GET['id'])
            people = work_order.people
            tem_people = [people]
            if people and '|' in people:
                tem_people = people.split('|')
            ret['people'] = tem_people
            ret['work_order'] = work_order

        ret.update({
            'type_list': type_list,
            'invoice_list': invoice_list,
            'users_dict': users,
            'transport': transport
        })
        return render(request, 'personal/workorder/workorder.html', ret)

    def post(self, request):
        res = dict()
        work_order = get_object_or_404(WorkOrder, pk=request.POST['id'])
        work_order_form = WorkOrderUpdateForm(request.POST, instance=work_order)
        if int(work_order.status) <= 1:
            if work_order_form.is_valid():
                work_order_form.save()
                res['status'] = 'success'
                if work_order.status == "2":
                    res['status'] = 'submit'
                    try:
                        SendMessage.send_workorder_email(request.POST['number'])
                        res['status'] = 'submit_send'
                    except Exception:
                        pass
            else:
                pattern = '<li>.*?<ul class=.*?><li>(.*?)</li>'
                errors = str(work_order_form.errors)
                work_order_form_errors = re.findall(pattern, errors)
                res = {
                    'status': 'fail',
                    'work_order_form_errors': work_order_form_errors[0]
                }
        else:
            res['status'] = 'ban'
        return HttpResponse(json.dumps(res), content_type='application/json')


class WrokOrderSendView(LoginRequiredMixin, View):
    """
    工单派发： 由审批人完成工单派发，记录派发状态 '1'，
    """

    def get(self, request):
        ret = dict()
        engineers = User.objects.filter(department__title='技术部')
        work_order = get_object_or_404(WorkOrder, pk=request.GET['id'])
        ret['engineers'] = engineers
        ret['work_order'] = work_order
        ret['record_type'] = "1"
        return render(request, 'personal/workorder/workorder_send.html', ret)

    def post(self, request):
        res = dict(status='fail')
        work_order_record_form = WorkOrderRecordForm(request.POST)
        if work_order_record_form.is_valid():
            work_order = get_object_or_404(WorkOrder, pk=request.POST['work_order'])
            status = work_order.status
            if status in ['0', '2'] and request.user.id == work_order.approver_id:
                work_order_record_form.save()
                work_order.receiver_id = request.POST['receiver']
                work_order.status = "3"
                work_order.do_time = request.POST['do_time']
                work_order.save()
                res['status'] = 'success'
                try:
                    SendMessage.send_workorder_email(request.POST['number'])
                    res['status'] = 'success_send'
                except Exception:
                    pass

            else:
                res['status'] = 'ban'
        return HttpResponse(json.dumps(res, cls=DjangoJSONEncoder), content_type='application/json')


class WorkOrderExecuteView(LoginRequiredMixin, View):

    def get(self, request):
        ret = dict()
        work_order = get_object_or_404(WorkOrder, pk=request.GET['id'])
        ret['work_order'] = work_order
        ret['record_type'] = "2"
        return render(request, 'personal/workorder/workorder_execute.html', ret)

    def post(self, request):
        res = dict(status='fail')
        work_order_record_form = WorkOrderRecordForm(request.POST)
        work_order = get_object_or_404(WorkOrder, pk=request.POST['work_order'])
        if work_order_record_form.is_valid() and work_order.receiver_id == request.user.id:
            status = work_order.status
            if status == '3' and request.user.id == work_order.receiver_id:
                work_order_record_form.save()
                work_order.status = "4"
                work_order.save()
                res['status'] = 'success'
                try:
                    SendMessage.send_workorder_email(request.POST['number'])
                    res['status'] = 'success_send'
                except Exception as e:
                    pass
            else:
                res['status'] = 'ban'
        return HttpResponse(json.dumps(res, cls=DjangoJSONEncoder), content_type='application/json')


class WorkOrderFinishView(LoginRequiredMixin, View):

    def get(self, request):
        ret = dict()
        work_order = get_object_or_404(WorkOrder, pk=request.GET['id'])
        ret['work_order'] = work_order
        ret['record_type'] = "3"
        return render(request, 'personal/workorder/workorder_finish.html', ret)

    def post(self, request):
        res = dict(status='fail')
        work_order_record_form = WorkOrderRecordForm(request.POST)
        work_order = get_object_or_404(WorkOrder, pk=request.POST['work_order'])
        if work_order_record_form.is_valid() and work_order.proposer.id == request.user.id:
            status = work_order.status
            if status == '4' and request.user.id == work_order.proposer_id:
                work_order_record_form.save()
                work_order.status = "5"
                work_order.save()
                res['status'] = 'success'
                try:
                    SendMessage.send_workorder_email(request.POST['number'])
                    res['status'] = 'success_send'
                except Exception as e:
                    pass
            else:
                res['status'] = 'ban'
        return HttpResponse(json.dumps(res, cls=DjangoJSONEncoder), content_type='application/json')


class WorkOrderReturnView(LoginRequiredMixin, View):

    def get(self, request):
        ret = dict()
        work_order = get_object_or_404(WorkOrder, pk=request.GET['id'])
        ret['work_order'] = work_order
        ret['record_type'] = "0"
        return render(request, 'personal/workorder/workorder_return.html', ret)

    def post(self, request):
        res = dict(status='fail')
        work_order_record_form = WorkOrderRecordForm(request.POST)
        work_order = get_object_or_404(WorkOrder, pk=request.POST['work_order'])
        if work_order_record_form.is_valid():
            status = work_order.status
            if status == '3':
                work_order_record_form.save()
                work_order.status = "0"
                work_order.save()
                res['status'] = 'success'
                try:
                    SendMessage.send_workorder_email(request.POST['number'])
                    res['status'] = 'success_send'
                except Exception as e:
                    pass
                work_order.receiver = None
                work_order.save()
            else:
                res['status'] = 'ban'
        return HttpResponse(json.dumps(res, cls=DjangoJSONEncoder), content_type='application/json')


class WorkOrderUploadView(LoginRequiredMixin, View):
    """
    申请上传附件
    """

    def post(self, request):
        res = dict(status='fail')
        work_order = get_object_or_404(WorkOrder, pk=request.POST['id'])
        work_order_project_upload_form = WorkOrderProjectUploadForm(request.POST, request.FILES, instance=work_order)
        if work_order_project_upload_form.is_valid() and request.user.id == work_order.cretor_id:
            work_order_project_upload_form.save()
            res['status'] = 'success'
        return HttpResponse(json.dumps(res, cls=DjangoJSONEncoder), content_type='application/json')


class APProjectUploadView(LoginRequiredMixin, View):
    """
    报销上传附件
    """

    def post(self, request):
        res = dict(status='fail')
        iii = request.POST['id']
        ap = get_object_or_404(BusinessApply, pk=request.POST['id'])
        ap_project_upload_form = APProjectUploadForm(request.POST, request.FILES, instance=ap)
        if ap_project_upload_form.is_valid() and request.user.id == ap.cretor_id:
            ap_project_upload_form.save()
            res['status'] = 'success'
        return HttpResponse(json.dumps(res, cls=DjangoJSONEncoder), content_type='application/json')



class WorkOrderDocumentView(LoginRequiredMixin, View):
    """
    工单文档
    """

    def get(self, request):
        ret = Menu.getMenuByRequestUrl(url=request.path_info)

        return render(request, 'personal/workorder/document.html', ret)


class WorkOrderDocumentListView(LoginRequiredMixin, View):
    """
    工单文档列表
    """

    def get(self, request):
        fields = ['work_order__number', 'work_order__customer__unit', 'name__name', 'add_time', 'file_content']
        ret = dict(data=list(WorkOrderRecord.objects.filter(~Q(file_content='')).values(*fields).order_by('-add_time')))

        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type='application/json')


# 审批流程设置
class WorkOrderFlowView(LoginRequiredMixin, View):
    """
    审批流程页面
    """

    def get(self, request):
        # ret = Menu.getMenuByRequestUrl(url=request.path_info)

        return render(request, 'personal/workorder/flow.html')


class WorkOrderFlowListView(LoginRequiredMixin, View):
    """
    审批流程列表
    """

    def get(self, request):
        fields = ['structure__title', 'order_type', 'id', 'pro_type']
        ret = dict(data=list(WorkOrderFlow.objects.filter().values(*fields).order_by('-create_time')))

        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type='application/json')


class WorkOrderFlowDetailView(LoginRequiredMixin, View):
    """
    审批流程查看,修改,新建路由
    """

    def get(self, request):
        ret = dict()
        flow_id = request.GET.get('id')
        structures = Structure.objects.all()
        users = User.objects.all().values('id', 'name')
        ret['flow_type'] = WorkOrderFlow.type_choices
        ret['pro_type'] = WorkOrderFlow.pro_type_choices
        ret['factor_choices'] = WorkOrderFlow.factor_choices
        ret['users'] = users
        if flow_id:
            flow = get_object_or_404(WorkOrderFlow, pk=flow_id)
            ret['flow'] = flow
            if flow.process:
                users_id = flow.process.split('|')  # 审批人
                if '&' in users_id[-1]:
                    end_users_id = users_id[-1].split('&')
                    order_user_id = end_users_id[-1]  # 条件审批人
                    users_id[-1] = end_users_id[0]
                    ret['order_user_id'] = int(order_user_id)

                process_info = []
                flow_users = list(users)
                for id in users_id:
                    for user in flow_users:
                        if int(id) == int(user['id']):
                            process_info.append(dict(id=int(id), name=user['name']))
                            flow_users.remove(user)
                            break
                ret['process'] = process_info
                ret['flow_users'] = flow_users
            if flow.carbon:
                carbon_users_id = flow.carbon.split('|')  # 抄送人
                ret['carbon_user'] = [int(x) for x in carbon_users_id]
        else:
            ret['structures'] = structures
        return render(request, 'personal/workorder/flow_detail.html', ret)

    def post(self, request):
        res = dict(result=False)
        flow_data = json.loads(request.body.decode())
        flow_id = flow_data.get('id')
        if flow_id:
            flow = get_object_or_404(WorkOrderFlow, pk=flow_data.get('id'))
        else:
            flow = WorkOrderFlow()
        flow.process = flow_data.get('process')
        flow.carbon = flow_data.get('carbon')
        flow.order_type = flow_data.get('order_type')
        flow.structure_id = flow_data.get('structure')
        flow.pro_type = flow_data.get('pro_type')

        flow.updater = request.user
        if flow_data.get('factor_type'):
            flow.factor_type = flow_data.get('factor_type')
            flow.factor = flow_data.get('factor')
        flow.carbon = flow_data.get('carbon')
        flow.order_type = flow_data.get('order_type')
        flow.save()
        res['result'] = True
        return HttpResponse(json.dumps(res), content_type='application/json')


# 报销
class ApplyCostView(LoginRequiredMixin, View):
    """
    报销页面
    """

    def get(self, request):
        ret = Menu.getMenuByRequestUrl(url=request.path_info)
        status_list = to_list(BusinessApply.status_choices)
        filters = dict()
        type_list = to_list(BusinessApply.type_choices)
        ret['type_list'] = type_list
        ret['status_list'] = status_list
        return render(request, 'personal/workorder/apply.html', ret)


class APListView(LoginRequiredMixin, View):
    """
    报销申请列表：通过前端传递回来的url来区分不同视图，返回相应列表数据
    """

    def get(self, request):
        fields = ['id', 'workorder__number', 'workorder__id', 'title', 'type', 'status', 'structure__title',
                  'create_time', 'workorder__advance', 'cretor__name', 'all_fee']
        filters = dict()
        if request.GET.get('number'):
            filters['workorder__number'] = request.GET.get('number')
        if request.GET.get('workorder_status'):
            filters['status'] = request.GET.get('workorder_status')
        if request.GET.get('customer'):
            filters['type'] = request.GET.get('customer')
        if request.GET.get('cretor'):
            filters['cretor__name'] = request.GET.get('cretor')
        if 'main_url' in request.GET and request.GET['main_url'] == '/personal/workorder_ap_cost/':  # 我的
            filters['cretor_id'] = request.user.id
            ret = dict(data=list(BusinessApply.objects.filter(**filters).values(*fields).order_by('-create_time')))
        if 'main_url' in request.GET and request.GET['main_url'] == '/personal/workorder_ap_cost_app/':  # 等待我审批的
            request_user_id = request.user.id
            filters['next_user_id'] = request_user_id
            filters['status__in'] = ['0', '1']
            ret = dict(data=list(BusinessApply.objects.filter(**filters).values(*fields).order_by('-create_time')))
            cashier = SpecialRole.objects.filter(title='0').first()
            if request_user_id == cashier.user.id:
                adv_workorder = list(
                    BusinessApply.objects.filter(status='5').values(*fields).order_by(
                        '-create_time'))  # 审批完成等待报销
                ret['data'] += adv_workorder
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type='application/json')


class ApplyCostUpdateView(LoginRequiredMixin, View):
    """
    报销费用更新页面
    """

    def get(self, request):
        ret = {}
        type_list = to_list(BusinessApply.type_choices)  # 审批类型
        invoice_list = to_list(BusinessApply.invoice_choices)  # 发票类型
        transport_list = to_list(BusinessApply.transport_choices)  # 交通工具类型
        users = User.objects.values('name', 'department__title', 'id')
        ret['users'] = users
        ret['invoice_list'] = invoice_list
        ret['transport_list'] = transport_list
        transport = to_list(WorkOrder.transport_choices)
        ap = get_object_or_404(BusinessApply, workorder_id=request.GET['id'])
        ap_status = ap.status
        if ap_status == '-1' or ap_status == '0' or ap_status == '3':
            ret['ap'] = ap
            if ap.invoice_type:
                ret['invoice'] = [ap.invoice_type]
                if '|' in ap.invoice_type:
                    ret['invoice'] = ap.invoice_type.split('|')
            if ap.type == '1':  # 出差
                users = User.objects.values('name', 'department__title', 'id')
                ret['users'] = users
                people = ap.people
                if people:
                    ret['people'] = [people]
                    if '|' in people:
                        tem_people = people.split('|')
                        ret['people'] = tem_people
                if ap.transport:
                    ret['transport'] = [ap.transport]
                    if '|' in transport:
                        tem = transport.split('|')
                        ret['transport'] = tem

            return render(request, 'personal/workorder/apply_update.html', ret)
        else:
            return redirect('/personal/workorder_ap_cost/detail?id={}'.format(request.GET['id']))

    def post(self, request):
        res = dict(result=False)
        ret_data = json.loads(request.body.decode())
        workorder_id = ret_data.get('id')
        if workorder_id:
            ap = get_object_or_404(BusinessApply, workorder_id=workorder_id)
        else:
            ap = BusinessApply()
        ap.title = ret_data.get('title')
        ap.type = ret_data.get('type')
        ap.status = '0'  # 等待审批
        ap.all_fee = ret_data.get('all_fee')
        ap.invoice_type = ret_data.get('invoice_type')
        ap.payee = ret_data.get('payee')
        ap.bank_account = ret_data.get('bank_account')
        ap.bank_info = ret_data.get('bank_info')
        ap.advance = ret_data.get('advance')
        ap.detail = ret_data.get('detail')
        if ret_data.get('type') == '1':  # 出差审批
            ap.start_time = ret_data.get('start_time')
            ap.end_time = ret_data.get('end_time')
            ap.people = ret_data.get('people')
            ap.transport = ret_data.get('transport')
            ap.becity = ret_data.get('becity')
            ap.destination = ret_data.get('destination')
            ap.completion_info = ret_data.get('completion_info')

            ap.food_fee = ret_data.get('food_fee')
            ap.rece_fee = ret_data.get('rece_fee')
            ap.tran_fee = ret_data.get('tran_fee')
            ap.acco_fee = ret_data.get('acco_fee')
            ap.other_fee = ret_data.get('other_fee')
            end_t = datetime.strptime(ap.end_time, '%Y-%m-%d %H:%M')
            start_t = datetime.strptime(ap.start_time, '%Y-%m-%d %H:%M')
            d_time_value = end_t - start_t
            days = d_time_value.days + (d_time_value.seconds / 3600 / 24)
            ap.days = round(days, 2)
        current_user_id = request.user.id
        order_flow = WorkOrderFlow.objects.filter(order_type=ret_data.get('type'), pro_type='1',
                                                  structure=request.user.department).first()
        update_next_user(ap, str(current_user_id), order_flow, '1')  # 更新审批人信息
        ap.save()
        res['status'] = 'success'
        return HttpResponse(json.dumps(res), content_type='application/json')


class ApplyCostAppView(LoginRequiredMixin, View):
    """
    审批报销页面
    """

    def get(self, request):
        ret = Menu.getMenuByRequestUrl(url=request.path_info)
        status_list = to_list(BusinessApply.status_choices)
        filters = dict()
        type_list = to_list(BusinessApply.type_choices)
        ret['type_list'] = type_list
        ret['status_list'] = status_list

        return render(request, 'personal/workorder/apply_app.html', ret)


class ApDetailView(LoginRequiredMixin, View):
    # 报销详情
    def get(self, request):
        ret = dict()
        users = User.objects.values('name', 'department__title', 'id')
        admin_user_list = []
        if request.GET.get('id'):
            print(request.GET['id'])
            ap = get_object_or_404(BusinessApply, workorder_id=request.GET['id'])
            work_order = ap.workorder
            work_order_log = work_order.workorderlog_set.filter(type='1').order_by('create_time')
            ret['ap'] = ap
            people = ap.people
            if people:
                ret['people'] = [people]
                if '|' in people:
                    tem_people = people.split('|')
                    people_obj = User.objects.filter(id__in=tem_people).values('id', 'name')
                    ret['people'] = people_obj
            invoice_type = ap.invoice_type
            if invoice_type:
                ret['invoice_type'] = []
                in_dict = to_dict(ap.invoice_choices)
                if '|' in invoice_type:
                    tem = invoice_type.split('|')
                    for i in tem:
                        ret['invoice_type'].append(in_dict.get(i))
                else:
                    ret['invoice_type'] = [in_dict.get(invoice_type)]
            transport = ap.transport
            if transport:
                ret['transport'] = []
                tr_dict = to_dict(ap.transport_choices)
                if '|' in transport:
                    tem = transport.split('|')
                    for i in tem:
                        ret['transport'].append(tr_dict.get(i))
                else:
                    ret['transport'] = [tr_dict.get(transport)]
            ret.update({
                'users_dict': users,
                'work_order_log': work_order_log
            })
            # 和工单无关联的用户禁止通过手动指定ID的形式非法获取数据
            try:
                role = Role.objects.get(title="管理")
                admin_user_ids = role.userprofile_set.values('id')
                for admin_user_id in admin_user_ids:
                    admin_user_list.append(admin_user_id['id'])
            except Exception:
                pass
            user_list = [x.creator.id for x in work_order_log]  # 审批过的人
            user_list += [work_order.cretor_id, ap.next_user_id]
            cashier = SpecialRole.objects.filter(title__in=['0', '1'])  # 出纳0, CFO1
            if cashier:
                for i in cashier:
                    user_list.append(i.user.id)
            user_list.extend(admin_user_list)
            user_list.extend(admin_user_list)  # 管理员也可以查看  TODO 等待测试

            if request.user.id in user_list:
                ret['work_order'] = work_order
                ret['work_order_log'] = work_order_log
            else:
                ret['ban'] = 'ban'

        return render(request, 'personal/workorder/apply_app_detail.html', ret)


class CostAppUpdateView(LoginRequiredMixin, View):
    """
    审批报销(弹窗里的)
    """

    def get(self, request):
        ret = dict()
        users = User.objects.values('name', 'department__title', 'id')
        if request.GET.get('id'):
            request_user_id = request.user.id
            ap = get_object_or_404(BusinessApply, workorder_id=request.GET['id'])
            work_order_log = ap.workorder.workorderlog_set.filter(type='1').order_by('create_time')
            ret['ap'] = ap
            people = ap.people
            if people:
                ret['people'] = [people]
                if '|' in people:
                    tem_people = people.split('|')
                    people_obj = User.objects.filter(id__in=tem_people).values('id', 'name')
                    ret['people'] = people_obj
            invoice_type = ap.invoice_type
            if invoice_type:
                ret['invoice_type'] = []
                in_dict = to_dict(ap.invoice_choices)
                if '|' in invoice_type:
                    tem = invoice_type.split('|')
                    for i in tem:
                        ret['invoice_type'].append(in_dict.get(i))
                else:
                    ret['invoice_type'] = [in_dict.get(invoice_type)]
            transport = ap.transport
            if transport:
                ret['transport'] = []
                tr_dict = to_dict(ap.transport_choices)
                if '|' in transport:
                    tem = transport.split('|')
                    for i in tem:
                        ret['transport'].append(tr_dict.get(i))
                else:
                    ret['transport'] = [tr_dict.get(transport)]

            # 获取申请人近十条报销申请记录
            user_id = ap.cretor_id
            businessApplys = BusinessApply.objects.filter(Q(cretor_id=user_id) & ~Q(workorder_id=request.GET.get('id')) & ~Q(status=-1)).order_by("-create_time")[:10]
            for i in businessApplys:
                if len(i.title) >= 10:
                    i.title = i.title[:10] + "..."
            ret['businessApplys'] = businessApplys

        ret.update({
            'users_dict': users,
            'work_order_log': work_order_log,
            'cashier': '0'
        })
        cashier = SpecialRole.objects.filter(title='0').first()
        if request_user_id == cashier.user.id:
            ret['cashier'] = '1'
        return render(request, 'personal/workorder/apply_app_update.html', ret)

    def post(self, request):
        res = dict()
        ret_data = json.loads(request.body.decode())
        ap = get_object_or_404(BusinessApply, pk=str(ret_data.get('id')))
        current_user_id = request.user.id
        if current_user_id == ap.next_user_id:  # TODO
            if ret_data.get('opinion') == 'agree':
                # 完成审批， 并写入下一个审批人
                ap.status = '1'
                order_flow = WorkOrderFlow.objects.filter(order_type=str(ret_data.get('type')), pro_type='1',
                                                          structure_id=str(ret_data.get('structure'))).first()
                update_next_user(ap, str(current_user_id), order_flow, '1')
                # 判断是否需要出纳  TODO  需要加入出纳
                workorder = ap.workorder
                # 不论什么，必须经过出纳
                if ap.status == '2':
                    ap.status = '5'
                # 之前的逻辑，只有钱不够数，需要经过出纳
                # if ap.status == '2' and \
                #         workorder.advance == '1' and \
                #         workorder.adv_payment == '1':  # 完成审批，预付款完成
                #     if float(ap.all_fee) <= float(workorder.cost):  # 报销钱小于等于预付款钱
                #         ap.status = '4'
                #         workorder.status = '6'
                #         workorder.save()
                #     else:
                #         ap.status = '5'
                # 记录审批log
                order_log = WorkOrderLog(order_id=ap.workorder,
                                         type='1',
                                         record_type='0',
                                         desc=ret_data.get('desc', ''),
                                         creator=request.user,
                                         structure=request.user.department
                                         )
            elif ret_data.get('opinion') == 'disagree':
                # 审批不同意， 标记结果
                ap.status = '3'
                order_log = WorkOrderLog(order_id=ap.workorder,
                                         type='1',
                                         record_type='1',
                                         desc=ret_data.get('desc', ''),
                                         creator=request.user,
                                         structure=request.user.department
                                         )
            order_log.save()
            ap.save()
            res['status'] = 'success'
        # 出纳
        elif ap.status == '5':
            cashier = SpecialRole.objects.filter(title='0').first()
            if cashier:
                if current_user_id == cashier.user.id:
                    if ret_data.get('opinion') == 'agree':
                        workorder = ap.workorder
                        ap.status = '4'
                        workorder.status = '6'
                        workorder.save()
                        # 记录审批log
                        order_log = WorkOrderLog(order_id=ap.workorder,
                                                 type='1',
                                                 record_type='0',
                                                 desc=ret_data.get('desc', ''),
                                                 creator=request.user,
                                                 structure=request.user.department
                                                 )
                    order_log.save()
                    ap.save()
                    res['status'] = 'success'

        else:
            res['error'] = '当前项目还没到你审批，请等待'
        return HttpResponse(json.dumps(res), content_type='application/json')


class CostAppUpdateDetailView(LoginRequiredMixin, View):
    """
    审批报销页面点击审批单号时的跳转页面
    """
    def get(self, request):
        ret = dict()

        user_id = request.user.id  # 获取当前访问用户id
        ret['user_id'] = user_id

        admin_user_list = []
        if 'id' in request.GET and request.GET['id']:
            work_order = get_object_or_404(WorkOrder, pk=request.GET['id'])
            work_order_log = work_order.workorderlog_set.filter(type='0').order_by('create_time')  # 关联表查询方法
            people = work_order.people
            if people:
                ret['people'] = [people]
                if '|' in people:
                    tem_people = people.split('|')
                    people_obj = User.objects.filter(id__in=tem_people).values('id', 'name')
                    ret['people'] = people_obj

            try:
                role = Role.objects.get(title="管理")
                admin_user_ids = role.userprofile_set.values('id')
                for admin_user_id in admin_user_ids:
                    admin_user_list.append(admin_user_id['id'])
            except Exception:
                pass
            user_list = [x.creator.id for x in work_order_log]  # 审批过的人
            user_list += [work_order.cretor_id, work_order.next_user_id]  # 自己和当前审批人
            cashier = SpecialRole.objects.filter(title__in = ['0','1']) # 出纳0, CFO1
            if cashier:
                for i in cashier:
                    user_list.append(i.user.id)
            user_list.extend(admin_user_list)

            # 和工单无关联的用户禁止通过手动指定ID的形式非法获取数据
            if user_id == work_order.cretor_id:
                ret['ban'] = 'ban'
            elif request.user.id in user_list:
                ret['work_order'] = work_order
                # ret['work_order_record'] = work_order_record
                ret['work_order_log'] = work_order_log
            else:
                ret['ban'] = 'ban'
        return render(request, 'personal/workorder/apply_app_update_detail.html', ret)


class WorkOrderAppLogView(LoginRequiredMixin, View):
    """
    审批历史页面
    """

    def get(self, request):
        ret = Menu.getMenuByRequestUrl(url=request.path_info)
        # app_log = WorkOrderLog.objects.filter(creator=request.user)
        type_list = to_list(WorkOrderLog.type_choices)
        record_list = to_list(WorkOrderLog.record_type_choices)
        ret['type_list'] = type_list
        ret['record_list'] = record_list
        return render(request, 'personal/workorder/workorder_app_log.html', ret)

class APPLogListView(LoginRequiredMixin, View):
    """
    审批历史列表
    """

    def get(self, request):
        fields = ['id', 'order_id__id', 'order_id__number', 'order_id__title', 'type', 'order_id__structure__title',
                  'create_time',  'order_id__cretor__name', 'record_type', 'order_id__cost']
        filters = dict(creator = request.user)
        if request.GET.get('number'):
            filters['order_id__number'] = request.GET.get('number')
        if request.GET.get('record_type'):
            filters['record_type'] = request.GET.get('record_type')
        if request.GET.get('app_type'):
            filters['type'] = request.GET.get('app_type')
        if request.GET.get('cretor'):
            filters['order_id__cretor__name'] = request.GET.get('cretor')
        # l = WorkOrderLog.objects.filter(**filters).values(*fields).order_by('-create_time')
        # ret = ""
        ret = dict(data=list(WorkOrderLog.objects.filter(**filters).values(*fields).order_by('-create_time')))
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type='application/json')


class WorkOrderFlowCashierView(LoginRequiredMixin, View):
    """
    审批流程出纳设置
    """

    def get(self, request):
        ret = Menu.getMenuByRequestUrl(url=request.path_info)
        users = User.objects.all().values('id', 'name')
        cashier = SpecialRole.objects.filter(title='0').first()
        CFO = SpecialRole.objects.filter(title='1').first()
        ret['users'] = users
        ret['cashier'] = ''
        ret['CFO'] = ''
        if cashier:
            ret['cashier'] = cashier.user.id
        if CFO:
            ret['CFO'] = CFO.user.id
        return render(request, 'personal/workorder/workorder_flow_cashier.html', ret)

    def post(self, request):
        res = {}
        ret_data = json.loads(request.body.decode())
        user_id = ret_data.get('user_id')
        if user_id:
            cashier = SpecialRole.objects.filter(title=ret_data.get('job_type')).first()
            if cashier:
                cashier.user_id = user_id
            else:
                cashier = SpecialRole(title=ret_data.get('job_type'), user_id=user_id)
            cashier.save()
            res['status'] = 'success'
        return HttpResponse(json.dumps(res), content_type='application/json')
