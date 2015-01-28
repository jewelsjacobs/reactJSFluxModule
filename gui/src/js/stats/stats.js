var React = require('react');
var Actions = require('./actions/ViewActionCreators.js');
var GraphItems = require('./components/GraphItems.react.js');
var BS = require('react-bootstrap');
var StatsStore = require('./stores/Stats.js');
var LoaderHelpers = require('./components/helpers/LoaderHelpers.js');
var Loader = require('react-loader');
var StatsNamesTypeAhead = require('./components/StatsNamesTypeAhead.react.js');
var DateTimePicker = require('./components/DateTimePicker.react.js');
var InstanceNameHeader = require('./components/InstanceNameHeader.react.js');
var UpdateGraphButton = require('./components/UpdateGraphButton.react.js');
var _ = require('lodash');

/**
 * @author Julia Jacobs
 * @version 1.0.0
 * @description Component for Stats module
 * @module stats
 * @type {*|Function}
 */

var Stats = React.createClass({
    getInitialState: function() {
      return {
        stats: StatsStore.getStatsState(),
        isLoaded: StatsStore.isLoading()
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
        stats: StatsStore.getStatsState(),
        isLoaded: StatsStore.isLoading()
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
            <Loader loaded={this.state.isLoaded} options={LoaderHelpers.spinnerOpts}>
            { dataIsLoaded ? graphComposer() : null }
            { dataIsLoaded ? <GraphItems shards={this.state.stats.shards} />  : null }
            </Loader>
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
