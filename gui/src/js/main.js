/** @jsx React.DOM */
'use strict';
/**
 * The application component. This is the top-level component.
 */
var React = require('react');
var GraphComposer = require('./stats/components/GraphComposer.react.js');
var Actions = require('./stats/actions/ActionCreators.js');
var GraphItems = require('./stats/components/GraphItems.react.js');
var BootstrapStore = require('./stats/stores/Bootstrap.js');

function getStateFromStores() {
  return {
    shardsAndReplicaSets: BootstrapStore.getShardsAndReplicasets(),
    instanceName : BootstrapStore.getInstance()
  };
};

var Stats = React.createClass({
    render: function() {
        return (
          <div classNameName="stats-container">
            <GraphComposer />
            <GraphItems />
          </div>
        );
    }
});

var InstanceName = React.createClass({
  getInitialState: function() {
   return getStateFromStores();
  },
  componentDidMount: function() {
   BootstrapStore.addChangeListener(this._onChange);
  },
  componentWillUnmount: function() {
   BootstrapStore.removeChangeListener(this._onChange);
  },
  render: function() {
    return (
    <div className="rs-detail-header-title">{ this.state.instanceName }</div>
    );
  },
  /**
   * Event handler for 'change' events coming from the stores
   */
  _onChange: function() {
    this.setState(getStateFromStores());
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


