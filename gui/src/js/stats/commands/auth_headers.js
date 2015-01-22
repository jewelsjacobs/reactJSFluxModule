'use strict';

var request = require('superagent');
var _ = require('lodash');

var BaseCommand = require('./base.js');

//
//
//

var TOKEN_ROUTE = '/api_token';
var _authHeaders = null;

//
// Auth Headers Command
// Get the auth headers from the command
//

function AuthHeadersCommand(options) {
    this.options = options;
    this.prereq = {};
    this.locked = true;
};

AuthHeadersCommand.prototype = _.extend({}, BaseCommand.prototype, {
     run: function(err, data, callback) {
         // cache the response here
         if (_authHeaders !== null) {
             callback(err, _authHeaders);
             return
         }

        // make the request for the api urls
        request.get(TOKEN_ROUTE)
            .end(function (err, response) {
                //_authHeaders = {
                //  "X-Auth-Account": response['user'],
                //  "X-Auth-Token": response['api_token']
                //};
                _authHeaders = {
                    "X-Auth-Account": "appboy",
                    "X-Auth-Token": "ImY2ZjBiZGFlNjBjZDRjODU4YzliMGYzMWE1MDRjNjMwIg.B6LRfw.4q5QIsbVGWBH0DvdYuvxJCAxaDw"
                }

                callback(err, _authHeaders);
        });
     }
});

AuthHeadersCommand.prototype.constructor = AuthHeadersCommand;
module.exports = AuthHeadersCommand;
