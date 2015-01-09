'use strict';
/**
 * Auth Data interface.
 */
var assign = require('object-assign');
var Constants = require('../constants/Constants.js');
var AppDispatcher = require('../dispatcher/AppDispatcher.js');
var BaseStore = require('./Store.js');
var AuthStore = require('./Auth');
var ShardsAndHostsStore = require('./ShardsAndHosts');
var ActionTypes = Constants.ActionTypes;
var request = require('superagent');
var APIUtils = require('../utils/APIUtils');

var _instanceName = ShardsAndHostsStore.getInstanceName();
var _shards = ShardsAndHostsStore.getShards();
var _host = _getHost();
var _apiUrl = ShardsAndHostsStore.getApiUrl();
var _availableStatsUrl = null;
var _authHeaders = AuthStore.getAuthHeaders();

function _getAvailableStatsUrl() {
  _availableStatsUrl = APIUtils.formatURL(
    "{0}/v2/instance/{1}/host/{2}/stats/available", _apiUrl, _instanceName, _host
  );
};

function _getHost() {
  var host = null;

  _shards.forEach(function(shard){
    if (shard.length == 0) {
      return;
    }
    host = shard[0];
  });

  if (host === null) {
    return []
  };
}

function _getStatNames() {

  _getAvailableStatsUrl();

  request
    .get(_availableStatsUrl)
    .set(_authHeaders)
    .end(function(err, res) {
           if (err) throw err;
           return res.data['data']['names'];
    });
};

var StatsNamesStore = assign(new BaseStore(), {

  emitChange: function() {
    this.emit(this.CHANGE_EVENT);
  },

  CHANGE_EVENT: 'STAT_CHANGE_EVENT',

  /**
   * Public method to get Auth Headers
   * @returns {null}
   */
  getStatNames: function() {
    return _getStatNames();
  }

});

/**
 * Register with the dispatcher to handle Graph Data Store related actions.
 */
StatsNamesStore.dispatchToken = AppDispatcher.register(function(payload) {

  AppDispatcher.waitFor([
    ShardsAndHostsStore.dispatchToken
  ]);

  var action = payload.action;

  switch(action.type) {

    case ActionTypes.CHECK_AUTH:
      _getStatNames();
      break;

    default:
      return true;
  }

  StatsNamesStore.emitChange();

});

module.exports = StatsNamesStore;
