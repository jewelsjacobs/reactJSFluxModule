'use strict';
/**
 * Auth Action Creators.
 */
var AppDispatcher = require('../dispatcher/AppDispatcher.js');
var Constants = require('../constants/Constants.js');
var ActionTypes = Constants.ActionTypes;

module.exports = {
  getStatName: function(statName) {
    AppDispatcher.handleViewAction({
     type: ActionTypes.GET_STAT_NAME,
     statName: statName
    });
  },

  getDateRange: function(range_data) {
    AppDispatcher.handleViewAction({
     type: ActionTypes.GET_DATE_RANGE,
     range_data: range_data
    });
  },

  updateGraph: function(data) {
    AppDispatcher.handleViewAction({
     type: ActionTypes.UPDATE_GRAPH,
     data: data
    });
  }

};

