# -*- coding: UTF-8 -*-
# __author__ : RobbieHan
# __data__  : 2017/12/8


from django.conf.urls import url

from personal import views_work_order

urlpatterns = [
    url(r'^workorder_flow/list$', views_work_order.WorkOrderFlowListView.as_view(), name="workorder_flow_list"),
    url(r'^workorder_flow/$', views_work_order.WorkOrderFlowView.as_view(), name="workorder_flow"),
    url(r'^workorder_flow/detail$', views_work_order.WorkOrderFlowDetailView.as_view(), name="workorder_flow_detail"),
    url(r'^workorder_flow/cashier$', views_work_order.WorkOrderFlowCashierView.as_view(), name="workorder_flow_cashier"),
]
