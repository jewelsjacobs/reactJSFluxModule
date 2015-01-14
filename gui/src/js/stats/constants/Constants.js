'use strict';
/**
 * Application constants.
 */
var keyMirror = require('keymirror');

module.exports = {

  ActionTypes: keyMirror({
   GET_SHARDS: null,
   GET_STAT_NAMES: null,
   GET_DATE_RANGE: null,
   GET_SELECTED_STAT_NAME: null
  }),

  PayloadSources: keyMirror({
    SERVER_ACTION: null,
    VIEW_ACTION: null
  })

};
