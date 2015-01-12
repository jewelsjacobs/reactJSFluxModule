'use strict';
/**
 * Auth Data interface.
 */
var assign = require('object-assign');
var Constants = require('../constants/Constants.js');
var AppDispatcher = require('../dispatcher/AppDispatcher.js');
var BaseStore = require('./Store.js');
var request = require('superagent');
var TOKEN_ROUTE = '/api_token';

/**
 * Auth Headers
 * @type {null}
 * @private
 */
var _authHeaders = null;

/**
 * Get the Auth Headers via Ajax
 * @private
 */
function _getAuthHeaders() {
  request.get(TOKEN_ROUTE, function(err, res){
    if (err) throw err;
    _authHeaders = {"X-Auth-Account": "appboy", "X-Auth-Token": "ImM4MzhlNGE0ODY2ODRhMjZhYzQ1NDA3ODM1NWM5ZTgyIg.B5XUqg.hPjP_g-q9BTDLjk-s7m4f_e1Z44"};
  });
}

var AuthStore = assign(new BaseStore(), {

  emitChange: function() {
    this.emit(this.CHANGE_EVENT);
  },

  CHANGE_EVENT: 'AUTH_CHANGE_EVENT',

  /**
   * Public method to get Auth Headers
   * @returns {null}
   */
  getAuthHeaders: function() {
    return _authHeaders;
  }

});

/**
 * Register with the dispatcher to handle Graph Data Store related actions.
 */
AuthStore.dispatchToken = AppDispatcher.register(function(payload) {
  var action = payload.action;

  switch(action.type) {
    default:
      _getAuthHeaders();
      AuthStore.emitChange();
      return true;
  }

});

module.exports = AuthStore;
