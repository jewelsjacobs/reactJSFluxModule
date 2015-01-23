/** @jsx React.DOM */
'use strict';
/**
 * The application component. This is the top-level component.
 */
var React = require('react');
var Actions = require('./stats/actions/ViewActionCreators.js');
var GraphItems = require('./stats/components/GraphItems.react.js');
var BS = require('react-bootstrap');
var StatsStore = require('./stats/stores/Stats.js');
var StatsNamesTypeAhead = require('./stats/components/StatsNamesTypeAhead.react.js');
var DateTimePicker = require('./stats/components/DateTimePicker.react.js');
var InstanceNameHeader = require('./stats/components/InstanceNameHeader.react.js');
var UpdateGraphButton = require('./stats/components/UpdateGraphButton.react.js');
var _ = require('lodash');

var Stats = React.createClass({
    getInitialState: function() {
      return {
        stats: StatsStore.getStatsState()
      };
    },
    componentDidMount: function() {
      StatsStore.addChangeListener(this._onChange);
    },
    componentWillUnmount: function() {
      StatsStore.removeChangeListener(this._onChange);
    },
    _onChange: function() {
      this.setState({
        stats: StatsStore.getStatsState()
      });
    },
    render: function() {
      var dataIsLoaded = _.has(this.state, "stats")
                         && !_.isUndefined(this.state.stats)
                         && !_.isEmpty(this.state.stats);

      var graphComposer = function() {
        return (
          <BS.Grid>
            <BS.Row className="show-grid">
              <StatsNamesTypeAhead statsNames={this.state.stats.stat_names} />
              <DateTimePicker />
              <UpdateGraphButton />
            </BS.Row>
          </BS.Grid>
        )
      }.bind(this);

      return (
        <div classNameName="stats-container">
          { dataIsLoaded ? graphComposer() : null }
          { dataIsLoaded ? <GraphItems shards={this.state.stats.shards} />  : null }
        </div>
      );
    }
});

React.render(
  <InstanceNameHeader />,
  document.getElementById('instance-name')
);

React.render(
  <Stats />,
  document.getElementById('stats')
);

Actions.getStats();
