from django.conf.urls import url
from .views import OilOrderView, OilStatisticView

urlpatterns = [
    # 油耗表
    url(r'^oil/order$', OilOrderView.as_view(), name="oil_order"),
    url(r'^oil/order/statistic$', OilStatisticView.as_view(), name="oil_statistic"),
]