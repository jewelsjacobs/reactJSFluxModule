var keyMirror = require('keymirror');

/**
 * Stats Module Action Constants
 * @type {{ActionTypes: (*|exports)}}
 */

module.exports = {

  ActionTypes: keyMirror({
   GET_STATS: null,
   GET_GRAPH_DATA: null,
   GET_STAT_NAME: null,
   GET_DATE_RANGE: null,
   UPDATE_GRAPH: null
  })

};
