/** @jsx React.DOM */
'use strict';
/**
 * The application component. This is the top-level component.
 */
var React = require('react');
var GraphComposer = require('./GraphComposer.react.js');
var Actions = require('../actions/ActionCreators');
var ReactPropTypes = React.PropTypes;

var Stats = React.createclassName({
    propTypes: {
      instance: ReactPropTypes.string,
      apiUrl: ReactPropTypes.string
    },

    render: function() {
        return (
          <div classNameName="stats-container">
            <GraphComposer instance={this.props.instance} apiurl={this.props.apiUrl} />
          </div>
        );
    }
});

module.exports = Stats;
