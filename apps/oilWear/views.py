import json

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.test.testcases import to_list
from django.views import View

from personal.models import WorkOrder
from rbac.models import Menu
from system.models import SystemSetup
from users.models import UserProfile
from .models import Vehicle, Operator, OilWear

User = get_user_model()


def oilWearManager(user_id):
    """
    判断用户是否为油耗表管理员
    :param user_id:
    :return:
    """
    user = User.objects.get(id=user_id)
    roles = user.roles.all()
    for role in roles:
        if role.id == 21:
            return True
    return False


class VehicleManageView(LoginRequiredMixin, View):
    """
    车辆管理页面
    """

    def get(self, request):
        ret = Menu.getMenuByRequestUrl(url=request.path_info)
        ret.update(SystemSetup.getSystemSetupLastData())
        return render(request, "oilWear/vehicle_list.html", ret)


class VehicleCreateView(LoginRequiredMixin, View):
    """
    车辆新增页面
    """

    def get(self, request):
        ret = dict()
        users = UserProfile.objects.all()
        ret['users'] = users

        vehicle_id = request.GET.get('id')
        if vehicle_id:
            vehicle = Vehicle.objects.get(id=vehicle_id)
            ret['vehicle'] = vehicle
            try:
                operator = vehicle.operator_set.all()[0].operator
                ret['operator'] = operator
            except:
                pass

        return render(request, "oilWear/vehicle_create.html", ret)

    def post(self, request):
        res = dict(result=False)
        user_id = request.session.get('_auth_user_id')
        if 'id' in request.POST and request.POST['id']:
            vehicle = get_object_or_404(Vehicle, pk=request.POST.get('id'))
        else:
            vehicle = Vehicle()
        vehicle.license_plate = request.POST.get('license_plate')
        vehicle.department = request.POST.get('department')
        vehicle.type = request.POST.get('vehicle_type')
        vehicle.creator_id = user_id
        vehicle.save()

        if request.POST.get('operator'):
            operator = Operator()
            operator.operator_id = request.POST.get('operator')
            operator.vehicle_id = vehicle.id
            operator.save()

        res['result'] = True
        return HttpResponse(json.dumps(res), content_type='application/json')


class VehicleListView(LoginRequiredMixin, View):
    """
    获取车辆列表
    """

    def get(self, request):
        fields = ['id', 'license_plate', 'department', 'type', 'create_time']
        filters = dict()
        if request.GET.get('number'):
            filters['license_plate'] = request.GET.get('number')

        ret = dict(data=list(
            Vehicle.objects.filter(**filters).values(*fields).filter(is_delete=False).order_by('-create_time')))
        # 获取载具管理员
        for car in ret['data']:
            operator_list = Operator.objects.filter(vehicle_id=car['id'])
            if operator_list:
                operator = []
                if len(operator_list) <= 3:
                    for i in operator_list:
                        operator.append(i.operator.name)
                    operator = ",".join(operator)
                    car['operator'] = operator
                else:
                    for i in operator_list[:3]:
                        operator.append(i.operator.name)
                    operator = ",".join(operator)
                    operator += " ..."
                    car['operator'] = operator
            else:
                car['operator'] = ""

        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type='application/json')


class VehicleAdmView(LoginRequiredMixin, View):
    """
    修改载具管理员
    """

    def get(self, request):
        ret = dict()
        if 'id' in request.GET and request.GET['id']:
            vehicle = get_object_or_404(Vehicle, pk=int(request.GET.get('id')))
            operator_obj_list = vehicle.operator_set.all()
            operator_id_list = []
            for operator in operator_obj_list:
                operator_id_list.append(operator.operator_id)
            added_adms = User.objects.filter(id__in=operator_id_list)
            all_adms = User.objects.exclude(username='admin')
            un_add_adms = set(all_adms).difference(added_adms)
            ret = dict(vehicle=vehicle, added_users=added_adms, un_add_users=list(un_add_adms))
        return render(request, 'oilWear/vehicle_adm.html', ret)

    def post(self, request):
        res = dict(result=False)
        id_list = None
        vehicle = get_object_or_404(Vehicle, pk=int(request.POST.get('id')))
        if 'to' in request.POST and request.POST['to']:
            id_list = map(int, request.POST.getlist('to', []))
            id_list = list(id_list)
        Operator.objects.filter(vehicle_id=vehicle.id).delete()
        if id_list:
            for user in User.objects.filter(id__in=id_list):
                operator = Operator()
                operator.operator = user
                operator.vehicle = vehicle
                operator.save()
        res['result'] = True
        return HttpResponse(json.dumps(res), content_type='application/json')


class VehicleDeleteView(LoginRequiredMixin, View):
    """
    删除载具
    """

    def post(self, request):
        res = dict()
        vehicle = get_object_or_404(Vehicle, pk=int(request.POST.get('id')))
        vehicle.is_delete = True
        vehicle.save()
        res['success'] = True
        return HttpResponse(json.dumps(res), content_type='application/json')


