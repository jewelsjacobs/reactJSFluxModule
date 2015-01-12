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
var AuthStore = require('./stats/stores/Auth.js');

function getStateFromStores() {
  return {
    shards: BootstrapStore.getShards(),
    api_url: BootstrapStore.getApiUrls(),
    instance: BootstrapStore.getInstance(),
    auth_headers: AuthStore.getAuthHeaders()
  };
}

var Stats = React.createClass({
    getInitialState: function() {
      return getStateFromStores();
    },
    componentDidMount: function() {
      BootstrapStore.addChangeListener(this._onChange);
      AuthStore.addChangeListener(this._onChange);
    },
    componentWillUnmount: function() {
      BootstrapStore.removeChangeListener(this._onChange);
      AuthStore.removeChangeListener(this._onChange);
    },
    render: function() {
        return (
          <div classNameName="stats-container">
            <GraphComposer />
            <GraphItems />
          </div>
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
  <Stats />,
  document.getElementById('stats')
);
