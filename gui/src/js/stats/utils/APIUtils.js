var request = require('superagent');
var async = require('async');
var _ = require('lodash');
var API_URLS_ROUTE = '/api_urls';
var TOKEN_ROUTE = '/api_token';
var _apiUrls = null;
var _authHeader = null;
//var _instanceName = window.location.pathname.split( '/' )[2];
var _instanceName = "appboy01_prod";
var _shards = null;
var _statNames = null;

function granularity(toDate, fromDate){
  var secondsDiff = toDate.diff(fromDate, 'seconds');
  var granularity = null;

  // pick the granularity to be reasonable based on the timespan chosen.
  if (secondsDiff <= 360) { // 6 hours
    granularity = 'minute';
  } else if (secondsDiff <= 259200) {  // 72 hours
    granularity = 'hour';
  } else {
    granularity = 'day';
  }

  return granularity;
}

var ApiUtils = {
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

  getStatNames: function(shards, cb) {
    if (_statNames !== null) {
      cb(null, _statNames);
      return;
    };

    var resultArray = _.pairs(shards[0]);

    return request
      .get(
      this.formatURL(
        "{0}/v2/instance/{1}/host/{2}/stats/available",
        _apiUrls.apiv2,
        _instanceName,
        resultArray[0][1][0]
      ))
      .set(_authHeader)
      .end(function(err, res) {
        _statNames = res.body;
        cb(err, _statNames);
      });
  },

  /**
   *
   * API call to get Graph data
   *
   * @param statName
   * @param hosts
   * @param startDate
   * @param endDate
   * @param cb
   * @returns {Request}
   */
  getGraph: function(statName, hosts, startDate, endDate, cb) {
    var startTime = moment(startDate).utc().format("YYYY-MM-DD HH:mm:ss");
    var endTime = moment(endDate).utc().format("YYYY-MM-DD HH:mm:ss");
    var stats = [];

    _.forEach(hosts, function(host){
      stats.push({
         "instance": _instanceName,
         "host": host,
         "name": statName
       });
    });

    return request
      .post(
      this.formatURL(
        "{0}/v2/graph/ad_hoc?granularity={1}&start_time={2}&end_time={3}",
        _apiUrls.apiv2,
        granularity(startDate, endDate),
        startTime,
        endTime
      ))
      .send({ stats: stats })
      .set(_authHeader)
      .end(function(err, res) {
         cb(err, res.body);
       });
  }

};

module.exports = ApiUtils;
