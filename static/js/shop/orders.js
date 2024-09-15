$(function () {
    // tabs
    $("#container .order_info ul li a").click(function (e) { 
        e.preventDefault();
        var tab_id = $(this).attr('href').replace('#','');
        $("#container .order_info .tab_container .tab_div").each(function () {
            if (($(this).is(':visible')) && ($(this).attr('id') !== tab_id)) {
                $(this).css('display','none');
                $('#'+tab_id).fadeIn('slow');
            }
        });
    });

    var CSRF_TOKEN = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

    function generate_errorsms(status, sms) {
        return `<div class="alert alert-${status ? 'success' : 'danger'} alert-dismissible fade show px-2 m-0 d-block w-100"><i class='fas fa-${status ? 'check' : 'exclamation'}-circle'></i> ${sms} <button type="button" class="btn-close d-inline-block" data-bs-dismiss="alert"></button></div>`;
    }

    // Register new and update order info
    $("#new_order_form").submit(function (e) { 
        e.preventDefault();
        
        $.ajax({
            type: 'POST',
            url: $(this).attr('action'),
            data: new FormData($(this)[0]),
            dataType: 'json',
            contentType: false,
            processData: false,
            headers: {
                'X-CSRFToken': CSRF_TOKEN
            },
            beforeSend: function() {
                $("#order_cancel_btn").removeClass('d-inline-block').addClass('d-none');
                $("#order_submit_btn").html("<i class='fas fa-spinner fa-pulse'></i> Saving").attr('type', 'button');
            },
            success: function(response) {
                $("#order_cancel_btn").removeClass('d-none').addClass('d-inline-block');
                $("#order_submit_btn").text("Save").attr('type', 'submit');

                var fdback = generate_errorsms(response.success, response.sms);
                
                $("#new_order_canvas .offcanvas-body").animate({ scrollTop: 0 }, 'slow');
                $("#new_order_form .formsms").html(fdback);
                
                if(response.update_success) {
                    $("#order_info_div").load(location.href + " #order_info_div");
                } else if(response.success) {
                    $("#new_order_form")[0].reset();
                    orders_table.draw();
                }
            },
            error: function(xhr, status, error) {
                $("#order_cancel_btn").removeClass('d-none').addClass('d-inline-block');
                $("#order_submit_btn").text("Save").attr('type', 'submit');
                var fdback = generate_errorsms(false, "Unknown error, reload & try again");
                $("#new_order_canvas .offcanvas-body").animate({ scrollTop: 0 }, 'slow');
                $("#new_order_form .formsms").html(fdback);
            }
        });
    });

    function get_dates(dt, div) {
        var mindate, maxdate, dt_start, dt_end = "";
        if (div == 'due') {
            mindate = $('#due_min_date').val();
            maxdate = $('#due_max_date').val();
        } else {
            mindate = $('#min_date').val();
            maxdate = $('#max_date').val();
        }
        if (mindate) dt_start = mindate + ' 00:00:00.000000';
        if (maxdate) dt_end = maxdate + ' 23:59:59.999999';
        return (dt === 0) ? dt_start : dt_end;
    }

    function clear_dates() {
        $('#min_date').val('');
        $('#max_date').val('');
        $('#due_min_date').val('');
        $('#due_max_date').val('');
    }

    function formatCurrency(num) {
        return num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' TZS';
    };

    $("#orders_table thead tr").clone(true).attr('class','filters').appendTo('#orders_table thead');
    var orders_table = $("#orders_table").DataTable({
        fixedHeader: true,
        processing: true,
        serverSide: true,
        ajax: {
            url: $("#orders_list_url").val(),
            type: "POST",
            data: function (d) {
                d.start_reg = get_dates(0, 'reg');
                d.end_reg = get_dates(1, 'reg');
                d.start_exp = get_dates(0, 'due');
                d.end_exp = get_dates(1, 'due');
            },
            dataType: 'json',
            headers: { 'X-CSRFToken': CSRF_TOKEN },
            dataSrc: function (json) {
                var tableFooter = $('#orders_table tfoot');
                $(tableFooter).find('tr').eq(1).find('th').eq(2).html(formatCurrency(json.grand_total));
                return json.data;
            },
        },
        columns: [
            { data: 'count' },
            { data: 'orderdate' },
            { data: 'customer' },
            { data: 'phone' },
            { data: 'price' },
            { data: 'duedate' },
            { data: 'user' },
            { data: 'action' },
        ],
        order: [[3, 'asc']],
        paging: true,
        lengthMenu: [[10, 20, 40, 50, 100, -1], [10, 20, 40, 50, 100, "All"]],
        pageLength: 10,
        lengthChange: true,
        autoWidth: true,
        searching: true,
        bInfo: true,
        bSort: true,
        orderCellsTop: true,
        columnDefs: [{
            targets: [0, 7],
            orderable: false,
        },
        {
            targets: 2,
            className: 'ellipsis',
            createdCell: function(cell, cellData, rowData, rowIndex, colIndex) {
                $(cell).attr('class', 'text-start');
            }
        },
        {
            targets: 4,
            createdCell: function(cell, cellData, rowData, rowIndex, colIndex) {
                $(cell).attr('class', 'text-end pe-2');
            }
        },
        {
            targets: 5,
            createdCell: function(cell, cellData, rowData, rowIndex, colIndex) {
                if (rowData.status < 0) {
                    $(cell).attr('class', 'text-danger');
                    $(cell).html(`<i class="fas fa-exclamation-circle"></i> `+rowData.duedate);
                } else if (rowData.status > 0) {
                    $(cell).attr('class', 'text-success');
                    $(cell).html(`<i class="fas fa-check-circle"></i> `+rowData.duedate);
                } else {
                    $(cell).html(`<i class="fas fa-clock"></i> `+rowData.duedate);
                }
            }
        },
        {
            targets: 6,
            createdCell: function(cell, cellData, rowData, rowIndex, colIndex) {
                $(cell).attr('class', 'text-start');
                if (rowData.user_type > 0) {
                    var cell_content = `<a href="${rowData.user_info}">${rowData.user}</a>`;
                    $(cell).html(cell_content);
                } else {
                    $(cell).html(rowData.user);
                }
            }
        },
        {
            targets: 7,
            className: 'align-middle text-nowrap text-center',
            createdCell: function (cell, cellData, rowData, rowIndex, colIndex) {
                var cell_content = `<a href="${rowData.order_info}" class="btn btn-color8 text-white btn-sm">View</a>`;
                $(cell).html(cell_content);
            }
        }],
        dom: "lBfrtip",
        buttons: [
            { // Copy button
                extend: "copy",
                text: "<i class='fas fa-clone'></i>",
                className: "btn btn-color8 text-white",
                titleAttr: "Copy",
                title: "Orders - BilnaCakes",
                exportOptions: {
                    columns: [0, 1, 2, 3, 4, 5, 6]
                }
            },
            { // PDF button
                extend: "pdf",
                text: "<i class='fas fa-file-pdf'></i>",
                className: "btn btn-color8 text-white",
                titleAttr: "Export to PDF",
                title: "Orders - BilnaCakes",
                filename: 'orders-bilnacakes',
                orientation: 'landscape',
                pageSize: 'A4',
                footer: true,
                exportOptions: {
                    columns: [0, 1, 2, 3, 4, 5, 6],
                    search: 'applied',
                    order: 'applied'
                },
                tableHeader: {
                    alignment: "center"
                },
                customize: function(doc) {
                    doc.styles.tableHeader.alignment = "center";
                    doc.styles.tableBodyOdd.alignment = "center";
                    doc.styles.tableBodyEven.alignment = "center";
                    doc.styles.tableHeader.fontSize = 7;
                    doc.defaultStyle.fontSize = 6;
                    doc.content[1].table.widths = Array(doc.content[1].table.body[1].length + 1).join('*').split('');

                    var body = doc.content[1].table.body;
                    for (i = 1; i < body.length; i++) {
                        doc.content[1].table.body[i][0].margin = [3, 0, 0, 0];
                        doc.content[1].table.body[i][0].alignment = 'center';
                        doc.content[1].table.body[i][1].alignment = 'center';
                        doc.content[1].table.body[i][2].alignment = 'left';
                        doc.content[1].table.body[i][3].alignment = 'center';
                        doc.content[1].table.body[i][4].alignment = 'right';
                        doc.content[1].table.body[i][5].alignment = 'center';
                        doc.content[1].table.body[i][6].alignment = 'left';
                        doc.content[1].table.body[i][6].margin = [0, 0, 3, 0];

                        for (let j = 0; j < body[i].length; j++) {
                            body[i][j].style = "vertical-align: middle;";
                        }
                    }
                }
            },
            { // Export to excel button
                extend: "excel",
                text: "<i class='fas fa-file-excel'></i>",
                className: "btn btn-color8 text-white",
                titleAttr: "Export to Excel",
                title: "Orders - BilnaCakes",
                exportOptions: {
                    columns: [0, 1, 2, 3, 4, 5, 6]
                }
            },
            { // Print button
                extend: "print",
                text: "<i class='fas fa-print'></i>",
                className: "btn btn-color8 text-white",
                title: "Orders - BilnaCakes",
                orientation: 'landscape',
                pageSize: 'A4',
                titleAttr: "Print",
                footer: true,
                exportOptions: {
                    columns: [0, 1, 2, 3, 4, 5, 6],
                    search: 'applied',
                    order: 'applied'
                },
                tableHeader: {
                    alignment: "center"
                },
                customize: function (win) {
                    $(win.document.body).css("font-size","11pt");
                    $(win.document.body).find("table").addClass("compact").css("font-size","inherit");
                }
            }
        ],
        footerCallback: function (row, data, start, end, display) {
            var api = this.api(), data;
            var intVal = function ( i ) {
                return typeof i === 'string' ?
                    i.replace(/[\s,]/g, '')
                     .replace(/TZS/g, '')
                     * 1 :
                    typeof i === 'number' ?
                        i : 0;
            };
            var priceTotal = api
                .column(4)
                .data()
                .reduce(function (a, b) {
                    return intVal(a) + intVal(b);
                }, 0);

            $(api.column(4).footer()).html(formatCurrency(priceTotal));
        },
        initComplete: function() {
            var api = this.api();
            api.columns([0, 1, 2, 3, 4, 5, 6, 7]).eq(0).each(function (colIdx) {
                var cell = $(".filters th").eq($(api.column(colIdx).header()).index());
                if (colIdx == 1) {
                    var calendar =`<button type="button" class="btn btn-sm btn-color8 text-white" data-bs-toggle="modal" data-bs-target="#date_filter_modal"><i class="fas fa-calendar-alt"></i></button>`;
                    cell.html(calendar);
                    $("#date_clear").on("click", function() {
                        $("#min_date").val("");
                        $("#max_date").val("");
                    });
                    $("#date_filter_btn").on("click", function() {
                        orders_table.draw();
                    });
                } else if (colIdx == 5) {
                    var calendar =`<button type="button" class="btn btn-sm btn-color8 text-white" data-bs-toggle="modal" data-bs-target="#duedate_filter_modal"><i class="fas fa-calendar-alt"></i></button>`;
                    cell.html(calendar);
                    $("#due_date_clear").on("click", function() {
                        $("#due_min_date").val("");
                        $("#due_max_date").val("");
                    });
                    $("#due_date_filter_btn").on("click", function() {
                        orders_table.draw();
                    });
                } else if (colIdx == 0 || colIdx == 7) {
                    cell.html("");
                } else {
                    $(cell).html("<input type='text' class='text-color5' placeholder='Filter..'/>");
                    $("input", $(".filters th").eq($(api.column(colIdx).header()).index()))
                    .off("keyup change").on("keyup change", function(e) {
                        e.stopPropagation();
                        $(this).attr('title', $(this).val());
                        var regexr = "{search}";
                        var cursorPosition = this.selectionStart;
                        api.column(colIdx).search(
                            this.value != '' ? regexr.replace('{search}', this.value) : '',
                            this.value != '',
                            this.value == ''
                            ).draw();
                        $(this).focus()[0].setSelectionRange(cursorPosition, cursorPosition);
                    });
                }
            });
        }
    });

    $("#orders_search").keyup(function() {
        orders_table.search($(this).val()).draw();
    });

    $("#orders_filter_clear").click(function (e) { 
        e.preventDefault();
        $("#orders_search").val('');
        clear_dates();
        orders_table.search('').draw();
    });

    var btn_deleting = false;
    $("#confirm_delete_btn").click(function (e) { 
        e.preventDefault();
        if(btn_deleting == false) {
            var formData = new FormData();
            formData.append("delete_order", $("#get_order_id").val());

            $.ajax({
                type: 'POST',
                url: $("#new_order_form").attr('action'),
                data: formData,
                dataType: 'json',
                contentType: false,
                processData: false,
                headers: {
                    'X-CSRFToken': CSRF_TOKEN
                },
                beforeSend: function() {
                    btn_deleting = true;
                    $("#cancel_delete_btn").removeClass('d-inline-block').addClass('d-none');
                    $("#confirm_delete_btn").html("<i class='fas fa-spinner fa-pulse'></i>");
                },
                success: function(response) {
                    btn_deleting = false;
                    if(response.success) {
                        window.alert('Order deleted successfully!');
                        window.location.href = response.url;
                    } else {
                        $("#cancel_delete_btn").removeClass('d-none').addClass('d-inline-block');
                        $("#confirm_delete_btn").html("<i class='fas fa-check-circle'></i> Yes");

                        var fdback = `<div class="alert alert-danger alert-dismissible fade show px-2 m-0 d-block w-100"><i class='fas fa-exclamation-circle'></i> ${response.sms} <button type="button" class="btn-close d-inline-block" data-bs-dismiss="alert"></button></div>`;

                        $("#confirm_delete_modal .formsms").html(fdback);
                    }
                },
                error: function(xhr, status, error) {
                    window.alert('Unknown error, reload and try again.');
                }
            });
        }
    });

    var btn_completing = false;
    $("#confirm_complete_btn").click(function (e) { 
        e.preventDefault();
        if(btn_completing == false) {
            var formData = new FormData();
            formData.append("complete_order", $("#get_order_id").val());

            $.ajax({
                type: 'POST',
                url: $("#new_order_form").attr('action'),
                data: formData,
                dataType: 'json',
                contentType: false,
                processData: false,
                headers: {
                    'X-CSRFToken': CSRF_TOKEN
                },
                beforeSend: function() {
                    btn_completing = true;
                    $("#cancel_complete_btn").removeClass('d-inline-block').addClass('d-none');
                    $("#confirm_complete_btn").html("<i class='fas fa-spinner fa-pulse'></i>");
                },
                success: function(response) {
                    btn_completing = false;
                    $("#complete_order_modal .formsms").html(generate_errorsms(response.success, response.sms));
                    if(response.success) {
                        $("#order_info_div").load(location.href + " #order_info_div");
                        $("#confirm_complete_btn").removeClass('d-inline-block').addClass('d-none');
                    } else {
                        $("#cancel_complete_btn").removeClass('d-none').addClass('d-inline-block');
                        $("#confirm_complete_btn").html("<i class='fas fa-check-circle'></i> Yes");
                    }
                },
                error: function(xhr, status, error) {
                    window.alert('Unknown error, reload and try again.');
                }
            });
        }
    });
});