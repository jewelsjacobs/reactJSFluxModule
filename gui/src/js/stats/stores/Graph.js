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
var _graphParams = {
  statName: 'mongodb.opcounters.query',
  startDate: null,
  endDate: null,
  hosts: null
};

var GraphStore = assign(new BaseStore(), {

  emitChange: function() {
    this.emit(this.CHANGE_EVENT);
  },

  getGraphState: function() {
    return _graph;
  },

  getGraphParams: function() {
    return _graphParams
  },

  CHANGE_EVENT: 'GRAPH_CHANGE_EVENT'

});

function persistGraphData(response) {
  _graph = response;
}

function persistGraphParams(response) {
  _.merge(_graphParams, response);
}

/**
 * Register with the dispatcher to handle Data needed on App Boostrap related actions.
 */
GraphStore.dispatchToken = AppDispatcher.register(function(payload) {

  var action = payload.action;

  switch(action.type) {

    case ActionTypes.GET_GRAPH_DATA:
      persistGraphData(action.graphData);
      GraphStore.emitChange();
      break;

    case ActionTypes.GET_GRAPH_PARAMS:
      persistGraphParams(action.paramObj);
      GraphStore.emitChange();
      break;

    default:

  }
});

module.exports = GraphStore;
