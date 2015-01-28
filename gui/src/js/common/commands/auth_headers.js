var request = require('superagent');
var _ = require('lodash');

var BaseCommand = require('./base.js');

var TOKEN_ROUTE = '/api_token';
var _authHeaders = null;

/**
 * Interface for the Auth Headers API
 *
 * @module commands/AuthHeadersCommand
 * @param {Object} options
 * @constructor
 */

function AuthHeadersCommand(options) {
    this.options = options;
    this.prereq = {};
    this.locked = true;
};

AuthHeadersCommand.prototype = _.extend({}, BaseCommand.prototype, {
     run: function(err, data, callback) {

         if (_authHeaders !== null) {
             callback(err, _authHeaders);
             return
         }

        request.get(TOKEN_ROUTE)
            .end(function (err, response) {
                _authHeaders = {
                  "X-Auth-Account": response.body['user'],
                  "X-Auth-Token": response.body['api_token']
                };

                callback(err, _authHeaders);
        });
     }
});

AuthHeadersCommand.prototype.constructor = AuthHeadersCommand;
module.exports = AuthHeadersCommand;
