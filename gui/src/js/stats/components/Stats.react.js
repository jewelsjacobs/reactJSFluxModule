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
    componentWillMount: function() {
      Actions.getApiUrl(this.props.apiUrl);
      Actions.getInstanceName(this.props.instance);
    },
    render: function() {
        return (
          <div classNameName="stats-container">
            <GraphComposer />
          </div>
        );
    }
});

module.exports = Stats;
