/** @jsx React.DOM */
'use strict';
/**
 * The application component. This is the top-level component.
 */
var React = require('react');
var BS = require('react-bootstrap');
var Actions = require('../actions/ActionCreators.js');
var StatNamesStore = require('../stores/StatNames.js');

var StatNames = React.createClass({
  getInitialState: function() {
    return StatNamesStore.getStatNamesState()
  },
  componentDidMount: function() {
    StatNamesStore.addChangeListener(this._onChange);
  },
  componentWillUnmount: function() {
    StatNamesStore.removeChangeListener(this._onChange);
  },
  _onChange: function() {
    this.setState(StatNamesStore.getStatNamesState());
  },
  render: function() {
    var options = "";
    if (this.state !== null) {
      var options = this.state.names.map(
        function (name, index) {
          return (
            <option value={name} key={index}>{name}</option>
          )
        });
    }
    return (
      <BS.Col xs={8} md={4}>
        <BS.Input type="select" label='Stat' defaultValue="mongodb.opcounters.query">
          {options}
        </BS.Input>
      </BS.Col>
    );
  }
});

module.exports = StatNames;
