/** @jsx React.DOM */
'use strict';
/**
 * The application component. This is the top-level component.
 */
var React = require('react');
var StatsNamesStore = require('../stores/StatsNames.js');
var BS = require('react-bootstrap');
var Actions = require('../actions/ActionCreators.js');

function getStatsNamesState() {
  return {
    names: StatsNamesStore.getStatNames()
  };
}

var StatNames = React.createClass({
  getInitialState: function() {
    return getStatsNamesState();
  },
  componentDidMount: function() {
    StatsNamesStore.addChangeListener(this._onChange);
  },
  componentWillUnmount: function() {
    StatsNamesStore.removeChangeListener(this._onChange);
  },
  _onChange: function(value) {
    this.setState(
      { value: value }
    );
    Actions.getStatName(value);
  },
  render: function() {
    var options = this.state.names.map(function(name, index){
      return (
        <option value={name} key={index}>{name}</option>
      )
    })
    return (
      <BS.Col xs={8} md={4}>
        <BS.Input type="select" label='Stat' onChange='' defaultValue="mongodb.opcounters.query">
          {options}
        </BS.Input>
      </BS.Col>
    );
  }
});

module.exports = StatNames;
