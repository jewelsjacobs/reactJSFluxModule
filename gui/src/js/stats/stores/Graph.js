'use strict';
/**
 * Auth Data interface.
 */
var assign = require('object-assign');
var AppDispatcher = require('../dispatcher/AppDispatcher.js');
var BaseStore = require('./Store.js');
var Constants = require('../constants/Constants.js');
var ActionTypes = Constants.ActionTypes;

var _graph = {};

var GraphStore = assign(new BaseStore(), {

  emitChange: function() {
    this.emit(this.CHANGE_EVENT);
  },

  getGraphState: function(replicaset) {
    return _graph[replicaset] || [];
  },

  CHANGE_EVENT: 'GRAPH_CHANGE_EVENT'

});

function persistGraphData(replicaset, response) {
  _graph[replicaset] = response;
}

/**
 * Register with the dispatcher to handle Data needed on App Boostrap related actions.
 */
GraphStore.dispatchToken = AppDispatcher.register(function(payload) {

  var action = payload.action;

  switch(action.type) {

    case ActionTypes.GET_GRAPH_DATA:

      persistGraphData(action.replicaset, action.graphData);
      GraphStore.emitChange(action.replicaset);
      break;

    default:

  }
});

module.exports = GraphStore;
