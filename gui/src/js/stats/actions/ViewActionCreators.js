'use strict';

/**
 * Action Creators module.
 *
 * {@link http://facebook.github.io/flux/docs/actions-and-the-dispatcher.html#content}
 *
 * @module actions/ViewActionCreators
 * @author Julia Jacobs
 * @version 1.0.0
 */
var AppDispatcher = require('../dispatcher/AppDispatcher.js');
var Constants = require('../constants/Constants.js');
var ActionTypes = Constants.ActionTypes;

var StatsCommand = require('../commands/stats.js');
var GraphCommand = require('../commands/graph.js');

module.exports = {

/**
 * getStats action
 *
 * @see StatsCommand
 * @see AppDispatcher
 * @see main.js
 * @fires ActionTypes#GET_STATS
 *
 * @description Action for statNames dropdown and graph items.
 */
  getStats: function() {
    new StatsCommand().execute(function (err, stats) {
      AppDispatcher.handleViewAction({
        type: ActionTypes.GET_STATS,
        stats: stats
      });
    });
  },

  getStatName: function(statName){
    AppDispatcher.handleViewAction({
       type: ActionTypes.GET_STAT_NAME,
       statName: statName
     });
  },

  updateGraph: function(updateState){
    AppDispatcher.handleViewAction({
     type: ActionTypes.UPDATE_GRAPH,
     updateState: updateState
   });
  },

  getDateRange: function(dates){
    AppDispatcher.handleViewAction({
     type: ActionTypes.GET_DATE_RANGE,
     dates: dates
   });
  },

  /**
   * getGraphData action
   *
   * @see GraphCommand
   * @see AppDispatcher
   * @see Graph.react
   * @fires ActionTypes.GET_GRAPH_DATA
   *
   * @description Action for graph.
   *
   * @param {string} replicaset - single replicaset
   * @param {string} statName - value of chosen statName from dropdown
   * @param {Object} startDate - value of start date from date range selector
   * @param {Object} endDate - value of end date from date range selector
   * @param {Array} hosts - single array of hosts
   */
    getGraphData: function(replicaset, statName, startDate, endDate, hosts) {
      new GraphCommand({
        statName: statName,
        startDate: startDate,
        endDate: endDate,
        hosts: hosts
      }).execute(function (err, graph) {
        AppDispatcher.handleViewAction({
           type: ActionTypes.GET_GRAPH_DATA,
           graphData: graph,
           replicaset: replicaset
         });
      })
    }
};

