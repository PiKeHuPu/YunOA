$(document).ready(function () {
    //初始化多选列表
    $('#process').multiSelect({keepOrder: true});
    $('#carbonSe').multiSelect();

});

var url = "/system/personal/workorder_flow/detail";

$("#btnSave").click(function () {
    var data = verify();
    if (data === false) {
        return
    }
    console.log(data);

    $.ajax({
        type: 'POST',
        url: url,
        data: JSON.stringify(data),
        contentType: "application/json; charset=UTF-8",
        dataType: "json",
        success: function (msg) {
            if (msg.result) {
                layer.alert('数据保存成功！', {icon: 1}, function (index) {
                    parent.layer.closeAll(); //关闭所有弹窗
                });
            } else {
                layer.alert('数据保存失败', {icon: 5});
                //$('errorMessage').html(msg.message)
            }
            return;
        }
    });
});


function postSuccess(msg) {
    if (msg.result) {
        layer.alert('数据保存成功！', {icon: 1}, function (index) {
            parent.layer.closeAll(); //关闭所有弹窗
        });
    } else {
        layer.alert('数据保存失败', {icon: 5});
        //$('errorMessage').html(msg.message)
    }
    return;
}

function isError(data, info) {
    if (data == null || data == "") {
        layer.alert('请' + info, {icon: 5});
        return true
    }
}

function isError2(data) {
    if (data == null || data == "") {
        return true
    } else {
        return false
    }
}

function verify() {
    var structure = $("#structure").val();
    var order_type = $("#order_type").val();
    var pro_type = $("#pro_type").val();
    // 审批流程
    var p = $("#ms-process .ms-selection").find("li:visible");
    var process = muiGetVal(p);
    // 抄送值, 不是必须
    var c = $("#ms-carbonSe .ms-selection").find("li:visible");
    var carbon = muiGetVal(c);
    // 条件审批
    var factor_type = $("#factor_type").val();
    var factor = $("#factor").val();
    var factor_process = $("#factor_process").val();

    var factor_itm ='';
    if (isError(structure, '选择部门')) {
        return false
    } else if (isError(order_type, '选择事件类别')) {
        return false
    } else if (isError(pro_type, '选择申请类别')) {
        return false
    } else if (process.length == 0) {
        layer.alert('请记录审批基本流程', {icon: 5});
        return false
    } else if (factor_type || factor || factor_process) {
        if (!(isError2(factor_type) === false && isError2(factor) === false && isError2(factor_process) === false)) {
            layer.alert('如果流程带有条件,请完全填写条件信息', {icon: 5});
            return false
        } else {
            factor_itm = '&'+factor_process
        }}
    var i;
    var processInfo = "", carbonInfo = "";
    for (i in process) {
        if (processInfo === "") {
            processInfo = userInfo[process[i]]
        } else {
            processInfo += "|"+ userInfo[process[i]];
        }

        // processInfo.push(userInfo[process[i]])
    }
    processInfo += factor_itm;

    for (i in carbon) {
        var car = carbon[i].replace(/\ +/g,"").replace(/[\r\n]/g,"");
        if (carbonInfo === "") {
            carbonInfo = userInfo[car]
        } else {
            carbonInfo += "|"+ userInfo[car];
        }
        // carbonInfo.push(userInfo[carbon[i]])
    }
    var retData = {
        "structure": structure,
        "order_type": order_type,
        "pro_type": pro_type,
        "process": processInfo,
        "carbon": carbonInfo,
        "factor_type": factor_type,
        "factor": factor,
        "factor_process": factor_process,
        "id": flow_id
    };
    console.log(retData);
    return retData

}

/* 获取multiselete */
function muiGetVal(p) {
    var muiVal = [];
    p.each(function () {
        muiVal.push($(this).text())
    });
    return muiVal
}

/*点取消刷新新页面*/
$("#btnCancel").click(function () {
    window.location.reload();

});