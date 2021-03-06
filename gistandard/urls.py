"""gistandard URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""




from django.conf.urls import url, include
from django.views.static import serve

from assess.views import AssessDep, AssessDetail, CreateGoal, CreatePerGoal, EditSchedule, AssessScore0, YearMonth, \
    PositionStatementList, PositionStatementCreate, PositionStatementAjax, AssessGather, AssessGatherList, \
    PositionStatementShowList
from exam.views import ExamQuestionBank, ExamQuestionBankImport, ExamList, ExamTypeManage, ExamCreate, ExamQuestionEdit, \
    ExamQuestionDelete, ExamDetail, ExamShowList, ExamStart, ExamAjax, ExamScoreDetail, ExamScoreReport, ExamHistory
from gistandard.settings import MEDIA_ROOT

import xadmin

from apps.users.views_user import LoginView, IndexView, LogoutView
from personal.views import Direction, ChangeStatement, ShowStatement, Catalog, ShowCatalog
from system.views import SystemView
from adm.views import AdmView, WarehouseView, \
    WarehouseCreateView, WarehouseDeleteView, AssetView, AssetCreateView, AssetAjaxView, AssetUseFlowView, \
    AssetApplyView, AssetApproveView, AssetApproveresultView, AssetApproveHistoryView, AssetOrderDetailView, \
    AssetTransferView, FileUpload, FileList, FileRename, FileDelete, SetFileType, FileTypeAjax, FileSubType, FileShow, \
    FileTypeEditPart
from oilWear.views import OilOrderCreateView
from personal import views as personal_views
from personal import views_work_order as order
from adm.views_asset import AssetUseHtmlView, AssetUseInfoView, AssetBackView
from bulletin import views as bulletin_views
from oilWear import views as oilWear_views
from users.views_structure import StructureAssetAdmView
from worklog.views import WorkLog_Show, WorkLog_Create, WorkLog_Detail, WorkLog_Edit, WorkLog_Set, WorkRecordDep, \
    WorkRecordUser, WorkRecordTemList, WorkRecordCreate, WorkRecordAjax, WorkRecordHistory

urlpatterns = [
    url(r'^xadmin/', xadmin.site.urls),
    url(r'^media/(?P<path>.*)$', serve, {"document_root": MEDIA_ROOT}),
    url(r'^$', IndexView.as_view(), name='index'),
    # 用户登录
    url(r'^login/$', LoginView.as_view(), name='login'),
    url(r'^logout/$', LogoutView.as_view(), name="logout"),
    # 操作说明
    url(r'^direction/$', Direction.as_view(), name='direction'),
    # 档案管理目录
    url(r'^adm/catalog/$', Catalog.as_view(), name='catalog'),
    url(r'^personal/catalog/', ShowCatalog.as_view(), name="show-catalog"),
    # 系统模块
    url(r'^system/$', SystemView.as_view(), name="system"),
    url(r'^system/basic/', include('users.urls', namespace='system-basic')),
    url(r'^system/rbac/', include('rbac.urls', namespace='system-rbac')),
    url(r'^system/tools/', include('system.urls', namespace='system-tools')),
    url(r'^system/oilWear/', include('oilWear.urls', namespace='system-oilWear')),
    url(r'^system/personal/', include('personal.urls', namespace='system-personal')),
    # 资产模块
    url(r'^adm/$', AdmView.as_view(), name="adm-main"),
    url(r'^adm/bsm/', include('adm.urls', namespace='adm-bsm')),
    url(r'^adm/equipment/', include('adm.urls_equipment', namespace='adm-equipment')),
    url(r'^adm/asset/', include('adm.urls_asset', namespace='adm-asset')),
    url(r'^adm/department', StructureAssetAdmView.as_view(), name='adm-department'),
    url(r'^personal/approve/history', AssetApproveHistoryView.as_view(), name='personal-approve-history'),
    url(r'^personal/apply/detail', AssetOrderDetailView.as_view(), name='personal-apply-detail'),
    url(r'^adm/warehouse', WarehouseView.as_view(), name='adm-warehouse'),
    url(r'^adm/whCreate', WarehouseCreateView.as_view(), name='adm-warehouse-create'),
    url(r'^adm/whDelete', WarehouseDeleteView.as_view(), name='adm-warehouse-delete'),
    url(r'^adm/n_asset', AssetView.as_view(), name='adm-n-asset'),
    url(r'^adm/n_create', AssetCreateView.as_view(), name='adm-n-create'),
    url(r'^adm/ajax', AssetAjaxView.as_view(), name='adm-ajax'),
    url(r'^adm/use_flow', AssetUseFlowView.as_view(), name='adm-useflow'),
    url(r'^personal/apply', AssetApplyView.as_view(), name='personal-apply'),
    url(r'^personal/approve/result', AssetApproveresultView.as_view(), name='personal-approve-result'),
    url(r'^personal/approve', AssetApproveView.as_view(), name='personal-approve'),
    url(r'^personal/transfer', AssetTransferView.as_view(), name='personal-transfer'),
    # 工作台模块
    # 审批报销
    url(r'^personal/$', personal_views.PersonalView.as_view(), name="personal"),
    url(r'^personal/userinfo', personal_views.UserInfoView.as_view(), name="personal-user_info"),
    url(r'^personal/uploadimage', personal_views.UploadImageView.as_view(), name="personal-uploadimage"),
    url(r'^personal/passwordchange', personal_views.PasswdChangeView.as_view(), name="personal-passwordchange"),
    url(r'^personal/phonebook', personal_views.PhoneBookView.as_view(), name="personal-phonebook"),
    url(r'^personal/workorder_Icrt/$', order.WorkOrderView.as_view(), name="personal-workorder_Icrt"),
    url(r'^personal/workorder_Icrt/list', order.WorkOrderListView.as_view(), name="personal-workorder-list"),
    url(r'^personal/workorder_Icrt/create', order.WorkOrderCreateView.as_view(), name="personal-workorder-create"),
    url(r'^personal/workorder_Icrt/detail', order.WorkOrderDetailView.as_view(), name="personal-workorder-detail"),
    url(r'^personal/workorder_Icrt/delete', order.WorkOrderDeleteView.as_view(), name="personal-workorder-delete"),
    url(r'^personal/workorder_Icrt/update', order.WorkOrderUpdateView.as_view(), name="personal-workorder-update"),
    url(r'^personal/workorder_app/$', order.WorkOrderAppView.as_view(), name="personal-workorder-app"),
    url(r'^personal/workorder_app/update', order.WorkOrderAppUpdateView.as_view(),
        name="personal-workorder-app-update"),  # 更新立项审批
    url(r'^personal/workorder_app/other/detail', order.WorkOrderAppOtherDetailView.as_view(),
        name="personal-workorder-app-other-detail"),
    ## 历史
    url(r'^personal/workorder_app/log', order.WorkOrderAppLogView.as_view(),
        name="personal-workorder-app-log"),  # 立项/报销审批历史
    url(r'^personal/app/log$', order.APPLogListView.as_view(),
        name="personal-app-log"),  # 报销历史list
    # 本部门申请记录(管理员可见)
    url(r'^personal/app/de_log$', order.APPDeLogListView.as_view(),
        name="personal-app-de_log"),  # 部门记录
    url(r'^personal/app/log_content$', order.APPLogListContentView.as_view(),
        name="personal-app-log-content"),  # 部门记录列表
    ## 报销
    url(r'^personal/workorder_ap_cost/update', order.ApplyCostUpdateView.as_view(),
        name="personal-workorder_ap_cost-update"),
    url(r'^personal/workorder_ap_cost/detail', order.ApDetailView.as_view(), name="personal-workorder_ap_cost-detail"),
    url(r'^personal/workorder_ap_cost/list', order.APListView.as_view(), name="personal-workorder_ap_cost-list"),
    url(r'^personal/workorder_ap_cost/$', order.ApplyCostView.as_view(), name="personal-workorder_ap_cost"),
    url(r'^personal/workorder_ap_cost_app/$', order.ApplyCostAppView.as_view(), name="personal-workorder_ap_cost_app"),
    url(r'^personal/workorder_ap_cost_app/other_detail$', order.ApplyCostAppOtherDetailView.as_view(),
        name="personal-workorder_ap_cost_app-other_detail"),
    url(r'^personal/workorder_ap_cost_app/update', order.CostAppUpdateView.as_view(),
        name="personal-workorder_ap_cost_app-update"),  # 更新报销审批
    url(r'^update_detail', order.CostAppUpdateDetailView.as_view(),
        name="personal-workorder_ap_cost_app-update_detail"),  # 审批报销页面点击审批单号时的跳转页面
    # url(r'^personal/workorder_app/list', order.WorkOrderAppListView.as_view(), name="personal-workorder_app_list"),
    # url(r'^personal/workorder_app/send', order.WrokOrderSendView.as_view(), name="personal-workorder-send"),
    # url(r'^personal/workorder_rec/$', order.WorkOrderView.as_view(), name="personal-workorder_rec"),
    # url(r'^personal/workorder_rec/execute', order.WorkOrderExecuteView.as_view(), name="personal-workorder-execute"),
    # url(r'^personal/workorder_rec/finish', order.WorkOrderFinishView.as_view(), name="personal-workorder-finish"),
    # 上传文件
    url(r'^personal/workorder_rec/upload', order.WorkOrderUploadView.as_view(), name="personal-workorder-upload"), # 申请上传
    url(r'^personal/workorder_Icrt/upload', order.APProjectUploadView.as_view(),
        name="personal-workorder-project-upload"), # 报销上传
    # url(r'^personal/workorder_rec/return', order.WorkOrderReturnView.as_view(), name="personal-workorder-return"),

    url(r'^personal/workorder_all/$', order.WorkOrderView.as_view(), name="personal-workorder_all"),
    url(r'^personal/document/$', order.WorkOrderDocumentView.as_view(), name="personal-document"),
    url(r'^personal/document/list', order.WorkOrderDocumentListView.as_view(), name="personal-document-list"),
    ## 物料领取
    url(r'^personal/asset/use/info$', AssetUseHtmlView.as_view(), name="personal-asset-use-html"),
    url(r'^personal/asset/use$', AssetUseInfoView.as_view(), name="personal-asset-use"),
    url(r'^personal/asset/use/back$', AssetBackView.as_view(), name="personal-asset-use-back"),
    # 油耗表
    url(r'^personal/oilWear/', include('oilWear.oilWear_urls', namespace='personal-oilWear')),
    url(r'^oil/order/create', OilOrderCreateView.as_view(), name="oil_order_create"),
    ## 公告栏
    url(r'system/bulletin/create$', bulletin_views.CreateView.as_view(), name="bulletin_create"),
    url(r'system/bulletin/show$', bulletin_views.ShowView.as_view(), name="bulletin_show"),
    url(r'system/bulletin/manage$', bulletin_views.ManageView.as_view(), name="bulletin_manage"),
    url(r'system/bulletin/type$', bulletin_views.CreateTypeView.as_view(), name="bulletin_type"),
    url(r'system/bulletin/list$', bulletin_views.ListView.as_view(), name="bulletin_list"),
    url(r'system/bulletin/other/update$', bulletin_views.UpdateOtherView.as_view(), name="bulletin_other_update"),
    url(r'system/bulletin/database/update$', bulletin_views.DatabaseUpdateView.as_view(), name="database_update"),

    # 未读公告提醒
    url(r'system/bulletin/unread_bulletin$', bulletin_views.UnreadBulletinView.as_view(), name="unread_bulletin"),
    # 物资续期提醒
    url(r'due_asset', personal_views.DueAssetView.as_view(), name="due_asset"),
    # 意见反馈
    url(r'^personal/feedback_view$', personal_views.FeedbackView.as_view(), name="feedback_view"),
    url(r'feedback_create', personal_views.CreateFeedback.as_view(), name="feedback_create"),
    url(r'feedback_delete', personal_views.FeedbackDelete.as_view(), name="feedback_delete"),
    url(r'feedback_ajax', personal_views.FeedbackAjax.as_view(), name="feedback_ajax"),
    url(r'feedback_remark', personal_views.FeedbackRemark.as_view(), name="feedback_remark"),
    # 抄送
    url(r'^personal/workorder_copy/$', order.CopyTo.as_view(), name="copy_to"),
    # 考核模块
    url(r'^personal/assess_dep/$', AssessDep.as_view(), name="assess_dep"),
    url(r'^personal/assess_detail/$', AssessDetail.as_view(), name="assess_detail"),
    url(r'^personal/create_goal/$', CreateGoal.as_view(), name="create_goal"),
    url(r'^personal/create_per_goal/$', CreatePerGoal.as_view(), name="create_per_goal"),
    url(r'^personal/edit_schedule/$', EditSchedule.as_view(), name="edit_schedule"),
    url(r'^personal/assess_score/$', AssessScore0.as_view(), name="assess_score"),
    url(r'^personal/year_month/$', YearMonth.as_view(), name="year_month"),
    url(r'^personal/position_statement_show_list/$', PositionStatementList.as_view(), name="position_statement_show_list"),
    url(r'^personal/assess_gather/$', AssessGather.as_view(), name="assess_gather"),
    url(r'^personal/assess_gather_list/$', AssessGatherList.as_view(), name="assess_gather_list"),
    url(r'system/position_statement$', PositionStatementShowList.as_view(), name="position_statement"),
    url(r'system/position_statement_create$', PositionStatementCreate.as_view(), name="position_statement_create"),
    url(r'system/position_statement_ajax$', PositionStatementAjax.as_view(), name="position_statement_ajax"),
    # 档案管理
    url(r'^adm/file_upload/$', FileUpload.as_view(), name="file_upload"),
    url(r'^adm/file_list/$', FileList.as_view(), name="file_list"),
    url(r'^adm/file_rename/$', FileRename.as_view(), name="file_rename"),
    url(r'^adm/file_delete/$', FileDelete.as_view(), name="file_delete"),
    url(r'^adm/file_type_set/$', SetFileType.as_view(), name="file_type_set"),
    url(r'^adm/file_type_ajax/$', FileTypeAjax.as_view(), name="file_type_ajax"),
    url(r'^adm/file_sub_type_set/$', FileSubType.as_view(), name="file_sub_type_set"),
    url(r'^personal/file_show_list/$', FileShow.as_view(), name="file_show_list"),
    url(r'^adm/file_type_edit_part/$', FileTypeEditPart.as_view(), name="file_type_edit_part"),
    # 修改个人岗位职责
    url(r'^personal/create_statement', ChangeStatement.as_view(), name='create_statement'),
    url(r'^personal/show_statement', ShowStatement.as_view(), name='show_statement'),
    # 工作日志
    url(r'^personal/work/worklog/', WorkLog_Show.as_view(), name="worklog_show"),
    url(r'^personal/work/create/', WorkLog_Create.as_view(), name="worklog_create"),
    url(r'^personal/work/detail/', WorkLog_Detail.as_view(), name="worklog_detail"),
    url(r'^personal/work/edit/', WorkLog_Edit.as_view(),name="worklog_edit"),
    url(r'^worklog/set/$', WorkLog_Set.as_view(), name="worklog_set"),
    url(r'^personal/work/work_record_dep/', WorkRecordDep.as_view(), name="work_record_dep"),
    url(r'^personal/work/work_record_user/', WorkRecordUser.as_view(), name="work_record_user"),
    url(r'^personal/work/work_record_tem_list/', WorkRecordTemList.as_view(), name="work_record_tem_list"),
    url(r'^personal/work/work_record_tem_create/', WorkRecordCreate.as_view(), name="work_record_tem_create"),
    url(r'^personal/work/work_record_ajax/', WorkRecordAjax.as_view(), name="work_record_ajax"),
    url(r'^personal/work/work_record_history/', WorkRecordHistory.as_view(), name="work_record_history"),
    # 考试系统
    url(r'^system/exam/question_bank/', ExamQuestionBank.as_view(), name="question_bank"),
    url(r'^system/exam/question_bank_import/', ExamQuestionBankImport.as_view(), name="question_bank_import"),
    url(r'^system/exam/question_bank_edit/', ExamQuestionEdit.as_view(), name="question_bank_edit"),
    url(r'^system/exam/question_delete/', ExamQuestionDelete.as_view(), name="question_delete"),
    url(r'^system/exam/type_manage/', ExamTypeManage.as_view(), name="exam_type"),
    url(r'^system/exam/list/', ExamList.as_view(), name="exam_list"),
    url(r'^system/exam/create/', ExamCreate.as_view(), name="exam_create"),
    url(r'^system/exam/detail/', ExamDetail.as_view(), name="exam_detail"),
    url(r'^system/exam/score_report/', ExamScoreReport.as_view(), name="score_report"),
    url(r'^personal/exam/list/', ExamShowList.as_view(), name="exam_show_list"),
    url(r'^personal/exam/history/list/', ExamHistory.as_view(), name="exam_history_list"),
    url(r'^personal/exam/start/', ExamStart.as_view(), name="exam_start"),
    url(r'^personal/exam/ajax/', ExamAjax.as_view(), name="exam_ajax"),
    url(r'^personal/exam/score_detail/', ExamScoreDetail.as_view(), name="score_detail"),
]
