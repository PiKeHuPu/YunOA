from django.conf.urls import url
from .views import *


urlpatterns = [
    # 载具
    url(r'^vehicle/manage', VehicleManageView.as_view(), name="vehicle_manage"),
    url(r'^vehicle/create', VehicleCreateView.as_view(), name="vehicle_create"),
    url(r'^vehicle/list', VehicleListView.as_view(), name="vehicle_list"),
]