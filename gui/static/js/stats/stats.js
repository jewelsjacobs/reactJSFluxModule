var app = angular.module("statsGraphApp", ['nvd3ChartDirectives']);

app.config(function($httpProvider) {
	$httpProvider.interceptors.push(interceptor);
});

app.constant("baseUrl", "http://127.0.0.1:5000/");

var interceptor = function($q, $location) {
	return {
		response: function(result) {
			result.data = {
				"key": result.data.name,
				"values": result.data.data,
				"description": result.data.description,
				"references": result.data.references
			};
			return result;
		}
	}
};


app.controller("OpcounterCtrl", function($scope, $http, baseUrl) {
	function fetchApiData() {
		var insertQueryData = [];
		var commandGetmoreData = [];
		var deleteUpdateData = [];

		$http.get(baseUrl + "serverStatus/opcounters.insert").
		success(function(data, status, headers, config) {
			insertQueryData[0] = data;
		});

		$http.get(baseUrl + "serverStatus/opcounters.query").
		success(function(data, status, headers, config) {
			insertQueryData[1] = data;
			$scope.insertQueryData = insertQueryData;
		});

		$http.get(baseUrl + "serverStatus/opcounters.command").
		success(function(data, status, headers, config) {
			commandGetmoreData[0] = data;
		});

		$http.get(baseUrl + "serverStatus/opcounters.getmore").
		success(function(data, status, headers, config) {
			commandGetmoreData[1] = data;
			$scope.commandGetmoreData = commandGetmoreData;
		});

		$http.get(baseUrl + "serverStatus/opcounters.delete").
		success(function(data, status, headers, config) {
			deleteUpdateData[0] = data;
		});

		$http.get(baseUrl + "serverStatus/opcounters.update").
		success(function(data, status, headers, config) {
			deleteUpdateData[1] = data;
			$scope.deleteUpdateData = deleteUpdateData;
		});
	}

	fetchApiData();

	$scope.xFunction = function() {
		return function(data) {
			return data[0];
		}
	};

	$scope.yFunction = function() {
		return function(data) {
			return data[1];
		}
	};

	$scope.legendDetails = {};

	$scope.toolTipContentFunction = function() {
		return function(key, x, y, event, graph) {
			return key + ": " + y + " events at " + x;
		}
	};

	$scope.xAxisTickFormatFunction = function() {
		return function(data) {
			return d3.time.format('%m/%d/%y %X')(moment.unix(data).toDate());
		}
	};
});
