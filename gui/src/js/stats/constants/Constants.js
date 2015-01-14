'use strict';
/**
 * Application constants.
 */
var keyMirror = require('keymirror');

module.exports = {

  ActionTypes: keyMirror({
   GET_SHARDS: null,
   SELECT_STAT: null,
   GET_STAT_NAMES: null,
   SELECT_DATE_RANGE: null,
   GET_HOSTS: null,
   UPDATE_GRAPH: null
  }),

  PayloadSources: keyMirror({
    SERVER_ACTION: null,
    VIEW_ACTION: null
  })

};
