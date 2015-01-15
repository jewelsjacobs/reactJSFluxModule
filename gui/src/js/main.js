/** @jsx React.DOM */
'use strict';
/**
 * The application component. This is the top-level component.
 */
var React = require('react');
var Actions = require('./stats/actions/ViewActionCreators.js');
var GraphItems = require('./stats/components/GraphItems.react.js');
var APIUtils = require('./stats/utils/APIUtils.js');
var BS = require('react-bootstrap');
var ShardsStore = require('./stats/stores/Shards.js');
var StatNamesStore = require('./stats/stores/StatNames.js');
var DateRangePicker = require('react-bootstrap-daterangepicker');
var moment = require('moment');

var Stats = React.createClass({
    getInitialState: function() {
      return {
        shards: ShardsStore.getShardsState(),
        value: 'mongodb.opcounters.query',
        ranges: {
          'Today': [moment().subtract(1, 'day'), moment()],
          'Yesterday': [moment().subtract(2, 'days'), moment().subtract(1, 'day')],
          'Last 7 Days': [moment().subtract(6, 'days'), moment()],
          'Last 30 Days': [moment().subtract(29, 'days'), moment()],
          'This Month': [moment().startOf('month'), moment().endOf('month')],
          'Last Month': [moment().subtract(1, 'month').startOf('month'), moment().subtract(1, 'month').endOf('month')]
        },
        startDate: moment().subtract(1, 'day'),
        endDate: moment(),
        statNames: StatNamesStore.getStatNamesState()
      };
    },
    handleEvent: function (event, picker) {
      this.setState({
        startDate: picker.startDate,
        endDate: picker.endDate
      });
    },
    componentDidMount: function() {
      ShardsStore.addChangeListener(this._onChange);
      StatNamesStore.addChangeListener(this._onChange);
    },
    componentWillUnmount: function() {
      ShardsStore.removeChangeListener(this._onChange);
      StatNamesStore.removeChangeListener(this._onChange);
    },
    _onChange: function() {
      this.setState({
        shards: ShardsStore.getShardsState(),
        statNames: StatNamesStore.getStatNamesState()
      });
    },
    onStatNameValueChange: function() {
      debugger;
      this.setState({
        value: event.target.value
      });
    },
    render: function() {
      var start = this.state.startDate.format('YYYY-MM-DD h:mm:ss a');
      var end = this.state.endDate.format('YYYY-MM-DD h:mm:ss a');
      var label = start + ' - ' + end;
      if (start === end) {
        label = start;
      }

      var dateRangePicker = function () {
        return (
          <BS.Col xs={8} md={4}>
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
      }.bind(this);

      var statOptions = function () {
        return this.state.statNames.map(
          function (name, index) {
            return (
              <option value={name} key={index}>{name}</option>
            )
          });
      }.bind(this);

      var statNames = function () {
        return (
          <BS.Col xs={8} md={4}>
            <BS.Input type="select" label='Stat' onChange={this.onStatNameValueChange} defaultValue={this.state.value}>
              {statOptions()}
            </BS.Input>
          </BS.Col>
        )
      }.bind(this);

      var graphComposer = function() {
        return (
        <BS.Grid>
          <BS.Row className="show-grid">
            { this.state.statNames !== null ? statNames() : null }
            { this.state.statNames !== null ? dateRangePicker() : null }
          </BS.Row>
        </BS.Grid>
        )
      }.bind(this);

      var graphItemsOptions = {
        shards: this.state.shards,
        statName: this.state.value,
        startDate: this.state.startDate,
        endDate: this.state.endDate
      };

      return (
        <div classNameName="stats-container">
          { this.state.statNames !== null ? graphComposer() : null }
          { this.state.statNames !== null ? <GraphItems options={graphItemsOptions} /> : null }
        </div>
      );
    }
});

var InstanceName = React.createClass({
  getInitialState: function() {
    return {
      instanceName : APIUtils.instanceName
    }
  },
  render: function() {
    return (
      <div className="rs-detail-header-title">{ this.state.instanceName }</div>
    );
  }
});

React.render(
  <InstanceName />,
  document.getElementById('instance-name')
);

React.render(
  <Stats />,
  document.getElementById('stats')
);

Actions.getShards();
Actions.getStatNames();
