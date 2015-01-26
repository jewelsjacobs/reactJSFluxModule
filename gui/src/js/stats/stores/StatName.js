'use strict';
/**
 * Auth Data interface.
 */
var assign = require('object-assign');
var AppDispatcher = require('../dispatcher/AppDispatcher.js');
var BaseStore = require('./Store.js');
var Constants = require('../constants/Constants.js');
var ActionTypes = Constants.ActionTypes;
var _ = require('lodash');

var _statName = null;

var StatNameStore = assign(new BaseStore(), {

  emitChange: function() {
    this.emit(this.CHANGE_EVENT);
  },

  getStatName: function() {
    return _statName;
  },

  CHANGE_EVENT: 'STAT_NAME_CHANGE_EVENT'

});

function persistStatNameData(response) {
  _statName = response;
}

/**
 * Register with the dispatcher to handle Data needed on App Boostrap related actions.
 */
StatNameStore.dispatchToken = AppDispatcher.register(function(payload) {

  var action = payload.action;

  switch(action.type) {

    case ActionTypes.GET_STAT_NAME:
      persistStatNameData(action.statName);
      StatNameStore.emitChange();
      break;

    default:

  }
});

module.exports = StatNameStore;
