'use strict';
/**
 * Auth Data interface.
 */
var assign = require('object-assign');
var AppDispatcher = require('../dispatcher/AppDispatcher.js');
var BaseStore = require('./Store.js');
var Constants = require('../constants/Constants.js');
var ActionTypes = Constants.ActionTypes;
var _date = null;

var DateStore = assign(new BaseStore(), {

  emitChange: function() {
    this.emit(this.CHANGE_EVENT);
  },

  getDateState: function() {
    return _date;
  },

  CHANGE_EVENT: 'DATE_CHANGE_EVENT'

});

function persistDateData(response) {
  _date = response;
}

/**
 * Register with the dispatcher to handle Data needed on App Boostrap related actions.
 */
DateStore.dispatchToken = AppDispatcher.register(function(payload) {

  var action = payload.action;

  switch(action.type) {

    case ActionTypes.GET_DATE_RANGE:
      persistDateData(action.date);
      DateStore.emitChange();
      break;

    default:

  }
});

module.exports = DateStore;
