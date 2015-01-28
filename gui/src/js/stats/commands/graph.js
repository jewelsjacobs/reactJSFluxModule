var request = require('superagent');
var _ = require('lodash');

var BaseCommand = require('../../common/commands/base.js');
var AuthHeadersCommand = require('../../common/commands/auth_headers.js');
var APIUtils = require('../../common/utils/APIUtils.js');
var apiUrls = require('../../common/configs/LoadConfig.js').api;
var moment = require('moment');

var GRAPH_ROUTE = "{0}/v2/graph/ad_hoc?granularity={1}&start_time={2}&end_time={3}";

/**
 * @description Picks the granularity to be reasonable
 * based on the timespan chosen
 * @param {moment} fromDate
 * @param {moment} toDate
 * @returns {*}
 * @private
 */
function _granularity(fromDate, toDate){
  var secondsDiff = toDate.diff(fromDate, 'seconds');
  var granularity = null;

  if (secondsDiff <= 360) { // 6 hours
    granularity = 'minute';
  } else if (secondsDiff <= 259200) {  // 72 hours
    granularity = 'hour';
  } else {
    granularity = 'day';
  }

  return granularity;
};

/**
 * Interface for the Graph API
 *
 * @module commands/graphcommand
 * @param {Object} options
 * @constructor
 */

function GraphCommand(options) {
    this.options = options;
    this.prereq = {
        "auth_headers": new AuthHeadersCommand()
    };
};

GraphCommand.prototype = _.extend({}, BaseCommand.prototype, {

     run: function(err, data, callback) {
         var startTime = moment(this.options.startDate).utc().format("YYYY-MM-DD HH:mm:ss");
         var endTime = moment(this.options.endDate).utc().format("YYYY-MM-DD HH:mm:ss");
         var stats = [];

         _.forEach(this.options.hosts, function(host){

           stats.push({
              "instance": APIUtils.instanceName,
              "host": host,
              "name": this.options.statName
            });
         }.bind(this));

         var url = APIUtils.formatURL(
             GRAPH_ROUTE,
             apiUrls['apiv2'],
             _granularity(this.options.startDate, this.options.endDate),
             startTime,
             endTime
         );

         request.post(url)
             .set(data['auth_headers'])
             .send({ stats: stats })
             .end(function (err, response) {
                 callback(err, response.body);
         });
     }
});

GraphCommand.prototype.constructor = GraphCommand;
module.exports = GraphCommand;
