function get_confirm() {
    var name = $('#jobname').text();
    var btn = $('#submit').button('loading');
    $.get("./war?name=" + name,
        function (data, status) {
            if (data == "true") {
                btn.button('reset');
                $('#myconfirm').modal('hide');
                location.reload();
            } else {
                var info = JSON.parse(data)
                $("#force_commit").css("display", "inline")
                $("#deploy_body").replaceWith("<b>Hi,还有" + info['count'] + "次代码提交没有被确认！ 它们的作者是：" + info['author'])
            }
        }
    );
}

function force_commit() {
    var name = $('#jobname').text();
    location.href = "./force_commit?name=" + name
}

function get_console(name, id) {
    $.get("./get_console?name=" + name + "&id=" + id,
        function (data, status) {
            if (status == "success") {
                $('#console').text("hello console")
            } else {
                $('#console').text("failed")
            }
        }
    )
}

$('#console').on('show.bs.modal', function (event) {
    var button = $(event.relatedTarget); // Button that triggered the modal
    var recipient = button.data('whatever');
    var name = $('#jobname').text();
    var id = button.data('jobid');
    if (!id) {
        id = 'magic'
    }
    $.get("./get_console?name=" + name + "&id=" + id,
        function (data, status) {
            if (status == "success") {
                $('#console_body').empty().append("<b>Hello Follow</b></br>" + data);
                //var modal = $(this)
                //modal.find('#console_body').text('New message to</br>' + "data")
            } else {
                $('#console_body').text("failed")
            }
        }
    );
    // Extract info from data-* attributes
    // If necessary, you could initiate an AJAX request here (and then do the updating in a callback).
    // Update the modal's content. We'll use jQuery here, but you could use a data binding library or other methods instead.

});


$(".btn-xs").click(
    function () {
        var bt = $(this).text();
        $("#whichbutton").text(bt)
    }
);

$("#list1").click(
    function () {
        $("#t_list").toggle('slow')
    }
);

$("#list2").click(
    function () {
        $("#p_list").toggle('slow')
    }
);

$("#submit_to_qa").click(
    function () {
        var pass = 0;
        $("#p_list").find("input").each(
            function () {
                if ($(this)[0].checked) {
                    pass = ++pass
                }
            }
        )
        if (pass < 1) {
            $("#modal-res").replaceWith('你必须确认提交代码涉及到那些项目!');
            $("#myconfirm").modal('show')
        } else {
            var author = $("#author").attr('value');
            $.get('./submit_to_qa?' + "author=" + author,
                function (data, status) {
                    if (data == 'ok') {
                        $("#modal-res").replaceWith('成功提交了代码信息!');
                        $("#myconfirm").modal('show')

                    } else {
                        $("#modal-res").replaceWith('出现错误啦!' + data);
                        $("#myconfirm").modal('show')
                    }
                }
            )
        }

    }
);

$("#pass_projectid > li").click(
    function () {
        var pid = $(this).parent().attr('value');
        var cmd = $(this).attr('cmd');
        $.get('./uitp?pid=' + pid + "&cmd=" + cmd,
            function (data, status) {
                if (status == "success") {
                    if (cmd == "show") {
                        $("#console_body").replaceWith(data);
                        $("#filelist").modal('show')
                    } else {
                        $("#output").modal('show')
                    }
                } else {
                    alert("failed")
                }
            }
        )
    }
);

$("#cancel_selected").click(
    function () {
        alert("get selected")
    }
);

$("#close_fl").click(
    function () {
        $("#console_body").replaceWith("null");
    }
)

$("#p_list input").click(
    function () {
        var status = $(this)[0].checked;
        var id = $(this).attr('project_id');

        //jQuery对象和DOM对象是什么
        //两者之间的区别
        //两者可以互相转换
        //jQuery -> DOM 用数组方式取 $("***")[0]或者$("***").get
        //DOM -> jQuery $(DOM)

        //id
        //DOM树
        if (status) {
            var cmd = "plus"

        }
        else {
            var cmd = "minus"
        }
        $.get("update_prj_info?cmd=" + cmd + "&id=" + id,
            function (data, status) {
                //alert(data + status);

            }
        )
    }
);

function do_cmd() {
    var info = $("#whichbutton").text();
    if (info == "启动") {
        var cmd = "start";
    }
    else if (info == "更新") {
        var cmd = "update";
    }
    else {
        var cmd = "stop"
    }
    $.get("./do_cmd?cmd=" + cmd,
        function (data, status) {
            obj = JSON.parse(data);
            if (obj['code'] == 0) {

                $("#myconfirm").modal('hide');
                location.reload()
            } else {
                $("#myconfirm").modal('hide');
                location.reload()
            }
        }
    )
}


$(document).ready(function () {
    setInterval('startrequest()', 2000)
});

function startrequest() {
    $('#time').text('Time：' + (new Date()).toString());
    $('#status_html_Genscript-SCM-QA').load('./get_status_html?c=Genscript-SCM-QA')
    $('#status_html_Genscript-SCM-Prod').load('./get_status_html?c=Genscript-SCM-Prod')
    $('#status_html_Genscript-SCM-Drsite').load('./get_status_html?c=Genscript-SCM-Drsite')
}

$("#close_res").click(
    function () {
        location.reload()
    }
);