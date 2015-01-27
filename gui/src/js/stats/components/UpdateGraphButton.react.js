var React = require('react');
var Actions = require('../actions/ViewActionCreators.js');
var BS = require('react-bootstrap');

var UpdateGraphButton = React.createClass({
  getInitialState: function() {
    return {update: false};
  },
  updateGraph: function() {
    this.setState({update: !this.state.update});
    Actions.updateGraph(!this.state.update);
  },
  render: function() {
    var invisibleTextForSpacingHack = {
      color: 'white'
    };

    return (
      <BS.Col xs={6} md={4}>
        <label style={invisibleTextForSpacingHack}>Spacing Hack</label>
        <BS.ButtonToolbar>
          <BS.Button bsStyle="primary" onClick={this.updateGraph}>Update Graph</BS.Button>
        </BS.ButtonToolbar>
      </BS.Col>
    );
  }
});

module.exports = UpdateGraphButton;
