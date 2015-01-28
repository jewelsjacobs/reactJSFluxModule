var assign = require('object-assign');
var AppDispatcher = require('../../common/dispatcher/AppDispatcher.js');
var BaseStore = require('../../common/stores/Store.js');
var Constants = require('../constants/Constants.js');
var ActionTypes = Constants.ActionTypes;
var _ = require('lodash');

var _statName = null;

/**
 * Store to manage states
 * related to the statname dropdown
 */

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
