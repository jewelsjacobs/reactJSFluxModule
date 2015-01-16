'use strict';

var request = require('superagent');
var _ = require('lodash');

var BaseCommand = require('./base.js');
var APIUrlCommand = require('./api_url.js');
var AuthHeadersCommand = require('./auth_headers.js');
var APIUtils = require('../utils/APIUtils.js');

//
// 
//

var SHARDS_ROUTE = "{0}/v2/instance/{1}/replicaset";
var _shards = null;

//
// Auth Headers Command
// Get the auth headers from the command
//

function ShardsCommand(options) {
    this.options = options;
    this.locked = true;
    this.prereq = {
        "api_urls": new APIUrlCommand(),
        "auth_headers": new AuthHeadersCommand()
    };
};

ShardsCommand.prototype = _.extend({}, BaseCommand.prototype, {
     run: function(err, data, callback) {
         // cache the response here
         if (_shards !== null) {
             callback(err, _shards);
             return
         }
         
         var url = APIUtils.formatURL(
             SHARDS_ROUTE, 
             data['api_urls']['apiv2'],
             APIUtils.instanceName
         );
         
         request.get(url)
             .set(data['auth_headers'])
             .end(function (err, response) {
                 _shards = response.body.data;
                 callback(err, _shards);
         });
     }
});

ShardsCommand.prototype.constructor = ShardsCommand;
module.exports = ShardsCommand;
