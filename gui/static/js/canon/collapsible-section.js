var collapseAll = function() {
    $(".rs-collapsible-section .rs-detail-section-header").each(function() {
        var parent = $(this).parent();
        parent.removeClass("expanded");
        parent.addClass("collapsed");
    });
}

var expandAll = function() {
    $(".rs-collapsible-section .rs-detail-section-header").each(function() {
        var parent = $(this).parent();
        parent.removeClass("collapsed");
        parent.addClass("expanded");
    });
}

$(document).ready(function() {

    $(".rs-collapsible-section .rs-detail-section-header").click(function() {
        $(this).parent().toggleClass("collapsed expanded");
    });

    $(".or-collapse-all").click(function() {
        collapseAll();
        hideDropdown();
        hideOverlay();
    });

    $(".or-expand-all").click(function() {
        expandAll();
        hideDropdown();
        hideOverlay();
    });

});
