var app = angular.module("statsGraphApp", ['nvd3ChartDirectives']);

//
// config values
//

app.value("tokenRoute", "/api_token");
app.value("instanceName", null);
app.value("apiUrl", null);

//
// String.format
// Implement a subset of the common .format() functions
//

String.format = String.format || function (string) {
	var output = string;

	for (var i = 1; i < arguments.length; i++) {
		var regEx = new RegExp("\\{" + (i - 1) + "\\}", "gm");
		output = output.replace(regEx, arguments[i]);
	}

	return output;
}

//
// AuthService
// Abstraction layer around doing authentication type things.
//

app.factory("AuthService", ['$q', '$http', 'tokenRoute', function ($q, $http, tokenRoute) {

	// private credential cache
	var authHeaders = null;

	//
	// getAuthHeaders()
	// Return the current auth headers for the user.
	//

	var getAuthHeaders = function () {
		var deferred = $q.defer();

		// used the cached versions of the credentials, if they exist
		if (authHeaders !== null) {
			deferred.resolve(authHeaders);
			return deferred.promise;
		}

		var request = $http.get(tokenRoute);

		// on success, give back the data
		request.success(function(data, status, headers, config) {
			authHeaders = {"X-Auth-Account": data['user'], "X-Auth-Token": data['api_token']};
			deferred.resolve(authHeaders);
		})

		// on failure, die here
		request.error(function(data, status, headers, config) {
			deferred.reject(status);
		});

		return deferred.promise;
	};

	// stuff to expose
	var AuthService = {
		getAuthHeaders: getAuthHeaders
	}

	return AuthService;
}]);

//
// StatsService
// Service to provide Stats 2.0 information.
//

app.factory("StatsService", ['$q', '$http', 'apiUrl', 'AuthService', function ($q, $http, apiUrl, AuthService) {

	//
	// getShardsAndHosts
	// Get the shards and hosts for a given instance.
	//

	var getShardsAndHosts = function (instance_name) {
		var url = String.format("{0}/v2/instance/{1}/replicaset", apiUrl, instance_name);

		var request = AuthService.getAuthHeaders().then(function (headers) {
			return $http.get(url, {headers: headers});
		});

		var deferred = $q.defer();

		// request is a default promise, not the $http one, so we'll need to
		// use the standard .then() instead of .success() or .error().

		var success = function (response) {
			var output = {};

			for (var i = 0; i < response.data['data'].length; i++) {
				var item = response.data['data'][i];
				angular.forEach(item, function (value, key) {
					output[key] = value;
				});
			}

			deferred.resolve(output);
		};

		var failure = function (result) {
			deferred.reject(result);
		};

		request.then(success, failure);
		return deferred.promise;
	};

	//
	// getStatForHostInPeriod
	// Get the specified stats (at the specified granularity) for the host in the period.
	//

	var getStatForHostInPeriod = function (instance_name, host_name, stat_name, period, granularity) {
		var url = String.format(
			"{0}/v2/instance/{1}/host/{2}/stats/{3}?period={4}&granularity={5}",
			apiUrl,
			instance_name,
			host_name,
			stat_name,
			period,
			granularity
		);

		var request = AuthService.getAuthHeaders().then(function (headers) {
			return $http.get(url, {headers: headers});
		});

		var deferred = $q.defer();

		var success = function (response) {
			deferred.resolve(response.data);
		};

		var failure = function (result) {
			deferred.reject(result);
		};

		request.then(success, failure);
		return deferred.promise;
	}

	// stuff to expose
	var StatsService = {
		getShardsAndHosts: getShardsAndHosts,
		getStatForHostInPeriod: getStatForHostInPeriod
	};

	return StatsService;
}]);

//
// StatsPageCtrl
// Owner of the page-wide scope.
//

app.controller("StatsPageCtrl", ["$scope", "StatsService", "instanceName", function ($scope, StatsService, instanceName) {

	// TODO: these should be dynamic
	$scope.statName = "mongodb.opcounters.query";
	$scope.period = 300; // seconds
	$scope.granularity = "minute";

	// grab the shards for this instance
	StatsService.getShardsAndHosts(instanceName).then(function (data) {
		$scope.shards = data;
	});
}]);

//
// StatsGraphCtrl
// Owner of the scope for a single graph.
//

app.controller("StatsGraphCtrl", ["$scope", "StatsService", "instanceName", function ($scope, StatsService, instanceName) {
	var getStats = function () {
		var host = $scope.host;
		var statName = $scope.statName;
		var period = $scope.period;
		var granularity = $scope.granularity;

		var success = function (data) {
			$scope.error = false;
			$scope.data = data;
		};

		var error = function (result) {
			$scope.error = true;
		};

		StatsService.getStatForHostInPeriod(instanceName, host, statName, period, granularity).then(success, error);
	}

	getStats();
}]);

//
// //
// // controller
// //
//
// app.controller("OpcounterCtrl", function($scope, $http, apiUrl) {
// 	function fetchApiData() {
// 		var insertQueryData = [];
// 		var commandGetmoreData = [];
// 		var deleteUpdateData = [];
//
// 		$http.get(apiUrl + "serverStatus/opcounters.insert").
// 		success(function(data, status, headers, config) {
// 			insertQueryData[0] = data;
// 		});
//
// 		$http.get(apiUrl + "serverStatus/opcounters.query").
// 		success(function(data, status, headers, config) {
// 			insertQueryData[1] = data;
// 			$scope.insertQueryData = insertQueryData;
// 		});
//
// 		$http.get(apiUrl + "serverStatus/opcounters.command").
// 		success(function(data, status, headers, config) {
// 			commandGetmoreData[0] = data;
// 		});
//
// 		$http.get(apiUrl + "serverStatus/opcounters.getmore").
// 		success(function(data, status, headers, config) {
// 			commandGetmoreData[1] = data;
// 			$scope.commandGetmoreData = commandGetmoreData;
// 		});
//
// 		$http.get(apiUrl + "serverStatus/opcounters.delete").
// 		success(function(data, status, headers, config) {
// 			deleteUpdateData[0] = data;
// 		});
//
// 		$http.get(apiUrl + "serverStatus/opcounters.update").
// 		success(function(data, status, headers, config) {
// 			deleteUpdateData[1] = data;
// 			$scope.deleteUpdateData = deleteUpdateData;
// 		});
// 	}
//
// 	fetchApiData();
//
// 	$scope.xFunction = function() {
// 		return function(data) {
// 			return data[0];
// 		}
// 	};
//
// 	$scope.yFunction = function() {
// 		return function(data) {
// 			return data[1];
// 		}
// 	};
//
// 	$scope.legendDetails = {};
//
// 	$scope.toolTipContentFunction = function() {
// 		return function(key, x, y, event, graph) {
// 			return key + ": " + y + " events at " + x;
// 		}
// 	};
//
// 	$scope.xAxisTickFormatFunction = function() {
// 		return function(data) {
// 			return d3.time.format('%m/%d/%y %X')(moment.unix(data).toDate());
// 		}
// 	};
// });
