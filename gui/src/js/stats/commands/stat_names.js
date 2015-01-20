'use strict';

var request = require('superagent');
var _ = require('lodash');

var BaseCommand = require('./base.js');
var AuthHeadersCommand = require('./auth_headers.js');
var ShardsCommand = require('./shards.js');
var APIUtils = require('../utils/APIUtils.js');
var apiUrls = require('../configs/apiUrls.json');

//
//
//

var STAT_NAMES_ROUTE = "{0}/v2/instance/{1}/host/{2}/stats/available";
var _statNames = null;

//
// Auth Headers Command
// Get the auth headers from the command
//

function StatNamesCommand(options) {
    this.options = options;
    this.locked = true;
    this.prereq = {
        "auth_headers": new AuthHeadersCommand(),
        "shards": new ShardsCommand()
    };
};

StatNamesCommand.prototype = _.extend({}, BaseCommand.prototype, {
     run: function(err, data, callback) {
         // cache the response here
         if (_statNames !== null) {
             callback(err, _statNames);
             return
         }

         var shardArray = _.pairs(data['shards'][0]);
         var hostname = shardArray[0][1][0];

         var url = APIUtils.formatURL(
             STAT_NAMES_ROUTE,
             apiUrls['apiv2'],
             APIUtils.instanceName,
             hostname
         );

         request.get(url)
             .set(data['auth_headers'])
             .end(function (err, response) {
                 _statNames = response.body.names;
                 callback(err, _statNames);
         });
     }
});

StatNamesCommand.prototype.constructor = StatNamesCommand;
module.exports = StatNamesCommand;
