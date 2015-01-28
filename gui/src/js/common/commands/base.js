var async = require('async');
var locks = require('locks');
var _ = require('lodash');

/**
 * Represents an Asyncronous action our application can take.
 *
 * Will execute any prerequisites specified in `this.prereq`, and pass the results
 * into the run method for processing.
 *
 * @module commands/base
 * @author Anthony Tarola
 * @version 1.0.0
 * @constructor
 * @param {Object} options - options for the commands to have.
 * @prop {Object} prereq - mapping of key to {Command} instances, which will
 *                         be run before the actual command runs
 * @prop {boolean} locked - should execution of this command be wrapped in a mutex.
 */

function BaseCommand(options) {
  this.options = options;
  this.prereq = {};
  this.locked = false;
};

BaseCommand.prototype = {

  /**
   * @prop {object} mutexes - a set of mutexes, keyed by classname.
   */

  mutexes: {},

  /**
   * Kick off the execution of the command.
   *
   * @public
   * @param {Function} callback - called with the results of the command.
   *                              signature: function (err, results)
   */

  execute: function (callback) {
    var locked = this.locked || false;

    if (locked) {
      this.executeLocked(callback);
    } else {
      this.executeUnlocked(callback);
    }
  },

  /**
   * Wrap the execution of the the command in a mutex, only allowing one
   * command of this type to run at a time.
   *
   * @private
   * @param {Function} callback - called with the results of the command.
   *                              signature: function (err, results)
   */

  executeLocked: function (callback) {
    var mutex = this.getMutex();

    mutex.lock(function () {
      this.doExecute(function (err, data) {
        mutex.unlock();
        callback(err, data);
      });
    }.bind(this));
  },

  /**
   * Execute the command with no mutex.
   *
   * @private
   * @param {Function} callback - called with the results of the command.
   *                              signature: function (err, results)
   */

  executeUnlocked: function (callback) {
    this.doExecute(callback);
  },

  /**
   * The actual execution of the command.
   * This will run all of the specified prerequists in parallel, then pass
   * the results in the run() method.
   *
   * @private
   * @param {Function} callback - called with the results of the command.
   *                              signature: function (err, results)
   */

  doExecute: function (callback) {
    var prereqs = this.prereq || {};
    var calls = {};

    _.each(prereqs, function (value, key) {
      calls[key] = value.execute.bind(value);
    });

    async.parallel(calls, function (err, data) {
      this.run(err, data, callback);
    }.bind(this));
  },

  /**
   * Get the mutex associated with this instance.
   * Note: this requires a properly set-up constructor function.
   *
   * @private
   * @returns {Mutex} - the mutex associated with this instance.
   */

  getMutex: function () {
    var name = this.constructor.name;
    var mutex = this.mutexes[name] = this.mutexes[name] || locks.createMutex();
    return mutex;
  },

  /**
   * Method containing the subclass specific code, should be overridden by subclasses.
   *
   * @abstract
   * @param {Object} err - any errors from the prerequisite commands will exist here.
   * @param {Object} data - the results of the prerequisites will be here, keyed by their names
   *                        in `this.prereq`.
   * @param {Function} callback - called with the results of the command.
   *                              signature: function (err, results)
   */

  run: function (err, data, callback) {
    callback(err, data);
  }
};

BaseCommand.prototype.constructor = BaseCommand;
module.exports = BaseCommand;
