$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrf_token);
        }
    }
});

$(document).on("mouseenter", ".showTitle", function() {
    $(this).attr('title', this.innerText);
});
function updateSideBar(){
    if ($(window).width() <= 992) {
        if ($('#sidebar').is(":visible") != $('#overlay').is(":visible")) {
            $('#overlay').toggle();
        }
    } else {
        if ($('#sidebar').is(":visible")) {
            $('.w3-main').css("margin-left","350px");
        } else {
            $('.w3-main').css("margin-left","0px");
        }
        if ($('#overlay').is(":visible")) {
            $('#overlay').toggle();
        }
    }
};
// Script to open and close sidebar
async function w3_toggle_menu() {
    if ($(window).width() > 992) {
        $.ajax({
            type: "POST",
            url: "/toggle/user/sidebar"
        })
    };
    $('#sidebar').toggle();
    updateSideBar();
    await new Promise(r => setTimeout(r, 450));
    $('.w3-table-all').DataTable().columns.adjust();
}
$(window).resize(updateSideBar);
$(document).ready(function(){
    if ($(window).width() <= 992 && $('#sidebar').is(":visible")) {
        $('#sidebar').toggle();
    }
});