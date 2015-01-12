var request = require('superagent');

module.exports = {
  formatURL: function(string) {
    String.format = String.format || function (string) {
      var output = string;

      for (var i = 1; i < arguments.length; i++) {
        var regEx = new RegExp(
          "\\{" + (
          i - 1) + "\\}", "gm");
        output = output.replace(regEx, arguments[i]);
      }

      return output;
    }
  }

};
