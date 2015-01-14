'use strict';
/**
 * Auth Data interface.
 */
var assign = require('object-assign');
var AppDispatcher = require('../dispatcher/AppDispatcher.js');
var BaseStore = require('./Store.js');
var Constants = require('../constants/Constants.js');
var ActionTypes = Constants.ActionTypes;
var _stat = null;

var StatStore = assign(new BaseStore(), {

  emitChange: function() {
    this.emit(this.CHANGE_EVENT);
  },

  getStatState: function() {
    return _stat;
  },

  CHANGE_EVENT: 'DATE_CHANGE_EVENT'

});

function persistStatData(response) {
  _stat = response;
}

/**
 * Register with the dispatcher to handle Data needed on App Boostrap related actions.
 */
StatStore.dispatchToken = AppDispatcher.register(function(payload) {

  var action = payload.action;

  switch(action.type) {

    case ActionTypes.SELECT_STAT:
      persistStatData(action.stat);
      StatStore.emitChange();
      break;

    default:

  }
});

module.exports = StatStore;
