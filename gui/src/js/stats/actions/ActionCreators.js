'use strict';
/**
 * Auth Action Creators.
 */
var AppDispatcher = require('../dispatcher/AppDispatcher.js');
var Constants = require('../constants/Constants.js');
var ActionTypes = Constants.ActionTypes;

module.exports = {

  getApiUrl: function(apiUrl) {
    AppDispatcher.handleServerAction({
      type: ActionTypes.GET_API_URL,
      apiUrl: apiUrl
    });
  },

  getInstanceName: function(instanceName) {
    AppDispatcher.handleViewAction({
      type: ActionTypes.GET_INSTANCE_NAME,
      instanceName: instanceName
    });
  },

  getStatName: function(statName) {
    AppDispatcher.handleViewAction({
     type: ActionTypes.GET_STAT_NAME,
     statName: statName
    });
  },

  getRange: function(data) {
    AppDispatcher.handleViewAction({
     type: ActionTypes.UPDATE_GRAPH,
     data: data
    });
  }

};

