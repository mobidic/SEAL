function view_sample(id) {
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrf_token);
            }
        }
    });

    $.ajax({
        type: "POST",
        url: "/toggle/sample/status",
        data: {
            "sample_id": id
        },
        success: function() {
            document.location.href = "/sample/" + id;
        }
    });
}

function toggle_status(id, status) {
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrf_token);
            }
        }
    });

    $.ajax({
        type: "POST",
        url: "/toggle/sample/status",
        data: {
            "sample_id": id,
            "status": status
        },
        success: function() {
            if (status == 1) {
                response = '<span class="w3-text-flat-peter-river"><i class="fas fa-user-clock"></i> <i><b>New Sample</b></i> <i class="fas fa-sort-down"></i></span>';
            } else if (status == 2) {
                response = '<span class="w3-text-flat-peter-river"><i class="fas fa-user-edit"></i> <i><b>Processing</b></i> <i class="fas fa-sort-down"></i></span>';
            } else if (status == 3) {
                response = '<span class="w3-text-flat-emerald"><i class="fas fa-user-check"></i> <i><b>Interpreted</b></i> <i class="fas fa-sort-down"></i></span>';
            } else if (status == 4) {
                response = '<span class="w3-text-flat-pumpkin"><i class="fas fa-user-lock"></i> <i><b>Validated</b></i> <i class="fas fa-sort-down"></i></span>';
            }
            document.getElementById("button-status-" + id).innerHTML = response;
        }
    });
}

$(document).ready(function() {
    table = $('#samples').DataTable({
        scrollX: true,
        proccessing: true,
        serverSide: true,
        ajax: {
            url: '/json/samples',
            type: 'POST',
            headers: {
                'X-CSRF-TOKEN': csrf_token
            },
        },
        columns: [
            {
                className: 'showTitle',
                data: {
                    _: "samplename",
                    display: function ( data, type, row ) {
                        if(data) {
                            return '<button onclick="view_sample(' + data.id + ')" class="w3-button w3-hover-flat-green-sea">' + data.samplename + '</button>';
                        }
                        return data
                    }
                }
            },
            { className: 'showTitle', data: "family" },
            { className: 'showTitle', data: "run.name" },
            { className: 'showTitle', data: "run.alias" },
            {
                className: 'showTitle ',
                data: {
                    _: "status",
                    display: function ( data, type, row ) {
                        response = "";
                        if(data) {
                            test = {
                                "-1": {
                                    "class": "w3-text-flat-alizarin",
                                    "icon": '<i class="fas fa-times-circle"></i>',
                                    "text": '<i><b>Error</b> - contact admin</i>',
                                },
                                "0": {
                                    "class": "w3-text-flat-wet-asphalt",
                                    "icon": '<i class="fas fa-cloud-download-alt"></i>',
                                    "text": '<i><b>Upload</b> - in progress</i>',
                                },
                                "1": {
                                    "class": "w3-text-flat-peter-river",
                                    "icon": '<i class="fas fa-user-clock"></i>',
                                    "text": '<i><b>New Sample</b></i>',
                                },
                                "2": {
                                    "class": "w3-text-flat-peter-river",
                                    "icon": '<i class="fas fa-user-edit"></i>',
                                    "text": '<i><b>Processing</b></i>',
                                },
                                "3": {
                                    "class": "w3-text-flat-emerald",
                                    "icon": '<i class="fas fa-user-check"></i>',
                                    "text": '<i><b>Interpreted</b></i>',
                                },
                                "4": {
                                    "class": "w3-text-flat-pumpkin",
                                    "icon": '<i class="fas fa-user-lock"></i>',
                                    "text": '<i><b>Validated</b></i>',
                                },
                            }
                            
                            response = '<span class="' + test[data.status]["class"] + '">' + test[data.status]["icon"] + " " + test[data.status]["text"] + ' <i class="fas fa-sort-down"></i></span>';
                            
                            valid = (data.status == 4 ? true : false);

                            sample_id = data.id;

                            disabled = "w3-disabled";
                            dropdown = "";
                            if (data.status != 4 || bio_or_admin) {
                                dropdown = '<div class="w3-dropdown-content w3-bar-block" style="position: fixed !important;right:0" id="button-status-' + sample_id + '-content">';
                                for (const idx of [1,2,3,4]) {
                                    var onclick = `onclick="toggle_status(` + sample_id + `, ` + idx +`)"`;
                                    var border = "w3-border-left w3-border-right";
                                    var disabled = "";
                                    if (idx == 4) {
                                        border = border + " w3-border-bottom";
                                        if (! bio_or_admin) {
                                            onclick = "";
                                            disabled = "w3-disabled"
                                        }
                                    }
                                    if (idx == 1) {
                                        border = border + " w3-border-top";
                                    }

                                    a = `
                                            <a `+onclick+` class="`+ border +` w3-bar-item w3-button">
                                                <span class="` + disabled + ` ` + test[idx]["class"] + `">` + test[idx]["icon"] + ` ` + test[idx]["text"] + `</span>
                                            </a>`;
                                    dropdown = dropdown + a;
                                }
                                dropdown = dropdown + '</div>';
                                disabled = "";
                            }
                            response = `
                                <div class="w3-dropdown-click w3-right" style="background-color:transparent">
                                    <button class="` + disabled + ` w3-left w3-button button-status" onclick="toggle_dd_status('button-status-` + sample_id + `')" id="button-status-` + sample_id + `">
                                        ` + response + `
                                    </button>`;
                            response = response + dropdown;
                            response = response + `
                                </div>`;
                        }
                        return response;
                    }
                }
            },
            {
                className: 'showTitle',
                orderable: false,
                data: "teams",
                render : {
                    _: function ( data, type, row ) {
                        if (data.length >= 1) {
                            teams = ""
                            for (i in data) {
                                teams += '<span class="w3-tag" style="max-width:100px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;background-color:' + data[i]["color"] + '">' + data[i]["teamname"] + '</span> ';
                            };
                            return teams
                        }
                        return "NA"
                    }
                }
            }
        ],
        createdRow: function( row, data, dataIndex ) {
            if ( data.status < 1 || data.status > 4) {
                $(row).addClass( 'w3-disabled' );
            }
        }
    });
});

$(document).on("click", function(event){
    if($(event.target).parents('.button-status').length || $(event.target).hasClass('button-status')) {
        return;
    }
    $('.StatusVisible').toggle();
    $('.StatusVisible').removeClass("StatusVisible");
});
function toggle_dd_status(id) {
    if (! $('#' + id + "-content").hasClass("StatusVisible")) {
        $('.StatusVisible').hide();
        $('.StatusVisible').removeClass("StatusVisible");
    }
    right = $(window).width() - $('#' + id).offset().left - $('#' + id).width();
    $('#' + id + "-content").css('margin-right', right);
    $('#' + id + "-content").toggle();
    $('#' + id + "-content").toggleClass("StatusVisible");
}