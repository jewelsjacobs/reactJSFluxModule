var AppDispatcher = require('../../common/dispatcher/AppDispatcher.js');
var Constants = require('../constants/Constants.js');
var ActionTypes = Constants.ActionTypes;
var StatsCommand = require('../commands/stats.js');
var GraphCommand = require('../commands/graph.js');

/**
 * Action Creators module.
 *
 * @link {http://facebook.github.io/flux/docs/actions-and-the-dispatcher.html#content}
 *
 * @module actions/viewactioncreators
 * @author Julia Jacobs
 * @version 1.0.0
 */

module.exports = {

  /**
   * getStats action
   *
   * @see StatsCommand
   * @see AppDispatcher
   * @see StatsNamesTypeAhead.react.js
   * @fires ActionTypes#GET_STATS
   *
   * @description Action for statNames dropdown and graph items.
   */
  getStats: function() {
    new StatsCommand().execute(function (err, stats) {
      AppDispatcher.handleViewAction({
        type: ActionTypes.GET_STATS,
        stats: stats,
        loader: true
      });
    });
  },

  /**
   * getStatName action
   *
   * @see AppDispatcher
   * @see StatsNamesTypeAhead.react.js
   * @fires ActionTypes#GET_STAT_NAME
   *
   * @description Action to send the selected statName.
   * @param {String} statName - name of chosen stat to view in graphs
   */
  getStatName: function(statName){
    AppDispatcher.handleViewAction({
       type: ActionTypes.GET_STAT_NAME,
       statName: statName
     });
  },

  /**
   * updateGraph action
   *
   * @see AppDispatcher
   * @see UpdateGraphButton.react.js
   * @see Graph.react.js
   * @fires ActionTypes#UPDATE_GRAPH
   *
   * @description When 'Update Graph' button is pressed.
   * @param {bool} updateState - a toggled state the graph component
   * can read to see if the button has been pressed or not.
   */
  updateGraph: function(updateState){
    AppDispatcher.handleViewAction({
     type: ActionTypes.UPDATE_GRAPH,
     updateState: updateState,
     loader: false
   });
  },

  /**
   * getDateRange action
   *
   * @see AppDispatcher
   * @see DateTimePicker.react.js
   * @fires ActionTypes#GET_DATE_RANGE
   *
   * @description Start and end dates are sent when 'Apply'
   * button on DateRangePicker is pressed.
   * @param {Object} dates
   */
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
           replicaset: replicaset,
           loader: true
         });
      })
    }
};
