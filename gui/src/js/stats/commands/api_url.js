'use strict';

var request = require('superagent');
var _ = require('lodash');

var BaseCommand = require('./base.js');

//
// 
//

var API_URLS_ROUTE = "/api_urls"
var _apiUrls = null;

//
// API URL Command
// Get the API URLs from the request
//

function APIUrlCommand(options) {
    this.options = options;
    this.prereq = {};
};

APIUrlCommand.prototype = _.extend({}, BaseCommand.prototype, {
    run: function(err, data, callback) {        
        // cache the response here
        if (_apiUrls !== null) {
            callback(err, _apiUrls);
            return
        }

        // make the request for the api urls
        request.get(API_URLS_ROUTE)
            .end(function (err, response) {
                // _apiUrls = response.data
                _apiUrls = {"apiv2": "https://sjc-api.objectrocket.com"};
                callback(err, _apiUrls);
            });
    }
});

APIUrlCommand.prototype.constructor = APIUrlCommand;
module.exports = APIUrlCommand;
