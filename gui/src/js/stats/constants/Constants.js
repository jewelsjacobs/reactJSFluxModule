'use strict';
/**
 * Application constants.
 */
var keyMirror = require('keymirror');

module.exports = {

  ActionTypes: keyMirror({
   GET_STAT_NAME: null,
   UPDATE_GRAPH: null,
   GET_API_URL: null,
   GET_INSTANCE_NAME: null
  }),

  PayloadSources: keyMirror({
    SERVER_ACTION: null,
    VIEW_ACTION: null
  })

};