class OilOrderView(LoginRequiredMixin, View):
    """
    油耗表
    """

    def get(self, request):
        ret = dict()
        user_id = request.session.get("_auth_user_id")

        if oilWearManager(user_id):
            vehicle_list = Vehicle.objects.filter(is_delete=False)
        else:
            vehicle_id = list(Operator.objects.values("vehicle_id").filter(operator_id=user_id, vehicle__is_delete=False))
            vehicle_id_list = set()
            for i in vehicle_id:
                vehicle_id_list.add(i["vehicle_id"])
            vehicle_list = Vehicle.objects.filter(id__in=vehicle_id_list)

        ret["vehicle_list"] = vehicle_list
        return render(request, "oilWear/oil_order.html", ret)

    def post(self, request):
        """
        车牌号查询ajax
        :param request:
        :return:
        """
        fields = ["id", "vehicle_id__license_plate", "vehicle_id__type", "vehicle_id__department", "operator__name", "refuel_time", "mileage", "weight", "price", "amount", "remark", 'operate_time']

        user_id = request.session.get("_auth_user_id")
        vehicle_id = list(Operator.objects.values("vehicle_id").filter(operator_id=user_id, vehicle__is_delete=False))
        vehicle_id_list = set()
        for i in vehicle_id:
            vehicle_id_list.add(i["vehicle_id"])

        filters = dict()
        if request.POST.get("license_plate"):
            filters["vehicle_id"] = request.POST.get("license_plate")

        if oilWearManager(user_id):
            ret = dict(data=list(OilWear.objects.filter(**filters, vehicle__is_delete=False).values(*fields).order_by('-operate_time')))
        else:
            ret = dict(data=list(OilWear.objects.filter(**filters, vehicle_id__in=vehicle_id_list).values(*fields).order_by('-operate_time')))
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type='application/json')


class OilOrderCreateView(LoginRequiredMixin, View):
    """
    新建油耗记录
    """

    def get(self, request):
        ret = dict()
        user_id = request.session.get("_auth_user_id")
        if oilWearManager(user_id):
            rels = Operator.objects.filter(vehicle__is_delete=False)
        else:
            rels = Operator.objects.filter(operator_id=user_id, vehicle__is_delete=False)
        ret["rels"] = rels
        return render(request, "oilWear/oil_order_create.html", ret)

    def post(self, request):
        res = dict()
        try:
            operator_id = request.session.get("_auth_user_id")
            refuel_time = request.POST.get("refuel_time")
            mileage = request.POST.get("mileage")
            weight = request.POST.get("weight")
            price = request.POST.get("price")
            amount = request.POST.get("amount")
            remark = request.POST.get("remark")
            vehicle_id = request.POST.get("license_plate")

            oil_order = OilWear()
            oil_order.operator_id = operator_id
            oil_order.refuel_time = refuel_time
            oil_order.mileage = mileage
            oil_order.weight = weight
            oil_order.price = price
            oil_order.amount = amount
            oil_order.remark = remark
            oil_order.vehicle_id = vehicle_id
            oil_order.save()
            res["result"] = True
        except:
            pass
        return HttpResponse(json.dumps(res), content_type='application/json')


class OilStatisticView(LoginRequiredMixin, View):
    """
    油耗统计
    """
    def get(self, request):
        ret = dict()
        user_id = request.session.get("_auth_user_id")
        if oilWearManager(user_id):
            vehicle_list = Vehicle.objects.filter(is_delete=False)
        else:
            vehicle_id = list(Operator.objects.values("vehicle_id").filter(operator_id=user_id, vehicle__is_delete=False))
            vehicle_id_list = set()
            for i in vehicle_id:
                vehicle_id_list.add(i["vehicle_id"])
            vehicle_list = Vehicle.objects.filter(id__in=vehicle_id_list)
        ret["vehicle_list"] = vehicle_list
        return render(request, "oilWear/oil_statistic.html", ret)

    def post(self, request):
        """
        油耗统计列表
        :param request:
        :return:
        """
        fields = ["id", "vehicle_id__license_plate", "vehicle_id__type", "vehicle_id__department", "operator__name",
                  "refuel_time", "mileage", "weight", "price", "amount", "remark", 'operate_time']
        filters = dict()
        # 三个字段都获取到后查询
        if request.POST.get("license_plate") and request.POST.get("start_time") and request.POST.get("end_time"):
            filters["vehicle_id"] = request.POST.get("license_plate")
            start_time = request.POST.get("start_time")
            end_time = request.POST.get("end_time")
            ret = dict(data=list(OilWear.objects.filter(**filters, refuel_time__range=(start_time, end_time)).values(*fields).order_by('-operate_time')))
            # 统计数据
            if ret['data']:
                num = len(ret['data'])

                mileage = ret['data'][0]['mileage'] - ret['data'][-1]['mileage']
                if mileage % 1 == 0:
                    mileage = int(mileage)

                weight = 0
                amount = 0
                for i in ret['data']:
                    weight += i['weight']
                    amount += i['amount']

                weight = round(weight, 2)
                amount = round(amount, 2)
                if weight % 1 == 0:
                    weight = int(weight)
                if amount % 1 == 0:
                    amount = int(amount)

                if mileage != 0:
                    oilWear = (weight - ret['data'][0]["weight"]) / mileage * 100
                    oilWear = "%.2f" % oilWear
                else:
                    oilWear = "无法计算油耗"

                statistic_str = "总共有<span class='stst'>" + str(num) + "</span>条记录，汽车行驶<span class='stst'>" + str(mileage) + "</span>公里，总加油量为<span class='stst'>" + str(weight) + "</span>升，共花费<span class='stst'>" + str(amount) + "</span>元,油耗为：<span class='stst'>" + str(oilWear) + "</span>。"
                ret["statistic_str"] = statistic_str
            else:
                ret["statistic_str"] = "该车辆此时间段暂无记录"
            ret["success"] = True
        else:
            ret = dict(data=list(OilWear.objects.filter(id=-1)))
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type='application/json')

