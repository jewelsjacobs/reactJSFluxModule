'use strict';
/**
 * Auth Data interface.
 */
var assign = require('object-assign');
var AppDispatcher = require('../dispatcher/AppDispatcher.js');
var BaseStore = require('./Store.js');
var Constants = require('../constants/Constants.js');
var ActionTypes = Constants.ActionTypes;
var _stats = null;

var StatsStore = assign(new BaseStore(), {

  emitChange: function() {
    this.emit(this.CHANGE_EVENT);
  },

  getStatsState: function() {
    return _stats;
  },

  CHANGE_EVENT: 'STATS_CHANGE_EVENT'
});

function persistStatsData(response) {
  _stats = response;
};

/**
 * Register with the dispatcher to handle Data needed on App Boostrap related actions.
 */
StatsStore.dispatchToken = AppDispatcher.register(function(payload) {

  var action = payload.action;

  switch(action.type) {

    case ActionTypes.GET_STATS:
      persistStatsData(action.stats);
      StatsStore.emitChange();
    break;

    default:

  }
});

module.exports = StatsStore;
