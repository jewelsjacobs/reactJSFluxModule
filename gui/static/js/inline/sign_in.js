$(document).ready(function() {
  // Validation for password reset form.
  $('#login-form').validate({
    rules: {
      login: {
        required: true,
      },
      password: {
        required: true,
      },
    },
    errorClass: 'rs-validation-block',
    errorElement: 'span',
    highlight: function(label) {
      $(label).closest('.rs-control-group').removeClass('success');
      $(label).closest('.rs-control-group').addClass('error');
    },
    success: function(label) {
      $(label).closest('.rs-control-group').removeClass('error');
      $(label).closest('.rs-control-group').addClass('success');
    }
  });

  // Validation for password reset popover.
  $('#password-reset-popover-form').validate({
    rules: {
      login: {
        required: true,
      },
    },
    errorClass: 'rs-validation-block',
    errorElement: 'span',
    highlight: function(label) {
      $(label).closest('.rs-control-group').removeClass('success');
      $(label).closest('.rs-control-group').addClass('error');
    },
    success: function(label) {
      $(label).closest('.rs-control-group').removeClass('error');
      $(label).closest('.rs-control-group').addClass('success');
    }
  });

});
