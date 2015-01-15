/** @jsx React.DOM */
'use strict';
/**
 * The application component. This is the top-level component.
 */
var React = require('react');
var BS = require('react-bootstrap');
var Actions = require('../actions/ViewActionCreators.js');
//var GraphStore = require('../stores/Graph.js');

var StatNames = React.createClass({
  getInitialState: function() {
    return {value: 'mongodb.opcounters.query'};
  },
  //componentDidMount: function() {
  //  GraphStore.addChangeListener(this._onChange);
  //},
  //componentWillUnmount: function() {
  //  GraphStore.removeChangeListener(this._onChange);
  //},
  _onChange: function(event) {
    this.setState({value: event.target.value});
    Actions.getGraphParams({ statName: this.state.value });
  },
  render: function() {
    var options = this.props.names.map(
      function (name, index) {
        return (
          <option value={name} key={index}>{name}</option>
        )
      });
    return (
      <BS.Col xs={8} md={4}>
        <BS.Input type="select" label='Stat' onChange={this._onChange} defaultValue={this.state.value}>
          {options}
        </BS.Input>
      </BS.Col>
    );
  }
});

module.exports = StatNames;
