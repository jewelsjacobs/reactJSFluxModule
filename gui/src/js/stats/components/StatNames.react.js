/** @jsx React.DOM */
'use strict';
/**
 * The application component. This is the top-level component.
 */
var React = require('react');
var MockDataStore = require('../stores/MockData.js');
var BS = require('react-bootstrap');

var StatNames = React.createClass({
  getInitialState: function() {
    return {
      names : MockDataStore.statsNames.names,
      value : "mongodb.opcounters.query"
    };
  },
  componentDidMount: function() {
    this.setState(
      { names: MockDataStore.statsNames.names }
    );
  },
  _onChange: function(value) {
    this.setState(
      { value: value }
    );
  },
  render: function() {
    var options = this.state.names.map(function(name, index){
      return (
        <option value={name} key={index}>{name}</option>
      )
    })
    return (

          <BS.Col md={3}>
            <BS.Input type="select" label='Stat' defaultValue="mongodb.opcounters.query">
              {options}
            </BS.Input>
          </BS.Col>
    );
  }
});

module.exports = StatNames;
