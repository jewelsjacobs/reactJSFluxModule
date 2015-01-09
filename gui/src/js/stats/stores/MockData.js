'use strict';

var assign = require('object-assign');
var Constants = require('../constants/Constants.js');
var AppDispatcher = require('../dispatcher/AppDispatcher.js');
var BaseStore = require('./Store.js');
var APIUtils = require('../utils/APIUtils');

var MockDataStore = assign(new BaseStore(), {

  emitChange: function() {
    this.emit(this.CHANGE_EVENT);
  },

  CHANGE_EVENT: 'MOCK_CHANGE_EVENT',

  getMockShardsAndHosts: APIUtils.getMockJSON('/replicaset.json'),

  getMockStatsNames: APIUtils.getMockJSON('/stats_available.json'),

  getMockGraphData: APIUtils.getMockJSON('/graph.json')

});

MockDataStore.dispatchToken = AppDispatcher.register(function(payload) {
  var action = payload.action;

  switch(action.type) {

    default:
      return true;
  }

  MockDataStore.emitChange();

});

module.exports = MockDataStore;
