/** @jsx React.DOM */
'use strict';
/**
 * The application component. This is the top-level component.
 */
var React = require('react');
var BS = require('react-bootstrap');
var DateRangeSelector = require('./DateRangeSelector.react.js');
var StatNames = require('./StatNames.react.js');
var StatNamesStore = require('../stores/StatNames.js');
var Actions = require('../actions/ViewActionCreators.js');

var GraphComposer = React.createClass({
  getInitialState: function() {
    return StatNamesStore.getStatNamesState();
  },
  componentWillMount: function() {
    Actions.getStatNames(this.props.data);
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
    console.log(this.state);
    return (
      <BS.Grid>
        <BS.Row className="show-grid">
            { this.state !== null ? <StatNames names={this.state.names} /> : null }
            { this.state !== null ? <DateRangeSelector /> : null }
        </BS.Row>
      </BS.Grid>
    );
  }
});

module.exports = GraphComposer;
