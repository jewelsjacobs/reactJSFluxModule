var request = require('superagent');
var prefix = require('superagent-prefix')('/static/json');
prefix(request);

module.exports = {

  getMockJSON: function(mockJsonFileName) {
    request
      .get(mockJsonFileName)
      .end(function(res){
         return res.data;
     });
  },

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
