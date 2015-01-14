'use strict';
/**
 * Auth Data interface.
 */
var assign = require('object-assign');
var AppDispatcher = require('../dispatcher/AppDispatcher.js');
var BaseStore = require('./Store.js');
var Constants = require('../constants/Constants.js');
var ActionTypes = Constants.ActionTypes;
var _graph = null;

var GraphStore = assign(new BaseStore(), {

  emitChange: function() {
    this.emit(this.CHANGE_EVENT);
  },

  getDateState: function() {
    return _graph;
  },

  CHANGE_EVENT: 'GRAPH_CHANGE_EVENT'

});

function persistGraphData(response) {
  _graph = response;
}

/**
 * Register with the dispatcher to handle Data needed on App Boostrap related actions.
 */
GraphStore.dispatchToken = AppDispatcher.register(function(payload) {

  var action = payload.action;

  switch(action.type) {

    case ActionTypes.UPDATE_GRAPH:
      persistGraphData(action.date);
      GraphStore.emitChange();
      break;

    default:

  }
});

module.exports = GraphStore;
