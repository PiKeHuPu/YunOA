from django.conf.urls import url
from .views import *

urlpatterns = [
    # 油耗表
    url(r'^oil/order', OilOrderView.as_view(), name="oil_order"),
]