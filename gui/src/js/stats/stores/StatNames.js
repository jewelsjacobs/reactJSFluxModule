'use strict';
/**
 * Auth Data interface.
 */
var assign = require('object-assign');
var AppDispatcher = require('../dispatcher/AppDispatcher.js');
var BaseStore = require('./Store.js');
var Constants = require('../constants/Constants.js');
var ShardsStore = require('./Shards');
var ActionTypes = Constants.ActionTypes;
var _statNames = null;


var StatNamesStore = assign(new BaseStore(), {

  emitChange: function() {
    this.emit(this.CHANGE_EVENT);
  },

  getStatNamesState: function() {
    return _statNames;
  },

  CHANGE_EVENT: 'STAT_NAMES_CHANGE_EVENT'

});

function persistStatNamesData(response) {
  _statNames = response;
}

/**
 * Register with the dispatcher to handle Data needed on App Boostrap related actions.
 */
StatNamesStore.dispatchToken = AppDispatcher.register(function(payload) {

  var action = payload.action;

  switch(action.type) {

    case ActionTypes.GET_STAT_NAMES:
      persistStatNamesData(action.statNames);
      StatNamesStore.emitChange();
      break;

    default:

  }
});

module.exports = StatNamesStore;
