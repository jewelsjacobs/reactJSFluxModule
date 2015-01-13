'use strict';

/**
 * BootstrapStore to get data needed for shards
 * @type {exports}
 */

var assign = require('object-assign');
var AppDispatcher = require('../dispatcher/AppDispatcher.js');
var Constants = require('../constants/Constants.js');
var ActionTypes = Constants.ActionTypes;
var BaseStore = require('./Store.js');
var AuthStore = require('./Auth.js');
var async = require('async');
var request = require('superagent');
var APIUtils = require('../utils/APIUtils.js');
var API_URLS_ROUTE = '/api_urls';
var _shards = [];
//var _instance = window.location.pathname.split( '/' )[2];
var _instance = "appboy01_prod";

/**
 * Gets Object with API URLs
 * @param cb
 * @returns {*}
 * @private
 */
function _getApiUrls(cb) {
  //return request
  //    .get(API_URLS_ROUTE)
  //    .end(function(err, res) {
  //       return cb(err, res);
  //     });
  //  };
  return cb(null,"https://sjc-api.objectrocket.com");
};

/**
 * Formats a url used in call to get replicaset data
 * @returns {*}
 * @private
 */
function _getReplicaSetUrl(apiUrl, cb) {
  var url = APIUtils.formatURL("{0}/v2/instance/{1}/replicaset", apiUrl, _instance);
  return cb(null, url);
};

/**
 * Getting Shards
 *
 * @param authHeaders
 * @param url
 * @param cb
 * @returns {Request}
 * @private
 */
function _getShardsAndReplicasets(authHeaders, url, cb) {
    return request
      .get(url)
      .set(authHeaders)
      .end(function(err, res) {
         cb(err, res);
       });
  };


var BootstrapStore = assign(new BaseStore(), {

  emitChange: function() {
    this.emit(this.CHANGE_EVENT);
  },

  getInstance: function() {
    return _instance;
  },

  getApiUrls: function(cb) {
    _getApiUrls(cb);
  },

  getShardsAndReplicasets: function() {
    async.waterfall([
      function(cb) {
        _getApiUrls(cb)
      },
      _getReplicaSetUrl,
      AuthStore.getAuthHeaders,
      _getShardsAndReplicasets
      ], function (err, result) {
        return result;
      });
  },

  CHANGE_EVENT: 'BOOTSTRAP_CHANGE_EVENT'

});

/**
 * Register with the dispatcher to handle Data needed on App Boostrap related actions.
 */
BootstrapStore.dispatchToken = AppDispatcher.register(function(payload) {
  AppDispatcher.waitFor([
    AuthStore.dispatchToken
  ]);

  var action = payload.action;

  switch(action.type) {

    case ActionTypes.STARTUP_ACTION:
      BootstrapStore.getShardsAndReplicasets();
      break;

    default:
      return true;
  }

  BootstrapStore.emitChange();

});

module.exports = BootstrapStore;
