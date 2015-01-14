var Actions = require('../actions/ActionCreators.js');
var React = require('react');
var BS = require('react-bootstrap');
var DateRangePicker = require('react-bootstrap-daterangepicker');
var DateStore = require('../stores/Date.js');
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
  sendDateRangeData: function() {
    var secondsDiff = this.state.endDate.diff(this.state.startDate, 'seconds');
    var granularity = null;

    // pick the granularity to be reasonable based on the timespan chosen.
    if (secondsDiff <= 360) { // 6 hours
      granularity = 'minute';
    } else if (secondsDiff <= 259200) {  // 72 hours
      granularity = 'hour';
    } else {
      granularity = 'day';
    };

    Actions.getDateRange({
     startDate :  this.state.startDate,
     endDate : this.state.endDate,
     granularity : granularity
    });
  },
  handleEvent: function (event, picker) {
    this.setState({
      startDate: picker.startDate,
      endDate: picker.endDate
    });
  },
  componentDidMount: function() {
    DateStore.addChangeListener(this._onChange);
  },
  componentWillUnmount: function() {
    DateStore.removeChangeListener(this._onChange);
  },
  _onChange: function() {
    this.setState(DateStore.getDateState());
  },
  render: function () {
    var start = this.state.startDate.format('YYYY-MM-DD h:mm:ss a');
    var end = this.state.endDate.format('YYYY-MM-DD h:mm:ss a');
    var label = start + ' - ' + end;
    if (start === end) {
      label = start;
    }
    return (
      <BS.Col xs={8} md={4}>
        <label>Range</label>
        <DateRangePicker startDate={this.state.startDate} onApply={this.sendDateRangeData} timePicker={true} timePicker12Hour={true} timePickerSeconds={true} endDate={this.state.endDate} ranges={this.state.ranges} onEvent={this.handleEvent}>
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
