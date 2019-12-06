from adm.models import Asset, AssetInfo, User
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



