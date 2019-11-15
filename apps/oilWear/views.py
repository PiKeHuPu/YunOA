import json

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.views import View

from rbac.models import Menu
from system.models import SystemSetup
from users.models import UserProfile
from .models import Vehicle, Operator

User = get_user_model()


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

        ret = dict(data=list(Vehicle.objects.filter(**filters).values(*fields).filter(is_delete=False).order_by('-create_time')))
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