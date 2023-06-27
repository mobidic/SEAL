$(document).ready(function() {
    table = $('#genes').DataTable({
        "language": {
            "loadingRecords": '<div class="animation-bar-1"><span style="width:100%"></span></div>',
        },
        scrollX: true,
        "proccessing": true,  "serverSide": true,
        scrollY:        "40vh",
        scrollX:        true,
        scrollCollapse: true,
        scroller:         true,
        fixedHeader:  true,
        ajax: {
            url: '/json/transcripts',
            type: 'POST',
            headers: {
                'X-CSRF-TOKEN': csrf_token
            },
        },
        colReorder: true,
        fixedColumns: {
            left:1,
            right:1
        },
        "columns": [
            { 'className': 'showTitle control-size-200', 'data': 'feature'},
            { 'className': 'showTitle control-size-300', 'data': 'biotype'},
            { 'className': 'showTitle control-size-200', 'data': 'feature_type'},
            { 'className': 'showTitle control-size-150', 'data': 'symbol'},
            { 'className': 'showTitle control-size-150', 'data': 'symbol_source'},
            { 'className': 'showTitle control-size-100', 'data': 'gene'},
            { 'className': 'showTitle control-size-100', 'data': 'source'},
            { 'className': 'showTitle control-size-200', 'data': 'protein'},
            { 'className': 'showTitle control-size-100', 'data': 'canonical'},
            { 'className': 'showTitle control-size-100', 'data': 'hgnc'},
            {
                "className": 'showTitle size-25 w3-center',
                "orderable":      false,
                "data": {
                    "_": "val",
                    "display" : function ( data, type, row, meta ) {
                        if (data) {
                            const transcript=data["feature"];
                            if (data["val"]) {
                                return '<input id="'+ transcript +'" class="w3-check" type="checkbox" checked="checked" onclick="add_transcript(\''+ transcript +'\');">';
                            } else {
                                return '<input id="'+ transcript +'" class="w3-check" type="checkbox" onclick="add_transcript(\''+ transcript +'\');">';
                            }
                        }
                        return "NA"
                    }
                }
            }
        ],
        "columnDefs": [
            {
                "render": {
                    "display": function ( data, type, row ) {
                        if (data) {
                            response = '<i title="CANONICAL" class="w3-text-flat-peter-river fas fa-star"></i>';
                        } else {
                            response = '<i title="" class="w3-text-flat-peter-river far fa-star"></i>';
                        }
                        return response;
                    },
                    "sort": function ( data, type, row ) {
                        return data;
                    },
                },
                "targets": 8
            }
        ],
    });
});

function add_transcript(transcript) {
    $.ajax({
        type: "POST",
        url: "/add/preferred",
        data: {
            "transcript": transcript
        }
    })
}