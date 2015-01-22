'use strict';
/**
 * Application constants.
 */
var keyMirror = require('keymirror');

module.exports = {

  ActionTypes: keyMirror({
   GET_STATS: null,
   GET_GRAPH_DATA: null,
   GET_STAT_NAME: null,
   GET_DATE_RANGE: null,
   GET_SHARD: null,
   UPDATE_GRAPH: null
  }),

  PayloadSources: keyMirror({
    SERVER_ACTION: null,
    VIEW_ACTION: null
  })

};
