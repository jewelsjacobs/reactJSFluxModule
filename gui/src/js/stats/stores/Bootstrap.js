'use strict';
/**
 * Graph Data interface.
 */
var assign = require('object-assign');
var Constants = require('../constants/Constants.js');
var AppDispatcher = require('../dispatcher/AppDispatcher.js');
var AuthStore = require('./Auth.js');
var BaseStore = require('./Store.js');
var ActionTypes = Constants.ActionTypes;
var request = require('superagent');
var APIUtils = require('../utils/APIUtils.js');

var _instanceName = APIUtils.getInstance();
var _apiUrl = APIUtils.getApiUrls();
var _replicaSetUrl = null;
var _authHeaders = AuthStore.getAuthHeaders();
var _shards = {};

function _getReplicaSetUrl() {
  _replicaSetUrl = APIUtils.formatURL("{0}/v2/instance/{1}/replicaset", _apiUrl, _instanceName);
};

function _getApiUrls() {
  //request
  //  .get("/api_urls")
  //  .end(function(err, res) {
  //     if (err) throw err;
  //     return res.data['api_urls'];
  //   });
  //}

  return "https://sjc-api.objectrocket.com"
};

function _getShards() {
  _getReplicaSetUrl();
  request
    .get(_replicaSetUrl)
    .set(_authHeaders)
    .end(function(err, res) {
       if (err) throw err;

       res.data['data'].forEach(function(element, index){
         res.data['data'][index].forEach(function(element, index){
           _shards[index] = element;
         });
       });

       return _shards;
     });
};

function _getInstance() {
  //var pathArray = window.location.pathname.split( '/' );
  ////Get instance - http://localhost:5051/instances/test_julia/stats
  //return pathArray[2];

  return "appboy01_prod";
};


var ShardsAndHostsStore = assign(new BaseStore(), {

  emitChange: function() {
    this.emit(this.CHANGE_EVENT);
  },

  getShards: function() {
    return _getShards();
  },

  getInstance: function() {
    return _getInstance();
  },

  getApiUrls: function() {
    return _getApiUrls();
  },

  CHANGE_EVENT: 'SHARDS_AND_HOSTS_CHANGE_EVENT'

});

/**
 * Register with the dispatcher to handle Graph Data Store related actions.
 */
ShardsAndHostsStore.dispatchToken = AppDispatcher.register(function(payload) {
  AppDispatcher.waitFor([
     AuthStore.dispatchToken
  ]);

  var action = payload.action;

  switch(action.type) {
    default:
      return true;
  }

  ShardsAndHostsStore.emitChange();

});

module.exports = ShardsAndHostsStore;
