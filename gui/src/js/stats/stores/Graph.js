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
var _update = false;

var _graph = {};

var GraphStore = assign(new BaseStore(), {

  emitChange: function() {
    this.emit(this.CHANGE_EVENT);
  },

  getGraphState: function(replicaset) {
    return _graph[replicaset];
  },

  updateGraph: function() {
    return _update;
  },

  CHANGE_EVENT: 'GRAPH_CHANGE_EVENT'

});

function persistGraphData(replicaset, response) {
  _graph[replicaset] = response;
}

function persistUpdateState(response) {
  _update = response;
}

/**
 * Register with the dispatcher to handle Data needed on App Boostrap related actions.
 */
GraphStore.dispatchToken = AppDispatcher.register(function(payload) {

  var action = payload.action;

  switch(action.type) {

    case ActionTypes.UPDATE_GRAPH:
      persistUpdateState(action.updateState);
      GraphStore.emitChange();
      break;

    case ActionTypes.GET_GRAPH_DATA:
      persistGraphData(action.replicaset, action.graphData);
      GraphStore.emitChange();
      break;

    default:

  }
});

module.exports = GraphStore;
