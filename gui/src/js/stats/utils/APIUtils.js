var request = require('superagent');
var async = require('async');
var request = require('superagent');
var _ = require('lodash');
var API_URLS_ROUTE = '/api_urls';
var TOKEN_ROUTE = '/api_token';
var _apiUrls = null;
var _authHeader = null;
//var _instanceName = window.location.pathname.split( '/' )[2];
var _instanceName = "appboy01_prod";
var _shards = null;
var _statnames = null;

module.exports = {
  formatURL: function(string) {

      var output = string;

      for (var i = 1; i < arguments.length; i++) {
        var regEx = new RegExp(
          "\\{" + (
          i - 1) + "\\}", "gm");
        output = output.replace(regEx, arguments[i]);
      }

      return output;
  },

  instanceName: _instanceName,

  getApiUrls: function(cb) {
    if (_apiUrls !== null) {
      cb(null, _apiUrls);
      return;
    };

    request
      .get(API_URLS_ROUTE)
      .end(
      function (err, res) {
        //_apiUrls = res
        _apiUrls = {"apiv2": "https://sjc-api.objectrocket.com"};
        cb(err, _apiUrls);
      });
  },

  getAuthHeader: function(cb) {
    if (_authHeader !== null) {
      cb(null, _authHeader);
      return;
    };

    request
      .get(TOKEN_ROUTE)
      .end(function(err, res) {
        //_authHeader = {
        //  "X-Auth-Account": res['user'],
        //  "X-Auth-Token": res['api_token']
        //};
        _authHeader = {
          "X-Auth-Account": "appboy",
          "X-Auth-Token": "ImFjMGQ1YjY3YjBkYjQ0MjQ4ZDU3MGE3NjEzZmRhZjk5Ig.B5dKvg.glbz5hJpIaMFQVj4TIbj1TbSGsM"
        }
        cb(err, _authHeader);
      });
  },

  getShards: function(apiUrl, authHeader, cb) {
    if (_shards !== null) {
      cb(null, _shards);
      return;
    };

    return request
      .get(
      this.formatURL(
        "{0}/v2/instance/{1}/replicaset",
        apiUrl.apiv2,
        _instanceName
      ))
      .set(authHeader)
      .end(function(err, res) {
         _shards = res.body;
         cb(err, _shards);
       });
  },

  getStatNames: function(apiUrl, authHeader, shards, cb) {

    if (_statnames !== null) {
      cb(null, _statnames);
      return;
    };

    var resultArray = _.pairs(shards.data[0]);

    return request
      .get(
      this.formatURL(
        "{0}/v2/instance/{1}/host/{2}/stats/available",
        apiUrl.apiv2,
        _instanceName,
        resultArray[0][1][0]
      ))
      .set(authHeader)
      .end(function(err, res) {
            _statnames = res.body;
             cb(err, _statnames);
           });
  },

  /**
   * {"stats": [{
   * "instance": "...",
   * "host": "...",
   * "name": "..."
   *   }]}
   * @param startDate
   * @param endDate
   * @param granularity
   * @param cb
   * @returns {Request}
   */
  getGraph: function(
    apiUrl,
    authHeader,
    startDate,
    endDate,
    granularity,

    cb) {

    if (_statnames !== null) {
      cb(null, _statnames);
      return;
    };

    return request
      .post(
      this.formatURL(
        "{0}/v2/graph/ad_hoc?granularity={1}&start_time={2}&end_time={3}",
        apiUrl.apiv2,
        granularity,
        startDate,
        endDate
      ))
      .send({ name: 'Manny', species: 'cat' })
      .set(authHeader)
      .end(function(err, res) {
             _statnames = res.body;
             cb(err, _statnames);
           });
  }

};
