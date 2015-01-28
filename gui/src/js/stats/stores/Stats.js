var assign = require('object-assign');
var AppDispatcher = require('../../common/dispatcher/AppDispatcher.js');
var BaseStore = require('../../common/stores/Store.js');
var Constants = require('../constants/Constants.js');
var ActionTypes = Constants.ActionTypes;
var _stats = null;
var _loader = false;

/**
 * Store to manage states
 * related to the statname API
 */

var StatsStore = assign(new BaseStore(), {

  emitChange: function() {
    this.emit(this.CHANGE_EVENT);
  },

  getStatsState: function() {
    return _stats;
  },

  isLoading: function() {
    return _loader;
  },

  CHANGE_EVENT: 'STATS_CHANGE_EVENT'
});

function persistStatsData(response) {
  _stats = response;
};

function loadingState(response) {
  _loader = response;
};

StatsStore.dispatchToken = AppDispatcher.register(function(payload) {

  var action = payload.action;

  switch(action.type) {

    case ActionTypes.GET_STATS:
      persistStatsData(action.stats);
      loadingState(action.loader);
      StatsStore.emitChange();
    break;

    default:

  }
});

module.exports = StatsStore;
