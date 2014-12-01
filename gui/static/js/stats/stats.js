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

	var getShardsAndHosts = function (instanceName) {
		var url = String.format("{0}/v2/instance/{1}/replicaset", apiUrl, instanceName);

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

	var getStatForHostInPeriod = function (instanceName, statName, shardHosts, period, granularity) {

		var url = String.format("{0}/v2/graph", apiUrl);

        var graph_data = {
            "stats": [],
            "granularity": granularity,
            "period": period
        };

        for (var i = 0; i < shardHosts.length; i++) {
            var host = shardHosts[i];

            graph_data['stats'].push({
                "instance": instanceName,
                "host": host,
                "name": statName
            });
        };

        console.log(graph_data);

		var request = AuthService.getAuthHeaders().then(function (headers) {
			return $http.post(url, graph_data, {headers: headers});
		});

		var deferred = $q.defer();

		var success = function (response) {
            var stat_info = [];

            for (var i = 0; i < response.data.stats.length; i++) {
                var stat = response.data.stats[i];
                stat_info.push({
                    key: stat.host_name,
                    values: stat.data
                });
            }

			deferred.resolve(stat_info);
		};

		var failure = function (result) {
			deferred.reject(result);
		};

		request.then(success, failure);
		return deferred.promise;
	};

    //
    // getStatNames
    // Grab the names of the stats that we'll use to show in the dropdown. Right now this returns the
    // list of names for the first host in the last shard.  We should eventually change the API to return a union
    // of all of the stat options for all of the hosts on the instance.
    //

    var getStatNames = function (instanceName, shards) {
        // we'll need to grab a host, given the shards structure here.
        var host = null;
        angular.forEach(shards, function (value) {
            if (value.length == 0) {
                return;
            }

            host = value[0];
        });

        if (host === null) {
            return []
        };

        // we have a host now, lets get it's options
		var url = String.format("{0}/v2/instance/{1}/host/{2}/stats/available", apiUrl, instanceName, host);

        var request = AuthService.getAuthHeaders().then(function (headers) {
			return $http.get(url, {headers: headers});
		});

		var deferred = $q.defer();

        var success = function (result) {
            deferred.resolve(result.data['names']);
        };

        var failure = function (result) {
            deferred.reject(result);
        };

        request.then(success, failure);
        return deferred.promise;
    };

	// stuff to expose
	var StatsService = {
		getShardsAndHosts: getShardsAndHosts,
		getStatForHostInPeriod: getStatForHostInPeriod,
        getStatNames: getStatNames
	};

	return StatsService;
}]);

//
// StatsPageCtrl
// Owner of the page-wide scope.
//

app.controller("StatsPageCtrl", ["$scope", "StatsService", "instanceName", function ($scope, StatsService, instanceName) {
	$scope.statName = "";
	$scope.granularity = "hour";
	$scope.period = 24;

	// grab the shards for this instance
	StatsService.getShardsAndHosts(instanceName).then(function (data) {
		$scope.shards = data;

        StatsService.getStatNames(instanceName, $scope.shards).then(function (data) {
            $scope.statNames = data;

            if (data.length > 0) {
                $scope.statName = data[0];
            }
        });
	});
}]);

//
// StatsGraphCtrl
// Owner of the scope for a single graph.
//

app.controller("StatsGraphCtrl", ["$scope", "$interval", "StatsService", "instanceName", function ($scope, $interval, StatsService, instanceName) {

    // load the data into the graph
	var updateGraph = function () {
		var statName = $scope.statName;
        var shardHosts = $scope.hosts;
		var period = $scope.period;
		var granularity = $scope.granularity;

        // don't do anything no stat is selected
        if (statName === '') {
            return;
        }

		var success = function (result) {
            $scope.error = false;
            $scope.data = result;
        };

		var error = function (result) {
			$scope.error = true;
		};

		StatsService.getStatForHostInPeriod(instanceName, statName, shardHosts, period, granularity).then(success, error);
	}

    //
    // Update the graph, and schedule the auto updates
    //

    updateGraph();
    $interval(updateGraph, 1000 * 30);

    //
    // watch for changes
    //

    angular.forEach(['statName', 'period', 'granularity'], function (item) {
        $scope.$watch(item, function (newValue, oldValue) {
            // only rerender on changes
            if (newValue == oldValue) {
                return;
            }

            updateGraph();
        });
    });

    //
    // Graph helper methods
    //

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
}]);
