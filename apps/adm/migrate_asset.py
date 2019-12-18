from adm.models import Asset, AssetInfo, User, AssetUseLog, AssetApprove
from users.models import Structure


def migrate_asset():
    old_assets = Asset.objects.all()
    for old_asset in old_assets:
        new_asset = AssetInfo()
        new_asset.id = old_asset.id
        new_asset.number = old_asset.assetNum
        new_asset.name = old_asset.brand
        new_asset.quantity = old_asset.assetCount
        new_asset.status = old_asset.status
        new_asset.create_time = old_asset.add_time
        if old_asset.dueremind == '1':
            new_asset.due_time = old_asset.dueDate
        new_asset.unit = old_asset.assetUnit
        new_asset.type = old_asset.model
        new_asset.remark = old_asset.desc
        new_asset.operator = User.objects.get(name=old_asset.operator)
        new_asset.department = Structure.objects.get(title='内蒙古云谷电力科技股份有限公司')
        new_asset.warehouse_id = '3'
        new_asset.save()

def migrate_asset_flow():
    old_asset_flows = AssetUseLog.objects.all()
    for old_asset_flow in old_asset_flows:
        new_asset_flow = AssetApprove()
        new_asset_flow.id = old_asset_flow.id
        new_asset_flow.proposer = User.objects.get(name=old_asset_flow.operator)
        new_asset_flow.asset_id = old_asset_flow.asset_id
        new_asset_flow.quantity = old_asset_flow.useCount
        new_asset_flow.purpose = old_asset_flow.title
        new_asset_flow.return_date = old_asset_flow.use_time
        new_asset_flow.status = "2"
        if old_asset_flow.give_back == "1":
            new_asset_flow.use_status = "2"
        elif old_asset_flow.give_back == "0":
            new_asset_flow.use_status = "1"
        new_asset_flow.create_time = old_asset_flow.add_time
        new_asset_flow.t_return_date = old_asset_flow.back_date
        new_asset_flow.return_quantity = old_asset_flow.back_count
        new_asset_flow.return_operator = old_asset_flow.back_creator
        new_asset_flow.save()


def create_no_back():
    no_back_assets = AssetApprove.objects.filter(use_status="1")
    for no_back_asset in no_back_assets:
        asset = no_back_asset.asset
        asset.id = None
        asset.save()
        asset.quantity = int(no_back_asset.quantity)
        asset.create_time = no_back_asset.asset.create_time
        asset.status = '1'
        asset.user_id = no_back_asset.proposer_id
        asset.save()
    print("done")




