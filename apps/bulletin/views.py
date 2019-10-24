# Create your views here.

import json
import re
from django.contrib.auth import get_user_model
from django.shortcuts import render
from django.shortcuts import get_object_or_404

User = get_user_model()

from django.views.generic.base import View
from django.http import HttpResponse
from django.core.serializers.json import DjangoJSONEncoder

from .models import Bulletin
from .models import BulletinType
from .form import BulletinUpdateForm
from .form import BulletinCreateForm
from rbac.models import Menu
from utils.mixin_utils import LoginRequiredMixin
from system.models import SystemSetup


class ShowView(LoginRequiredMixin, View):
    """
    弹窗展示页
    """

    def get(self, request):
        fields = ['title', 'id', 'type__title', 'status', 'create_time', 'type__status', 'file_content']
        data=list(Bulletin.objects.filter(type__status='1', status='1').values(*fields).order_by('-create_time'))
        ret = dict()
        tem_dict = {}
        for i in data:
            type_title = i.get('type__title')
            if not tem_dict.get(type_title):
                tem_dict[type_title] = []
            tem_dict[type_title].append(i)
        ret['data'] = tem_dict
        ret['status'] = 'success'
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type='application/json')

class ManageView(LoginRequiredMixin, View):
    """
    公告管理
    """
    def get(self, request):
        ret = Menu.getMenuByRequestUrl(url=request.path_info)
        return render(request, 'bulletin/bulletin_manage.html', ret)

class ListView(LoginRequiredMixin, View):
    """
    公告list
    """
    def get(self, request):
        fields = ['title', 'id', 'type__title', 'status', 'create_time', 'type__status', 'file_content']
        ret = dict(
            data = list(Bulletin.objects.filter().values(*fields).order_by('-create_time'))
        )
        ret['status'] = 'success'
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type='application/json')




class CreateView(LoginRequiredMixin, View):
    """
    新建/更新公告
    """
    def get(self, request):
        bu_type = BulletinType.objects.all()
        ret = {'bu_type': bu_type}
        id = request.GET.get('id')
        if id:
            bulletin = get_object_or_404(Bulletin, pk=str(id))
            ret['bulletin'] = bulletin

        return render(request, 'bulletin/bulletin_create.html', ret)


    def post(self, request):
        res = dict()
        ret_data = request.POST
        id = ret_data.get('id')
        file_id = ret_data.get('file_id')

        # 更新
        if id:
            bulletin = get_object_or_404(Bulletin, pk=str(id))
            # 更新文件
            if file_id:
                bulletin_form = BulletinUpdateForm(request.POST, request.FILES, instance=bulletin)
                if bulletin_form.is_valid():
                    bulletin_form.save()

            # 更新名称和类型
            else:
                bulletin.title = ret_data.get('title')
                bulletin.type_id = ret_data.get('type')
                bulletin.save()
        else:
            bulletin = Bulletin()
            bulletin_form = BulletinCreateForm(request.POST, request.FILES, instance=bulletin)
            if bulletin_form.is_valid():
                bulletin_form.save()
        res['status'] = 'success'
        return HttpResponse(json.dumps(res, cls=DjangoJSONEncoder), content_type='application/json')

class UpdateOtherView(LoginRequiredMixin, View):
    """
    get：打开文件替换页面。post更新停用，启用
    """
    def get(self, request):
        ret = {}
        id = request.GET.get('id')
        if id:
            bulletin = get_object_or_404(Bulletin, pk=str(id))
            ret['bulletin'] = bulletin
        return render(request, 'bulletin/bulletin_file_update.html', ret)

    def post(self, request):
        res = dict()
        ret_data = json.loads(request.body.decode())
        id = ret_data.get('id')
        status = ret_data.get('status')
        if id:
            bu = get_object_or_404(Bulletin, pk=str(id))
            if status != None:
                bu.status = str(status)
            bu.save()
        res['status'] = 'success'
        return HttpResponse(json.dumps(res, cls=DjangoJSONEncoder), content_type='application/json')



class CreateTypeView(LoginRequiredMixin, View):
    """
    新建公告类型
    """
    def get(self, request):
        bu_type = BulletinType.objects.all()
        ret = {'bu_type': bu_type}
        return render(request, 'bulletin/bulletin_type.html', ret)

    def post(self, request):
        res = dict()
        ret_data = json.loads(request.body.decode())
        id = ret_data.get('id')
        status = ret_data.get('status')
        title = ret_data.get('title')
        if id:
            bu_type = get_object_or_404(BulletinType, pk=str(id))
            if status:
                bu_type.status = status
            if title:
                bu_type.title = title
        else:
            bu_type = BulletinType(title=title, status='1')
        bu_type.save()
        res['status'] = 'success'
        return HttpResponse(json.dumps(res, cls=DjangoJSONEncoder), content_type='application/json')
