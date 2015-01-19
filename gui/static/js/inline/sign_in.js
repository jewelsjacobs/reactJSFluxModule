$(document).ready(function() {

  // Validation options.
  function options(formType) {

    var rules = {
      login: {
        required: true
      }
    };

    if (formType === "logInForm") {
      rules.password = { required: true };
    }

    return {
      rules: rules,
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
    };
  }

  // Validation for password reset form.
  $('#login-form').validate(options("logInForm"));

  // Validation for password reset popover.
  $('#password-reset-popover-form').validate(options("passwordResetPopoverForm"));
});
