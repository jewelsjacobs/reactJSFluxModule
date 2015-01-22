'use strict';

var request = require('superagent');
var _ = require('lodash');

var BaseCommand = require('./base.js');
var AuthHeadersCommand = require('./auth_headers.js');
var APIUtils = require('../utils/APIUtils.js');
var apiUrls = require('../configs/apiUrls.json');

var STATS_ROUTE = "{0}/v2/instance/{1}/stats_config";
var _stats = null;

/**
 * Command to get shards and statsNames
 * from instance API
 *
 * @param options
 * @constructor
 */

function StatsCommand(options) {
    this.options = options;
    this.locked = true;
    this.prereq = {
        "auth_headers": new AuthHeadersCommand()
    };
};

StatsCommand.prototype = _.extend({}, BaseCommand.prototype, {

  /**
   * API method
   * @param err
   * @param data
   * @param callback
   */
     run: function(err, data, callback) {
         // cache the response here
         if (_stats !== null) {
             callback(err, _stats);
             return
         }

         var url = APIUtils.formatURL(
           STATS_ROUTE,
           apiUrls['apiv2'],
           APIUtils.instanceName
         );

         request.get(url)
             .set(data['auth_headers'])
             .end(function (err, response) {
                 _stats = response.body;
                 callback(err, _stats);
         });
     }
});

StatsCommand.prototype.constructor = StatsCommand;
module.exports = StatsCommand;
