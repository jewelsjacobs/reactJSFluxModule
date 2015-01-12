'use strict';
/**
 * Graph Data interface.
 */
var assign = require('object-assign');
var Constants = require('../constants/Constants.js');
var AppDispatcher = require('../dispatcher/AppDispatcher.js');
var AuthStore = require('./Auth.js');
var ShardsAndHostsStore = require('./ShardsAndHosts.js');
var BaseStore = require('./Store.js');
var ActionTypes = Constants.ActionTypes;
var request = require('superagent');
var APIUtils = require('../utils/APIUtils.js');

var _instanceName = APIUtils.getInstance();
var _shards = ShardsAndHostsStore.getShards();
var _host = _getHost();
var _apiUrl = APIUtils.getApiUrl();
var _availableStatsUrl = null;
var _authHeaders = AuthStore.getAuthHeaders();
var TOKEN_ROUTE = '/api_token';

function _getStatsData() {

};

function _getGraphData(range_data) {

  var url = APIUtils.formatURL(
    "{0}/v2/graph/ad_hoc?granularity={1}&start_time={2}&end_time={3}",
    _apiUrl,
    range_data.granularity,
    range_data.startDate,
    range_data.endDate
  );

  request
    .get(url)
    .set(_authHeaders)
    .end(function(err, res) {
           if (err) throw err;
           return res.data['stats'];
         });
};

var GraphStore = assign(new BaseStore(), {

  emitChange: function() {
    this.emit(this.CHANGE_EVENT);
  },

  CHANGE_EVENT: 'GRAPH_CHANGE_EVENT'

});

/**
 * Register with the dispatcher to handle Graph Data Store related actions.
 */
GraphStore.dispatchToken = AppDispatcher.register(function(payload) {
  var action = payload.action;

  switch(action.type) {

    case ActionTypes.GET_DATE_RANGE:
      this.getGraphData(action.range_data);
      break;

    default:
      return true;
  }

  GraphStore.emitChange();

});

module.exports = GraphStore;
