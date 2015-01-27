
/**
 * Auth Data interface.
 */
var assign = require('object-assign');
var AppDispatcher = require('../../common/dispatcher/AppDispatcher.js');
var BaseStore = require('../../common/stores/Store.js');
var Constants = require('../constants/Constants.js');
var ActionTypes = Constants.ActionTypes;
var _ = require('lodash');

var _dates = null;

var DateRangeStore = assign(new BaseStore(), {

  emitChange: function() {
    this.emit(this.CHANGE_EVENT);
  },

  getDateRange: function() {
    return _dates;
  },

  CHANGE_EVENT: 'DATE_RANGE_CHANGE_EVENT'

});

function persistDateRangeData(response) {
  _dates = response;
}

/**
 * Register with the dispatcher to handle Data needed on App Boostrap related actions.
 */
DateRangeStore.dispatchToken = AppDispatcher.register(function(payload) {

  var action = payload.action;

  switch(action.type) {

    case ActionTypes.GET_DATE_RANGE:
      persistDateRangeData(action.dates);
      DateRangeStore.emitChange();
      break;

    default:

  }
});

module.exports = DateRangeStore;
