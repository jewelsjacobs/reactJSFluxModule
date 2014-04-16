var overlay;

var hideOverlay = function(){
	overlay.removeClass('visible').addClass('hidden');
}

var showOverlay = function() {
	overlay.removeClass('hidden').addClass('visible');
}

$(document).ready(function() {
	$('body').append('<div class="or-overlay hidden"></div>');
	overlay = $('.or-overlay');
	overlay.click(function() {
		hidePopover();
		hideDropdown();
		hideOverlay();
	});
});
