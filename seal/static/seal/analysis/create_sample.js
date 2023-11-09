function autocomplete_patient(data, value) {
    $('#index-hidden').remove();
    $('#affected-hidden').remove();
    if(value in data) {
        $("#patient_alias").prop('readonly', true);
        $("#patient_alias").val(data[value]["alias"]);
        $("#family").prop('readonly', true);
        if (data[value]["family"]) {
            $("#family").val(data[value]["family"]);
        } else {
            $("#family").val("");
        }
        $("#index").prop('disabled', true);
        if (data[value]["index"]) {
            $("#index").prop('checked', true);
            $('<input>').attr({
                type: 'hidden',
                name: 'index',
                id: 'index-hidden',
                value: true
            }).appendTo('#form-new-sample');
        } else {
            $("#index").prop('checked',false);
            $('<input>').attr({
                type: 'hidden',
                name: 'index',
                id: 'index-hidden',
                value: false
            }).appendTo('#form-new-sample');
        }
        $("#affected").prop('disabled', true);
        if (data[value]["affected"]) {
            $("#affected").prop('checked', true);
            $('<input>').attr({
                type: 'hidden',
                name: 'affected',
                id: 'affected-hidden',
                value: true
            }).appendTo('#form-new-sample');
        } else {
            $("#affected").prop('checked',false);
            $('<input>').attr({
                type: 'hidden',
                name: 'affected',
                id: 'affected-hidden',
                value: false
            }).appendTo('#form-new-sample');
        }
    } else {
        $("#patient_alias").prop('readonly', false);
        $("#patient_alias").val("");
        $("#family").prop('readonly', false);
        $("#family").val("");
        $("#affected").prop('disabled', false);
        $("#affected").prop('checked',false);
        $("#index").prop('disabled', false);
        $("#index").prop('checked',false);
    }
}

$.getJSON('/json/patients', function(data){
    var t2 = {};
    for( elt in data["data"]){
        t2[data["data"][elt]["id"]] = data["data"][elt]
    }
    $('#patientID').autocomplete({
        source: Object.keys(t2),
        autoFocus: true,
        focus: function( event, ui ) {
            autocomplete_patient(t2, ui.item.value);
        },
        close: function( event, ui ) {
            console.log("y")
            autocomplete_patient(t2, $('#patientID').val());
        }
    });
});

///////////////////////////////////////////////////////////////////////////////

var families=[];
$.getJSON('/json/families', function(data, status, xhr){
    for (var i = 0; i < data['data'].length; i++ ) {
        families.push(data["data"][i]["family"]);
    }
});

$('#family').autocomplete({
    source: families,
    autoFocus: true,
});


///////////////////////////////////////////////////////////////////////////////

function autocomplete_run(data, value) {
    if(value in data) {
        $("#run_alias").prop('readonly', true);
        $("#run_alias").val(data[value]["alias"]);
    } else {
        $("#run_alias").prop('readonly', false);
        $("#run_alias").val("");
    }
}

$.getJSON('/json/runs', function(data){
    t = {};
    for( elt in data["data"]){
        t[data["data"][elt]["name"]] = data["data"][elt]
    }
    $('#run').autocomplete({
        source:Object.keys(t),
        autoFocus: true,
        change: function( event, ui ) {
            autocomplete_run(t, $('#run').val());
        },
        select: function( event, ui ) {
            autocomplete_run(t, ui.item.value);
        },
        focus: function( event, ui ) {
            autocomplete_run(t, ui.item.value);
        }
    });
});

///////////////////////////////////////////////////////////////////////////////

$('#teams').select2();