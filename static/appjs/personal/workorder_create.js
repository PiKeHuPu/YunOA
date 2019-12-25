/*点取消刷新新页面*/
var work_order_id = {};

function workf() {
    return work_order_id
}

$("#btnCancel").click(function () {
    window.location.reload();

});

/*input 时间输入选择*/
function datimeP() {
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
}


$(function () {


    showInfo();
    //Initialize Select2 Elements
    $(".select2").select2();
    if (work_order_people.length > 0) {
        $('#people').val(work_order_people).trigger('change')
    }
    ;
    showFile();
});


// 显示申请内容
var apply_info = new Vue({
    el: '#apply-info',
    data: {seen: false}
});
var travel_info = new Vue({
    el: '#travel-info',
    data: {seen: false}
});

var type_select = new Vue({
    el: '#order-type',
    data: {
        selected: work_order_type
    }
});

function applyOnly(){
    var is_only = document.getElementById("ao");
    if (is_only.checked) {
        document.getElementById("bank-account").readOnly="true";
        document.getElementById("payee").readOnly="true";
        document.getElementById("bank-info").readOnly="true";
        document.getElementById("invoice-type").disabled="true";
    } else {
        document.getElementById("bank-account").readOnly=false;
        document.getElementById("payee").readOnly=false;
        document.getElementById("bank-info").readOnly=false;
        document.getElementById("invoice-type").disabled=false;
    }
}

function showInfo() {
    if ($("#order-type option:checked").val() == '0'  && $("#advance").val() == '0') {
        $("#ao_div").hide();
        $("#ao").prop("checked", false);
        applyOnly();
        apply_info.seen = true;
        $("#back_info_name").text('立项申请');
        travel_info.seen = false;
    }
    else if ($("#order-type option:checked").val() == '0'  && $("#advance").val() == '1') {
        $("#ao_div").show();
        apply_info.seen = true;
        $("#back_info_name").text('立项申请');
        travel_info.seen = false;
    }
    else if ($("#order-type option:checked").val() == '1' && $("#advance").val() == '0') {
        $("#ao_div").hide();
        $("#ao").prop("checked", false);
        applyOnly();
        apply_info.seen = false;
        travel_info.seen = true;
        datimeP();
    } else if ($("#order-type option:checked").val() == '1' && $("#advance").val() == '1') {
        $("#ao_div").hide();
        $("#ao").prop("checked", false);
        applyOnly();
        apply_info.seen = true;
        $("#back_info_name").text('预支信息');
        travel_info.seen = true;
        datimeP();

    }
}

$("#order-type").on('change', function (e) {
    showInfo();
});

$("#advance").on('change', function (e) {
    showInfo();
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
            uploadUrl: "/personal/workorder_rec/upload",
            allowedFileExtensions: ['jpg', 'gif', 'png'],
            uploadExtraData: function (perviewId, index) {
                var obj = workf();
                return obj;
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



// 数据验证
function isError(data, info) {
    if (data == null || data == "") {
        layer.alert( info, {icon: 5});
        return true
    }
}

// 提交数据

function verify() {
    var number = $("#number").val(),
        title = $("#title").val(),
        type = $("#order-type").val(),
        cost = $("#cost").val(),
        start_time = $("#start-time").val(),
        end_time = $("#end-time").val(),

        invoice_type = $("#invoice-type").val(),
        bank_account = $("#bank-account").val(),
        payee = $("#payee").val(),
        bank_info = $("#bank-info").val(),
        apply_only = $("#ao").is(":checked"),
        feetype = $("#feetype").val(),


        people = $("#people").val(),
        transport = $("#transport").val(),
        becity = $("#becity").val(),
        destination = $("#destination").val(),

        advance = $("#advance").val();


    var r_num = /^\d*$/; //全数字

    if (isError(title, '请费用类型')) {
        return false
    }else if (isError(title, '请填写工作内容')) {
        return false
    } else if (isError(type, '请选择审批类型')) {
        return false
    } else if (isError(cost, '请填写申请金额')) {
        return false
    }
    if (type == '0' || advance == '1') {
        // console.log(apply_only);
        if (apply_only) {

        } else {
            if (isError(invoice_type, '请选择发票类型')) {
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
            if (isError(invoice_type, '请选择发票类型')) {
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
        }

    } else if (type == '1') {
        if (isError(transport, '情选择交通工具')) {
            return false
        } else if (isError(becity, '请输入出发地点')) {
            return false
        } else if (isError(destination, '请输入目标地点')) {
            return false
        } else if (isError(start_time, '请填写开始时间')) {
            return false
        } else if (isError(end_time, '请填写结束时间')) {
            return false
        }
    }

    var tem_people = "";
    if (people === null) {
        tem_people = ""
    } else {
        for (i in people) {
            if (tem_people === "") {
                tem_people = people[i]
            } else {
                tem_people += "|" + people[i]
            }
        }
    }

    return retData = {
        id: $("#orderId").val(),
        number: number,
        title: title,
        type: type,
        cost: cost,
        start_time: start_time,
        end_time: end_time,

        invoice_type: invoice_type,
        bank_account: bank_account,
        payee: payee,
        bank_info: bank_info,
        advance: advance,
        apply_only: apply_only,
        feetype:feetype,

        people: tem_people,
        transport: transport,
        becity: becity,
        destination: destination
    }

};

var url = "/personal/workorder_Icrt/create";

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
            // 提醒框
            if (msg.status == 'success') {
                work_order_id['id'] = msg.workorder_id;
                // 上传附件
                if ($(".file-caption-name")[0]){
                    if ($(".file-caption-name")[0].title != "") {
                    $("#file_content").fileinput("upload");
                    }
                }

                layer.alert('申请提交成功！', {icon: 1}, function (index) {
                    parent.layer.closeAll(); //关闭所有弹窗
                });
            } else if (msg.status == 'fail') {
                layer.alert(msg.errors_info, {icon: 5});
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


