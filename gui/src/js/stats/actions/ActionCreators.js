'use strict';
/**
 * Auth Action Creators.
 */
var AppDispatcher = require('../dispatcher/AppDispatcher.js');
var Constants = require('../constants/Constants.js');
var ActionTypes = Constants.ActionTypes;
var async = require('async');
var APIUtils = require('../utils/APIUtils.js');
var StatNamesStore = require('../stores/StatNames.js');

module.exports = {
  getShards: function() {
    async.parallel(
      [
        APIUtils.getApiUrls,
        APIUtils.getAuthHeader,
      ], function (err, results) {
        APIUtils.getShards(
          results[0], results[1], function (shards) {
            AppDispatcher.handleViewAction(
              {
                type: ActionTypes.GET_SHARDS,
                shards: arguments[1]
              });
              APIUtils.getStatNames(results[0], results[1], arguments[1], function(err, result){
                AppDispatcher.handleViewAction({
                   type: ActionTypes.GET_STAT_NAMES,
                   statNames: result
                 });
              });
          });
      });
  },

  getDateRange: function(date) {
    AppDispatcher.handleViewAction({
      type: ActionTypes.GET_DATE_RANGE,
      date: date
    });
  }

};

