/**
 * Some JS for the migration pages.
 * TODO(TheDodd): Once we get React/Flux framework in place, move this code into the components
 * themselves.
 */
$(document).ready(function() {
    var goBackForm = $('#go-back-form');
    var nextStep = $('#sso-migration-link-account-form-submit');

    // Listener to display terms of service overlay.
    $('a[href=#tos]').click(function(event) {
        $('#tos').fadeIn();
        event.preventDefault();
    });

    // Listener to close terms of service overlay.
    $('a[href=#close-tos]').click(function(event) {
        $('#tos').fadeOut();
        event.preventDefault();
    });

    // Listener for TOS confirmation.
    $('#migration-terms-and-conditions').change(function() {
        if (this.checked) {
            nextStep.removeClass('disabled');
            nextStep.removeProp('disabled');
        } else {
            nextStep.addClass('disabled');
            nextStep.prop('disabled', true);
        }
    });

    // Listener for go back requests.
    $('#go-back-button').click(function() {
        goBackForm.submit();
    });
});
