$(document).ready(function(){
    var families=[];
    $.getJSON('/json/families', function(data, status, xhr){
        for (var i = 0; i < data['data'].length; i++ ) {
            families.push(data["data"][i]["family"]);
        }
    });

    $('#family').autocomplete({
        source: families,
    });

    var runs=[];
    $.getJSON('/json/runs', function(data, status, xhr){
        for (var i = 0; i < data['data'].length; i++ ) {
            runs.push(data["data"][i]["name"]);
        }
    });

    $('#run').autocomplete({
        source: runs,
    });
});

$('#multiSelectTeams').multiSelect({
    selectableHeader: "<div class='w3-container w3-teal'>Selectable Teams</div>",
    selectionHeader: "<div class='w3-container w3-teal'>Selected Teams</div>",
});