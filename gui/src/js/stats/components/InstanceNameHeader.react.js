var React = require('react');
var APIUtils = require('../../common/utils/APIUtils.js');

/**
 * @author Julia Jacobs
 * @version 1.0.0
 * @description Just takes instance name variable and puts it in header.
 * @module components/instancename
 * @type {*|Function}
 */

var InstanceName = React.createClass({
  getInitialState: function() {
     return {
       instanceName : APIUtils.instanceName
     }
  },
  render: function() {
    return (
      <div className="rs-detail-header-title">{ this.state.instanceName }</div>
    );
  }
});

module.exports = InstanceName;
