'use strict';

/**
 * Auth Action Creators.
 */

var AppDispatcher = require('../dispatcher/AppDispatcher.js');
var Constants = require('../constants/Constants.js');
var ActionTypes = Constants.ActionTypes;

var ShardsCommand = require('../commands/shards.js');


module.exports = {
    getShards: function() {
        new ShardsCommand().execute(function (err, shards) {
            AppDispatcher.handleViewAction({
                type: ActionTypes.GET_SHARDS,
                shards: shards
            });
        });
    },

    getStatNames: function(shards) {
        APIUtils.getStatNames(shards, function(err, statNames) {
            AppDispatcher.handleViewAction({
                type: ActionTypes.GET_STAT_NAMES,
                statNames: statNames
            });
        })
    },

    getGraphData: function() {
        APIUtils.getGraph(statName, startDate, endDate, hosts, function(err, graphData) {
            AppDispatcher.handleViewAction({
                type: ActionTypes.GET_GRAPH_DATA,
                graphData: graphData
            });
        })
    },

    getGraphParams: function(paramObj) {
        AppDispatcher.handleViewAction({
            type: ActionTypes.GET_GRAPH_PARAMS,
            paramObj: paramObj
        });
    }
};

