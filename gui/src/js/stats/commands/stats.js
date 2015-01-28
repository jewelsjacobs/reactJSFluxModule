var request = require('superagent');
var _ = require('lodash');

var BaseCommand = require('../../common/commands/base.js');
var AuthHeadersCommand = require('../../common/commands/auth_headers.js');
var APIUtils = require('../../common/utils/APIUtils.js');
var apiUrls = require('../../common/configs/LoadConfig.js').api;

var STATS_ROUTE = "{0}/v2/instance/{1}/stats_config";
var _stats = null;

/**
 * Interface for the Stats API
 *
 * @module commands/statscommand
 * @param {Object} options
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
