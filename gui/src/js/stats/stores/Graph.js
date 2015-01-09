'use strict';
/**
 * Graph Data interface.
 */
var assign = require('object-assign');
var Constants = require('../constants/Constants.js');
var AppDispatcher = require('../dispatcher/AppDispatcher.js');
var BaseStore = require('./Store.js');
var ActionTypes = Constants.ActionTypes;
var request = require('superagent');

var TOKEN_ROUTE = '/api_token';

/**
 * Auth Headers
 * @type {null}
 * @private
 */
var _auth_headers = null;

/**
 * Get the Auth Headers via Ajax
 * @private
 */
function _getAuthHeaders() {

}

var GraphStore = assign(new BaseStore(), {

  emitChange: function() {
    this.emit(this.CHANGE_EVENT);
  },

  CHANGE_EVENT: 'GRAPH_CHANGE_EVENT',

  /**
   * Public method to get Auth Headers
   * @returns {null}
   */
  getAuthHeaders: function() {
    return _auth_headers;
  }

});

/**
 * Register with the dispatcher to handle Graph Data Store related actions.
 */
GraphStore.dispatchToken = AppDispatcher.register(function(payload) {
  var action = payload.action;

  switch(action.type) {

    case ActionTypes.CHECK_AUTH:
      _getAuthHeaders();
      break;

    default:
      return true;
  }

  GraphStore.emitChange();

});

module.exports = GraphStore;
