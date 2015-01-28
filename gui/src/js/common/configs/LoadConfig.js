/**
 * @module configs/loadconfig
 * @description loads configuration from gulp command
 * @see README.md
 */

module.exports = require("./" + process.env.NODE_ENV + ".js", {glob: true});
