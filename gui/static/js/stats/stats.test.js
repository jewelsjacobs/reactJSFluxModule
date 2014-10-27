
//
// Auth Service Tests
//

describe("AuthService", function () {

	var AuthService, httpBackend;

	it("should respond with a user and token", function () {
		var data = {"user": "test_user", "api_token": "test_token"}
		httpBackend.expect("GET", "/api_token").respond(data);

		AuthService.getAuthHeaders().then(function (data) {
			expect(data["X-Auth-Account"]).toEqual("test_user");
			expect(data["X-Auth-Token"]).toEqual("test_token");
		});

		httpBackend.flush();
	});

    beforeEach(function() {
		angular.mock.module('statsGraphApp');

		inject(function($httpBackend, _AuthService_) {
			httpBackend = $httpBackend;
			AuthService = _AuthService_;
		});
  	});

    afterEach(function() {
		httpBackend.verifyNoOutstandingExpectation();
		httpBackend.verifyNoOutstandingRequest();
    });
});

//
// Stats Service Tests
//

describe("StatsService", function () {
	var StatsService, httpBackend, app;

	var auth_data = {"user": "test_user", "api_token": "test_token"};

	var shard_data = {
		"data": [{
			"replset": [
				"test_host:0000"
			]
		}]
	};

	var stats_data = {
	    "type": "gauge",
	    "data": [
	        [1413421980.0, 0]
	    ],
	    "name": "mongodb.opcounters.query",
	    "references": [],
	    "description": "mongodb.opcounters.query"
	}

	it("should return the set of shards for an instance", function () {
		var apiEndpoint = "http://test.com/v2/instance/test_instance/replicaset";
		httpBackend.expect("GET", "/api_token").respond(auth_data);
		httpBackend.expect("GET", apiEndpoint).respond(shard_data);

		StatsService.getShardsAndHosts("test_instance").then(function (data) {
			expect(data.hasOwnProperty("replset")).toBe(true);
			expect(data["replset"]).toContain("test_host:0000");
		});

		httpBackend.flush();
	});

	it("should return the data for a host on a shard", function () {
		var apiEndpoint = "http://test.com/v2/instance/test_instance/host/test_host:0000/stats/mongodb.opcounters.query?period=18000&granularity=minute";
		httpBackend.expect("GET", "/api_token").respond(auth_data);
		httpBackend.expect("GET", apiEndpoint).respond(stats_data);

		var promise = StatsService.getStatForHostInPeriod(
			"test_instance",
			"test_host:0000",
			"mongodb.opcounters.query",
			300,
			"minute"
		);

		promise.then(function (data) {
			expect(data.type).toBe("gauge");
			expect(data.name).toBe("mongodb.opcounters.query")
		});

		httpBackend.flush();
	});

    beforeEach(function() {
		angular.mock.module('statsGraphApp', {
			apiUrl: "http://test.com"
		});

		inject(function($httpBackend, _StatsService_) {
			httpBackend = $httpBackend;
			StatsService = _StatsService_;
		});
  	});

    afterEach(function() {
		httpBackend.verifyNoOutstandingExpectation();
		httpBackend.verifyNoOutstandingRequest();
    });
});

//
// Stats Page Controller test
//

describe("StatsPageCtrl", function () {
    var scope, createDeferred, StatsService;

    it("should have information about the shards", function () {
        expect(scope.shards).toEqual(shardData);
    });

    it("should have a list of stat names", function () {
        expect(scope.statNames).toEqual(statNames);
    });

    it("should have a defined stat name", function () {
        expect(scope.statName).toEqual(statNames[0]);
    });

    var statNames = [
        "mongodb.opcounters.query"
    ];

	var shardData = {
		"data": [{
			"replset": [
				"test_host:0000"
			]
		}]
	};

	var statsData = {
	    "type": "gauge",
	    "data": [
	        [1413421980.0, 0]
	    ],
	    "name": "mongodb.opcounters.query",
	    "references": [],
	    "description": "mongodb.opcounters.query"
	}

    beforeEach(function() {
		angular.mock.module('statsGraphApp', {
			apiUrl: "http://test.com",
            instanceName: "test_instance"
		});

        inject(function ($q) {
            createDeferred = function (data) {
        		var deferred = $q.defer();
                deferred.resolve(data);
                return deferred.promise;
            };
        });

        StatsService = {
    		getShardsAndHosts: function () { return createDeferred(shardData); },
    		getStatForHostInPeriod: function () { return createDeferred(statsData); },
            getStatNames: function () { return createDeferred(statNames); }
        };

        inject(function ($controller, $rootScope, instanceName) {
            scope = $rootScope.$new();
            $controller('StatsPageCtrl', {$scope: scope, StatsService: StatsService, instanceName: instanceName});
            scope.$digest();
        });
  	});
});
