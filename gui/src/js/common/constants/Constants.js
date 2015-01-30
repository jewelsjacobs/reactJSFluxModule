var keyMirror = require('keymirror');

/**
 * Base Application Constants
 *
 * @type {{PayloadSources: (*|exports)}}
 */

module.exports = {

  PayloadSources: keyMirror({
    SERVER_ACTION: null,
    VIEW_ACTION: null
  })

};
