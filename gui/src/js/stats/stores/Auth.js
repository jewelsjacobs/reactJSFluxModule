'use strict';
/**
 * Auth Data interface.
 */
var assign = require('object-assign');
var BaseStore = require('./Store.js');
var request = require('superagent');
var AppDispatcher = require('../dispatcher/AppDispatcher.js');
var async = require('async');
var request = require('superagent');
var TOKEN_ROUTE = '/api_token';

/**
 * Get the Auth Headers via Ajax
 * with a callback for the nodeJS async
 * module.
 *
 * Also uses nodeJS superagent for
 * async calls which is cleaner than promises.
 *
 * @link https://github.com/visionmedia/superagent
 * @link https://github.com/caolan/async
 * @param url
 * @param cb
 * @returns {*}
 * @private
 */
function _getAuthHeaders(url, cb) {
  //return request
  //  .get(TOKEN_ROUTE)
  //  .end(function(err, res) {
  //    authHeaders = {
  //      "X-Auth-Account": res['user'],
  //      "X-Auth-Token": res['api_token']
  //    };
  //    return cb(err, authHeaders);
  //  });
  //};
  return cb(null,{
    "X-Auth-Account": "appboy",
    "X-Auth-Token": "ImM4MzhlNGE0ODY2ODRhMjZhYzQ1NDA3ODM1NWM5ZTgyIg.B5XUqg.hPjP_g-q9BTDLjk-s7m4f_e1Z44"
  }, url);
};

var AuthStore = assign(new BaseStore(), {

  emitChange: function() {
    this.emit(this.CHANGE_EVENT);
  },

  CHANGE_EVENT: 'AUTH_CHANGE_EVENT',

  /**
   * Public method to get Auth Headers
   *
   * @param url
   * @param cb
   * @returns {*}
   */
  getAuthHeaders: function(url, cb) {
    _getAuthHeaders(url, cb);
  }

});

/**
 * Register with the dispatcher to handle Data needed on App Boostrap related actions.
 */
AuthStore.dispatchToken = AppDispatcher.register(function(payload) {

  var action = payload.action;

  switch(action.type) {

    default:
      return true;
  }

  AuthStore.emitChange();

});

module.exports = AuthStore;
