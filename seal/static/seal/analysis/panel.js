$(function(){
    $('.js-example-basic-multiple').select2();
});

$(document).ready(function() {
    $.getJSON("/json/beds", function(data) {
        var options = '<option value="0">No panel</option>';
        for (x in data) {
            option = '<option value="' + x + '" >'
            option += data[x];
            option += "</option>";
            options += option;
        }
        $('#selectBed').html(options);
    });

    table = $('#regions').DataTable({
        ajax: '/json/bed/0',
        "columns": [
            { 'className': 'showTitle control-size-200', 'data': 'chr'},
            { 'className': 'showTitle control-size-300', 'data': 'start'},
            { 'className': 'showTitle control-size-200', 'data': 'stop'},
            { 'className': 'showTitle control-size-150', 'data': 'name'},
        ],
        dom: 'lBfrtip',
        buttons: [
            'copy', 'csv'
        ]
    });
});

function view_panel(id) {
    $("#regions").css('opacity', '0.6');
    table = $('#regions').DataTable();
    table.ajax.url( '/json/bed/' + id ).load(function(){$("#regions").css('opacity', '1');});
}