$(function () {
    $(".select2").select2();
    if (ap_invoice) {
        $('#invoice').val(ap_invoice).trigger('change')
    }
    if (ap_people) {
        $('#people').val(ap_people).trigger('change')
    }
    if (ap_transport) {
        $('#transport').val(ap_transport).trigger('change')
    }
    // all_fee计算
    $("#tran_fee").blur(function () {
        allFee();
    });
    $("#acco_fee").blur(function () {
        allFee();
    });
    $("#food_fee").blur(function () {
        allFee();
    });
    $("#rece_fee").blur(function () {
        allFee();
    });
    $("#other_fee").blur(function () {
        allFee();
    });

    showFile();

});

/*input 时间输入选择*/
$(".form_datetime").datetimepicker({
    language: 'zh',
    //weekStart: 1,
    //todayBtn:  1,
    autoclose: 1,
    todayHighlight: 1,
    //startView: 2,
    forceParse: 0,
    showMeridian: 1,
    format: 'yyyy-mm-dd hh:ii',
}).on('changeDate', function (ev) {
    $(this).datetimepicker('hide');
});

// 显示提交文件
var file_be = new Vue({
    el: "#file_be",
    data: {seen: false}
});
var file_no = new Vue({
    el: "#file_no",
    data: {seen: false}
});

function fileUP () {
    $("#file_content").fileinput({
            language: "zh",
            showPreview: false,
            showUpload: false,
            uploadUrl: "/personal/workorder_Icrt/upload",
            allowedFileExtensions: ['jpg', 'gif', 'png'],
            uploadExtraData: {
                id: ap_id,
            },
            maxFileCount: 1,
            maxFileSize: 5120
        });
}

function showFile() {
    if (file_content) {
        file_be.seen = true;
        file_no.seen = false;
    } else {
        fileUP();
        file_no.seen = true;
        file_be.seen = false;
    }
}


function fileRe() {
    fileUP();
    file_no.seen = true;
    file_be.seen = false;
}

// all_fee计算
function allFee() {
    var all = 0;
    if (ap_type == '0') {

    } else if (ap_type == '1') {
        all = Number($("#tran_fee").val()) +
            Number($("#acco_fee").val()) +
            Number($("#food_fee").val()) +
            Number($("#rece_fee").val()) +
            Number($("#other_fee").val())
    }
    $("#all_fee").val(all)
}

// 数据验证
function isError(data, info) {
    if (data == null || data == "") {
        layer.alert( info, {icon: 5});
        return true
    }
}

//   | 拼接数据
function temData(data) {
    var tem = "";
    if (data === null) {
        tem = ""
    } else {
        for (i in data) {
            if (tem === "") {
                tem = data[i]
            } else {
                tem += "|" + data[i]
            }
        }
    }
    return tem
}

// 提交数据


function verify() {
    var title = $("#title").val(),
        type = ap_type,
        all_fee = $("#all_fee").val(),


        invoice_type = $("#invoice").val(),
        bank_account = $("#bank-account").val(),

        payee = $("#payee").val(),
        bank_info = $("#bank-info").val(),
        feetype = $("#feetype").val(),
        check_img = $("#check_img").val();


    var tem_invoice = temData(invoice_type);

    if (ap_type == '1') {    // 出差
        var
            tran_fee = $("#tran_fee").val(),
            acco_fee = $("#acco_fee").val(),
            food_fee = $("#food_fee").val(),
            rece_fee = $("#rece_fee").val(),
            other_fee = $("#other_fee").val(),
            detail = $("#detail").val(),
            people = $("#people").val(),
            transport = $("#transport").val(),
            becity = $("#becity").val(),
            destination = $("#destination").val(),
            start_time = $("#start-time").val(),
            end_time = $("#end-time").val(),
            completion_info = $("#completion_info").val();
        var tem_people = temData(people),
            tem_transport = temData(transport);

    }

    var r_num = /^\d*$/; //全数字

    if (isError(title, '请填写工作内容')) {
        return false
    } else if (isError(all_fee, '请填写总费用')) {
        return false
    } else if (isError(invoice_type, '请选择发票类型')) {
        return false
    } else if (isError(bank_account, '请输入银行账号')) {
        return false
    } else if (bank_account.length < 5 || bank_account.length > 30) {
        layer.alert('留意银行卡号长度', {icon: 5});
        return false
    } else if (!r_num.exec(bank_account)) {
        layer.alert('银行卡号必须全为数字', {icon: 5});
        return false
    } else if (isError(payee, '请输入收款方')) {
        return false
    } else if (isError(bank_info, '请输入开户行')) {
        return false
    }

    if (ap_type == '1') {
        if (isError(start_time, '请填写开始时间')) {
            return false
        } else if (isError(end_time, '请填写结束时间')) {
            return false
        } else if (isError(tran_fee, '请填写交通费用')) {
            return false
        } else if (isError(acco_fee, '请填写住宿费用')) {
            return false
        } else if (isError(food_fee, '请填写餐饮费用')) {
            return false
        } else if (isError(rece_fee, '请填写招待费用')) {
            return false
        } else if (isError(becity, '请输入出发地点')) {
            return false
        } else if (isError(destination, '请输入目标地点')) {
            return false
        } else if (isError(transport, '情选择交通工具')) {
            return false
        } else if (isError(completion_info, '请输入完成情况')) {
            return false
        }
    }


    var retData = {
        id: id,
        title: title,
        type: type,
        all_fee: all_fee,
        invoice_type: tem_invoice,
        bank_account: bank_account,
        payee: payee,
        bank_info: bank_info,
        feetype: feetype,
        check_img: check_img,
    };
    if (ap_type == '1') {
        retData['people'] = tem_people;
        retData['transport'] = tem_transport;
        retData['becity'] = becity;
        retData['destination'] = destination;
        retData['transport'] = tem_transport;
        retData['completion_info'] = completion_info;
        retData['tran_fee'] = tran_fee;
        retData['food_fee'] = food_fee;
        retData['rece_fee'] = rece_fee;
        retData['acco_fee'] = acco_fee;
        retData['other_fee'] = other_fee;
        retData['start_time'] = start_time;
        retData['end_time'] = end_time;
        retData['detail'] = detail;
    }
    return retData

}


var url = "/personal/workorder_ap_cost/update";

$("#btnSave").click(function () {
    var data = verify();
    if (data === false) {
        return
    }
    $.ajax({
        type: 'POST',
        url: url,
        data: JSON.stringify(data),
        contentType: "application/json; charset=UTF-8",
        cache: false,
        beforeSend: function () {
            this.layerIndex = layer.load(1, {
                shade: [0.1, '#fff'] //0.1透明度的白色背景
            });
        },
        success: function (msg) {
            layer.closeAll('loading');
            if (msg.status == 'success') {
                // 上传附件
                if ($(".file-caption-name")[0]){
                    if ($(".file-caption-name")[0].title != "") {
                        $("#file_content").fileinput("upload");
                    }
                }
                layer.alert('报销提交成功！', {icon: 1}, function (index) {
                    parent.layer.closeAll(); //关闭所有弹窗
                });
            } else if (msg.status == 'fail') {
                layer.alert(msg.work_order_form_errors, {icon: 5});
            } else if (msg.status == 'submit') {
                layer.alert('工单申请已提交，邮件发送失败！', {icon: 0}, function (index) {
                    parent.layer.closeAll(); //关闭所有弹窗
                });
            } else if (msg.status == 'submit_send') {
                layer.alert('工单申请已提交,邮件发送成功！', {icon: 1}, function (index) {
                    parent.layer.closeAll(); //关闭所有弹窗
                });
            }
        }
    });

});
