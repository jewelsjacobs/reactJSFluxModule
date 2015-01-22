/** @jsx React.DOM */
'use strict';
/**
 * The application component. This is the top-level component.
 */
var React = require('react');
var Actions = require('../actions/ViewActionCreators.js');
var BS = require('react-bootstrap');
var DateRangePicker = require('react-bootstrap-daterangepicker');
var moment = require('moment');

var DateTimePicker = React.createClass({
  getInitialState: function() {
    return {
      ranges: {
        'Today': [moment().subtract(1, 'day'), moment()],
        'Yesterday': [moment().subtract(2, 'days'), moment().subtract(1, 'day')],
        'Last 7 Days': [moment().subtract(6, 'days'), moment()],
        'Last 30 Days': [moment().subtract(29, 'days'), moment()],
        'This Month': [moment().startOf('month'), moment().endOf('month')],
        'Last Month': [moment().subtract(1, 'month').startOf('month'), moment().subtract(1, 'month').endOf('month')]
      },
      startDate: moment().subtract(1, 'day'),
      endDate: moment()
    };
  },
  handleEvent: function (event, picker) {
    this.setState({
      startDate: picker.startDate,
      endDate: picker.endDate
    });
    Actions.getDateRange({
     startDate: this.state.startDate,
     endDate: this.state.endDate
    });
  },
  render: function() {
    var start = this.state.startDate.format('YYYY-MM-DD h:mm:ss a');
    var end = this.state.endDate.format('YYYY-MM-DD h:mm:ss a');
    var label = start + ' - ' + end;
    if (start === end) {
      label = start;
    }

    return (
      <BS.Col xs={6} md={4}>
        <label>Range</label>
        <DateRangePicker startDate={this.state.startDate} onApply={this.handleEvent} timePicker={true} timePicker12Hour={true} timePickerSeconds={true} endDate={this.state.endDate} ranges={this.state.ranges}>
          <BS.Button className="selected-date-range-btn" style={{width: '100%'}}>
            <div className="pull-left">
              <BS.Glyphicon glyph="calendar" />
            </div>
            <div className="pull-right">
              <span>
                {label}
              </span>
              <span className="caret"></span>
            </div>
          </BS.Button>
        </DateRangePicker>
      </BS.Col>
    );
  }
});

module.exports = DateTimePicker;
