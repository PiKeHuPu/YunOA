import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.views import View

from rbac.models import Menu
from system.models import SystemSetup
from users.models import UserProfile
from .models import Vehicle, Operator


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
        ret = dict(data=list(Vehicle.objects.values(*fields).order_by('id')))
        # 获取载具管理员
        for car in ret['data']:
            operator_list = Operator.objects.filter(vehicle_id=car['id'])
            if operator_list:
                operator = []
                for i in operator_list:
                    operator.append(i.operator.name)
                operator = ",".join(operator)
                car['operator'] = operator
            else:
                car['operator'] = ""

        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type='application/json')
