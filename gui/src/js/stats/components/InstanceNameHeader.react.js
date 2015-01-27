var React = require('react');
var APIUtils = require('../../common/utils/APIUtils.js');

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
