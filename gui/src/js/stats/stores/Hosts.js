'use strict';
/**
 * Auth Data interface.
 */
var assign = require('object-assign');
var AppDispatcher = require('../dispatcher/AppDispatcher.js');
var BaseStore = require('./Store.js');
var Constants = require('../constants/Constants.js');
var ActionTypes = Constants.ActionTypes;
var _hosts = null;

var HostsStore = assign(new BaseStore(), {

  emitChange: function() {
    this.emit(this.CHANGE_EVENT);
  },

  getHostsState: function() {
    return _hosts;
  },

  CHANGE_EVENT: 'HOSTS_CHANGE_EVENT'

});

function persistHostsData(response) {
  _hosts = response;
}

/**
 * Register with the dispatcher to handle Data needed on App Boostrap related actions.
 */
HostsStore.dispatchToken = AppDispatcher.register(function(payload) {

  var action = payload.action;

  switch(action.type) {

    case ActionTypes.GET_HOSTS:
      persistHostsData(action.hosts);
      HostsStore.emitChange();
      break;

    default:

  }
});

module.exports = HostsStore;
