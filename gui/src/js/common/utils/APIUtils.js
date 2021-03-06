/**
 * API utility methods
 *
 * @module utils/apiutils
 * @type {{formatURL: Function, instanceName: *}}
 */

var ApiUtils = {
  formatURL: function (string) {

    var output = string;

    for (var i = 1; i < arguments.length; i++) {
      var regEx = new RegExp(
        "\\{" + (
        i - 1) + "\\}", "gm");
      output = output.replace(regEx, arguments[i]);
    }

    return output;
  },

  instanceName: window.location.pathname.split('/')[2]

};

module.exports = ApiUtils;
