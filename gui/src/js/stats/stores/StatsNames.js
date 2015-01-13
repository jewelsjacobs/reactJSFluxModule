'use strict';
/**
* Auth Data interface.
*/
var assign = require('object-assign');
var Constants = require('../constants/Constants.js');
var AppDispatcher = require('../dispatcher/AppDispatcher.js');
var BaseStore = require('./Store.js');
var AuthStore = require('./Auth.js');
var BootstrapStore = require('./Bootstrap.js');
var ActionTypes = Constants.ActionTypes;
var request = require('superagent');
var async = require('async');
var APIUtils = require('../utils/APIUtils.js');
var _statNames = [];

/**
 * Formats a url used in call to get stats names data
 * @returns {*}
 * @private
 */
function _getAvailableStatsUrl(apiUrl, host, cb) {
  var url = APIUtils.formatURL(
    "{0}/v2/instance/{1}/host/{2}/stats/available",
    apiUrl, BootstrapStore.getInstance(),
    host
  );
  return cb(null, url);
};

/**
 * Get Shards as callback to work with async waterfall
 * callback
 * @returns {*}
 * @private
 */
function _getShardsAndReplicasetsAsCallBack(cb) {
  return cb(null, BootstrapStore.getShardsAndReplicasets())
};

/**
 * Gets the stat names from the API
 * @param authHeaders
 * @param url
 * @param cb
 * @private
 */
function _getStatNamesFromApi(authHeaders, url, cb) {
  request
    .get(url)
    .set(authHeaders)
    .end(function(err, res) {
           if (err) throw err;
           return res.data['data']['names'];
         });
};

/**
 * Gets the host from the shards
 *
 * @param shards
 * @param apiUrl
 * @param cb
 * @returns {*}
 * @private
 */
function _getHost(shards, apiUrl, cb) {
  var host = null;

  shards.forEach(function(shard){
    if (shard.length == 0) {
      throw new Error('No shards')
    }
    return cb(null, apiUrl, shard[0]);
  });

  if (host === null) {
    return cb(null, apiUrl, []);
  };
}

/**
 * Gets the stat name from the dropdown
 * @param statName
 * @private
 */
function _getStatName(statName) {
  console.log(statName);
};

/**
 * Async waterfall method to get stat names
 * @private
 */
function _updateStatNames() {

};

var StatsNamesStore = assign(new BaseStore(), {

  emitChange: function() {
    this.emit(this.CHANGE_EVENT);
  },

  CHANGE_EVENT: 'STAT_CHANGE_EVENT',

  /**
   * Returns available stat names for instance
   * @returns {*}
   */
  getStatNames: function() {
    return _statNames;
  },

  setStatNames: function() {
    async.waterfall([
        function(cb) {
          BootstrapStore.getApiUrls(cb)
        },
        _getShardsAndReplicasetsAsCallBack,
        _getHost,
        _getAvailableStatsUrl,
        AuthStore.getAuthHeaders,
        _getStatNamesFromApi
      ], function (err, result) {
        _statNames = result;
        this.emitChange();
    });
  }

});

/**
* Register with the dispatcher to handle Graph Data Store related actions.
*/
StatsNamesStore.dispatchToken = AppDispatcher.register(function(payload) {

  AppDispatcher.waitFor([
    BootstrapStore.dispatchToken
  ]);

  var action = payload.action;

  switch(action.type) {
  /**
   * Occurs when stat name drop down selects option
   */
    case ActionTypes.GET_STAT_NAME:
      _getStatName(action.statName);
      break;

    default:
      return true;
  }

  StatsNamesStore.emitChange();

});

module.exports = StatsNamesStore;
