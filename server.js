/* Create Express application */
var express = require("express");
var app = express();
var morgan  = require('morgan');
var errorhandler = require('errorhandler');
//var methodOverride = require('method-override');
//var bodyParser = require('body-parser');
var routingProxy = require('http-proxy').RoutingProxy();

/* Configure a simple logger and an error handler. */
app.use(morgan('combined'));
app.use(errorhandler());

var apiPath = 1.0,
	apiHost = my.host.com,
	apiPort = 8080;

function apiProxy(pattern, host, port) {
  return function(req, res, next) {
    if (req.url.match(pattern)) {
      routingProxy.proxyRequest(req, res, {host: host, port: port});
    } else {
      next();
    }
  }
}

// API proxy middleware
app.use(apiProxy(new RegExp('\/' + apiPath + '\/.*'), apiHost, apiPort));

// Static content middleware
//app.use(methodOverride());
//app.use(bodyParser());
//app.use(express.static(__dirname));
//app.use(app.router);

app.listen(3000);
