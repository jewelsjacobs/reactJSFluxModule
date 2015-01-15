'use strict';

/**
 * Auth Action Creators.
 */

var AppDispatcher = require('../dispatcher/AppDispatcher.js');
var Constants = require('../constants/Constants.js');
var ActionTypes = Constants.ActionTypes;

var ShardsCommand = require('../commands/shards.js');
var StatNamesCommand = require('../commands/stat_names.js');
var GraphCommand = require('../commands/graph.js');

module.exports = {
    getShards: function() {
      new ShardsCommand().execute(function (err, shards) {
        AppDispatcher.handleViewAction({
          type: ActionTypes.GET_SHARDS,
          shards: shards
        });
      });
    },

    getStatNames: function() {
      new StatNamesCommand().execute(function (err, statNames) {
        AppDispatcher.handleViewAction({
          type: ActionTypes.GET_STAT_NAMES,
          statNames: statNames
        });
      })
    },

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

