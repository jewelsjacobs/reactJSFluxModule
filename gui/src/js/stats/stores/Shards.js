'use strict';
/**
 * Auth Data interface.
 */
var assign = require('object-assign');
var AppDispatcher = require('../dispatcher/AppDispatcher.js');
var BaseStore = require('./Store.js');
var Constants = require('../constants/Constants.js');
var ActionTypes = Constants.ActionTypes;
var _shards = null;

var ShardsStore = assign(new BaseStore(), {

  emitChange: function() {
    this.emit(this.CHANGE_EVENT);
  },

  getShardsState: function() {
    return _shards;
  },

  CHANGE_EVENT: 'SHARDS_CHANGE_EVENT'
});

function persistShardsData(response) {
  _shards = response;
};

/**
 * Register with the dispatcher to handle Data needed on App Boostrap related actions.
 */
ShardsStore.dispatchToken = AppDispatcher.register(function(payload) {

  var action = payload.action;

  switch(action.type) {

    case ActionTypes.GET_SHARDS:
      persistShardsData(action.shards);
      ShardsStore.emitChange();
    break;

    default:

  }
});

module.exports = ShardsStore;
