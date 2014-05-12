var collapseAll = function() {
    $(".rs-collapsible-section .rs-detail-section-header").each(function() {
        var parent = $(this).parent();
        if (!parent.hasClass('collapsed')) {
            parent.click();
            parent.removeClass('expanded');
            parent.addClass('collapsed');
        }
    });
}

var expandAll = function() {
    $(".rs-collapsible-section .rs-detail-section-header").each(function() {
        var parent = $(this).parent();
        if (!parent.hasClass('expanded')) {
            parent.click();
            parent.removeClass('collapsed');
            parent.addClass('expanded');
        }
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
