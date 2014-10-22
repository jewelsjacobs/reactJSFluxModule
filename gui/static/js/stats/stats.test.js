
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
		var apiEndpoint = "http://test.com/v2/instance/test_instance/host/test_host:0000/stats/mongodb.opcounters.query?period=300&granularity=minute";
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
