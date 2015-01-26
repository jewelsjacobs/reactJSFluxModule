/** @jsx React.DOM */
'use strict';
/**
 * The application component. This is the top-level component.
 */
var React = require('react/addons');
var Actions = require('../actions/ViewActionCreators.js');
var ReactBootstrapAsyncAutocomplete = require('react-bootstrap-async-autocomplete');
var BS = require('react-bootstrap');
var _ = require('lodash');

var StatsNamesTypeAhead = React.createClass({
  getInitialState: function() {
    /**
     * GraphStore.getGraphState(this.props.replicaset)
     * returns graph data from store
     */
    return {statName: "connections.current"}
  },
  onSelected: function(statName) {
    this.setState({statName: statName});
    Actions.getStatName("mongodb." + statName);
  },
  searchRequested : function(key, cb) {
    setTimeout(function() { //Emulate async
      var results = [];
      _.forEach(this.props.statsNames, function(statsName){
        statsName = statsName.replace('mongodb.', '');
        if (statsName.indexOf(key) > -1) {
          results.push(statsName);
        }
      })
      cb(results);
    }.bind(this), 1);
  },
  render: function() {
    return (
    <BS.Col xs={6} md={4}>
      <label>Chosen Stat: {this.state.statName}</label>
      <ReactBootstrapAsyncAutocomplete
        type="text"
        placeholder="i.e. connections.current"
        onSearch={this.searchRequested}
        onItemSelect={this.onSelected}
        groupClassName="group-class"
        wrapperClassName="wrapper-class"
        labelClassName="label-class"
      />
    </BS.Col>
    );
  }
});

module.exports = StatsNamesTypeAhead;
