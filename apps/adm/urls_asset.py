# -*- coding: UTF-8 -*-
# __author__ : RobbieHan
# __data__  : 2017/12/8

from django.conf.urls import url

from adm import views_asset

urlpatterns = [

    url(r'^$', views_asset.AssetView.as_view(), name='asset'),
    url(r'^list', views_asset.AssetListView.as_view(), name="list"),
    url(r'^create', views_asset.AssetCreateView.as_view(), name="create"),
    url(r'^update', views_asset.AssetUpdateView.as_view(), name="update"),

    url(r'^detail', views_asset.AssetDetailView.as_view(), name="asset-detail"),
    url(r'^delete', views_asset.AssetDeleteView.as_view(), name='delete'),
    url(r'^upload', views_asset.AssetUploadView.as_view(), name='upload'),


    # 领取资产
    url(r'^use$', views_asset.AssetUseView.as_view(), name="use"),
    url(r'^use/list', views_asset.AssetListView.as_view(), name='use-list'),
    # 资产领取地址
    url(r'^useaddress', views_asset.AddressView.as_view(), name="asset-use-address"),

    # 领取物资查看
    url(r'^use/flow$', views_asset.AssetUseFlowView.as_view(), name="asset-use-flow"),
    url(r'^use/flow/list', views_asset.AssetUseFlowListView.as_view(), name="asset-use-flow-list"),

]


