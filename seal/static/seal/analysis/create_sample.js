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

    var filters=[];
    $.getJSON('/json/filters', function(data, status, xhr){
        for (let key in data) {
            filters.push(data[key]);
        }
    });

    var beds=[];
    $.getJSON('/json/beds', function(data, status, xhr){
        for (let key in data) {
            beds.push(data[key]);
        }
    });

    $('#run').autocomplete({
        source: runs,
    });

    $('#filter').autocomplete({
        source: filters,
    });

    $('#bed').autocomplete({
        source: beds,
    });
    $('.js-example-basic-multiple').select2();
});
