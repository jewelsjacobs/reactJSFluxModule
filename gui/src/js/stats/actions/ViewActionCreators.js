'use strict';
/**
 * Auth Action Creators.
 */
var AppDispatcher = require('../dispatcher/AppDispatcher.js');
var Constants = require('../constants/Constants.js');
var ActionTypes = Constants.ActionTypes;
var async = require('async');
var APIUtils = require('../utils/APIUtils.js');

module.exports = {
  getShards: function() {
    async.parallel(
      [
        APIUtils.getApiUrls,
        APIUtils.getAuthHeader,
      ], function (err, results) {
        APIUtils.getShards(results[0], results[1], function (err, shards) {
            AppDispatcher.handleViewAction(
            {
              type: ActionTypes.GET_SHARDS,
              shards: shards
            });
        });
      });
  },

  getStatNames: function(shards) {
    APIUtils.getStatNames(shards, function (err, statNames){
      AppDispatcher.handleViewAction({
         type: ActionTypes.GET_STAT_NAMES,
         statNames: statNames
       });
    })
  },

  selectStat: function(stat) {
    AppDispatcher.handleViewAction({
     type: ActionTypes.SELECT_STAT,
     stat: stat
    });
  },

  getDateRange: function(dateRange) {
    AppDispatcher.handleViewAction({
      type: ActionTypes.SELECT_DATE_RANGE,
      dateRange: dateRange
    });
  },

  getHosts: function(hosts) {
    AppDispatcher.handleViewAction({
     type: ActionTypes.GET_HOSTS,
     hosts: hosts
   });
  },

  updateGraph: function() {
    APIUtils.getGraph(statName, hosts, startDate, endDate, function (err, statNames){
      AppDispatcher.handleViewAction({
         type: ActionTypes.GET_STAT_NAMES,
         statNames: statNames
       });
    })
  }

};

