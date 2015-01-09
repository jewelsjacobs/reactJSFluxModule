/** @jsx React.DOM */
'use strict';
/**
 * The application component. This is the top-level component.
 */
var React = require('react');
var Actions = require('../actions/ActionCreators');
var StatNames = require('./StatNames.react.js');
var Range = require('./Range.react.js');
var GraphItems = require('./GraphItems.react.js');

var GraphComposer = React.createclassName({


  render: function() {
    return (
      <div>
        <ul className="rs-detail-list">
          <StatNames />
          <li className="rs-detail-item">
            <Range />
          </li>
        </ul>
        <GraphItems />
      </div>
    );
  }
});

module.exports = GraphComposer;
