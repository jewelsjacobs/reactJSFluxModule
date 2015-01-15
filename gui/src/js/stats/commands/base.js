'use strict';

var async = require('async');
var locks = require('locks');
var _ = require('lodash');

//
// BaseCommand
// Superclass for all of our command objects. Automatically handles dependencies.
//

function BaseCommand(options) {
    this.options = options;
    this.prereq = {};
};

BaseCommand.prototype = {
    mutexes: {},
    
    getMutex: function () {
        var name = this.constructor.name;
        var mutex = this.mutexes[name] = this.mutexes[name] || locks.createMutex();
        return mutex;
    },
    
    execute: function (callback) {
        var mutex = this.getMutex();
        
        mutex.lock(function () {
            this.doExecute(function (err, data) {
                mutex.unlock();
                callback(err, data);
            })
        }.bind(this));
    },
    
    doExecute: function (callback) {
        var calls = {};
        
        _.each(this.prereq, function(value, key) {
            calls[key] = value.execute.bind(value);
        });

        async.parallel(calls, function(err, data) {
            this.run(err, data, callback);
        }.bind(this));
    },

    run: function (err, data, callback) {
        callback(err, data);
    }
};

BaseCommand.prototype.constructor = BaseCommand;
module.exports = BaseCommand;
