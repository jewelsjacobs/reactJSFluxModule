var app = angular.module("statsGraphApp", ['nvd3', 'ngQuickDate']);

//
// config values
//

app.value("tokenRoute", "/api_token");
app.value("instanceName", null);
app.value("apiUrl", null);


// configure our date pickers with icons from FontAwesome
app.config(function(ngQuickDateDefaultsProvider) {
    return ngQuickDateDefaultsProvider.set({
    closeButtonHtml: "<i class='fa fa-times'></i>",
    buttonIconHtml: "<i class='fa fa-calendar'></i>",
    nextLinkHtml: "<i class='fa fa-chevron-right'></i>",
    prevLinkHtml: "<i class='fa fa-chevron-left'></i>"
  });
});

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
    // getStatForHosts
    // internal method to get a stat for a set of hosts, used by getStatForHostsInPeriod() and
    // getStatForHostsBetweenDates().
    //

    var getStatForHosts = function (instanceName, statName, shardHosts, graphData) {
        graphData['stats'] = [];

        for (var i = 0; i < shardHosts.length; i++) {
            var host = shardHosts[i];

            graphData['stats'].push({
                "instance": instanceName,
                "host": host,
                "name": statName
            });
        };

		var url = String.format("{0}/v2/graph", apiUrl);

		var request = AuthService.getAuthHeaders().then(function (headers) {
			return $http.post(url, graphData, {headers: headers});
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
	// getStatForHostInPeriod
	// Get the specified stats (at the specified granularity) for the host in the period.
	//

	var getStatForHostsInPeriod = function (instanceName, statName, shardHosts, period, granularity) {
        var graphData = {
            "granularity": granularity,
            "period": parseInt(period, 10)
        };

        return getStatForHosts(instanceName, statName, shardHosts, graphData);
	};

	//
	// getStatForHostsBetweenDates
	// Get the specified stats (at the specified granularity) for the host in the period.
	//

	var getStatForHostsBetweenDates = function (instanceName, statName, shardHosts, fromDate, toDate, granularity) {
        var graphData = {
            "granularity": granularity,
            "start_time": moment(fromDate).utc().format("YYYY-MM-DD HH:mm:ss"),
            "end_time": moment(toDate).utc().format("YYYY-MM-DD HH:mm:ss")
        };

        return getStatForHosts(instanceName, statName, shardHosts, graphData);
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


	// stuff to expose
	var StatsService = {
		getShardsAndHosts: getShardsAndHosts,
		getStatForHostsInPeriod: getStatForHostsInPeriod,
        getStatForHostsBetweenDates: getStatForHostsBetweenDates,
        getStatNames: getStatNames
	};

	return StatsService;
}]);

//
// StatsPageCtrl
// Owner of the page-wide scope.
//

app.controller("StatsPageCtrl", ["$scope", "StatsService", "instanceName", function ($scope, StatsService, instanceName) {
    $scope.granularity = "hours";
    $scope.mode = 'for the last';
    $scope.period = 24;
    $scope.statName = "";
    $scope.fromDate = moment().subtract(1, 'days').format();
    $scope.toDate = moment().format();

    // change the options shown based on the ui mode
    $scope.$watch('mode', function (newValue, oldValue) {
        if (newValue == oldValue) {
            return;
        }

        if (newValue == 'between'){
            angular.element("#between").show();
            angular.element("#last").hide();
        } else {
            angular.element("#between").hide();
            angular.element("#last").show();
        }
    });

    // executed when the update button is clicked.  $broadcast will notify all of the child
    // scopes about the event that happened.
    $scope.onUpdate = function () {
        $scope.$broadcast('updateClicked');
    };

	// grab the shards for this instance
	StatsService.getShardsAndHosts(instanceName).then(function (data) {
		$scope.shards = data;

        StatsService.getStatNames(instanceName, $scope.shards).then(function (data) {
            $scope.statNames = data;
            angular.element("#load-stat-names").hide();

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

    // graph options
    $scope.options = {
        "chart": {
            "type": "lineChart",
            "height": 300,
            "margin": {
                "top": 20,
                "right": 20,
                "bottom": 20,
                "left": 50
            },
            "useInteractiveGuideline": true,
            "transitionDuration": 250,
            "x": function (data) {
                return data[0];
            },
            "xAxis": {
                "staggerLabels": true,
                "tickFormat": function (data) {
                    return d3.time.format('%m/%d/%y %X')(moment.unix(data).toDate());
                }
            },
            "y": function (data) {
                return data[1];
            }
        }
    };

    // graph data
    $scope.data = undefined;

    // load the data into the graph
	var updateGraph = function () {
        var fromDate = $scope.fromDate;
        var period = $scope.period;
        var shardHosts = $scope.hosts;
        var shardName = $scope.shardName;
        var statName = $scope.statName;
        var toDate = $scope.toDate;

        // granularities in the form have an 's' appended for niceness, this strips it.
        var granularity = $scope.granularity.slice(0, - 1);

        // don't do anything if no stat is selected
        if (statName === '') {
            return;
        }

        angular.element("#load-" + shardName).show();

        var success = function (result) {
            if (result[0]['values'].length === 0) {
                $scope.data = [];
            } else {
                $scope.data = result;
            }

            angular.element("#load-" + shardName).hide();
            $scope.error = false;
        };

        var error = function (result) {
            angular.element("#load-" + shardName).hide();
            $scope.error = true;
        };

        if ($scope.mode === 'between') {
            StatsService.getStatForHostsBetweenDates(instanceName, statName, shardHosts, fromDate, toDate, granularity).then(success, error);
        } else {
            StatsService.getStatForHostsInPeriod(instanceName, statName, shardHosts, period, granularity).then(success, error);
        }
    };

    updateGraph();

    // Make sure that we don't repeatedly call the update to the graph multiple times while
    // a user is editing the form. The time to wait before executing the function is in ms.
    var doUpdateGraph = updateGraph.debounce(300);

    // Schedule updates to the graph for every 2 seconds
    $interval(doUpdateGraph, 1000 * 60 * 2);

    // on update click, do the graph update
    $scope.$on('updateClicked', function () {
        doUpdateGraph();
    });
}]);
