var Actions = require('../actions/ActionCreators.js');
var React = require('react');
var BS = require('react-bootstrap');
var DateRangePicker = require('react-bootstrap-daterangepicker');
var moment = require('moment');

var DateRangeSelector = React.createClass({
  getInitialState: function () {
    return {
      ranges: {
        'Today': [moment(), moment()],
        'Yesterday': [moment().subtract(1, 'days'), moment().subtract(1, 'days')],
        'Last 7 Days': [moment().subtract(6, 'days'), moment()],
        'Last 30 Days': [moment().subtract(29, 'days'), moment()],
        'This Month': [moment().startOf('month'), moment().endOf('month')],
        'Last Month': [moment().subtract(1, 'month').startOf('month'), moment().subtract(1, 'month').endOf('month')]
      },
      startDate: moment().subtract(29, 'days'),
      endDate: moment()
    };
  },
  handleEvent: function (event, picker) {
    this.setState({
      startDate: picker.startDate,
      endDate: picker.endDate
    });
  },
  render: function () {
    var start = this.state.startDate.format('YYYY-MM-DD h:mm:ss a');
    var end = this.state.endDate.format('YYYY-MM-DD h:mm:ss a');
    var label = start + ' - ' + end;
    if (start === end) {
      label = start;
    }
    return (
      <BS.Col md={3}>
        <label>Range</label>
        <DateRangePicker startDate={this.state.startDate} timePicker={true} timePicker12Hour={true} timePickerSeconds={true} endDate={this.state.endDate} ranges={this.state.ranges} onEvent={this.handleEvent}>
          <BS.Button className="selected-date-range-btn" style={{width:'100%'}}>
            <div className="pull-left"><BS.Glyphicon glyph="calendar" /></div>
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

module.exports = DateRangeSelector;
