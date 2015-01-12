/** @jsx React.DOM */
'use strict';
/**
 * The application component. This is the top-level component.
 */
var React = require('react');
var GraphComposer = require('./stats/components/GraphComposer.react.js');
var Actions = require('./stats/actions/ActionCreators.js');
var ReactPropTypes = React.PropTypes;
var GraphItems = require('./stats/components/GraphItems.react.js');
var Stats = React.createClass({
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
            <GraphItems />
          </div>
        );
    }
});

React.render(
  <Stats instance={window.instance} apiUrl={window.apiUrl} />,
  document.getElementById('stats')
);
