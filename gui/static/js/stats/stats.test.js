function generateTsData() {
	results = [];
	for (i = 0; i <= 90; i++) {
		results[results.length] = [(Date.now() / 1000) - (86400 * i), Math.floor((Math.random() * 100) + 1)];
	}
	return results;
}

opcountersCommandData = {
	"data": generateTsData(),
	"description": "The average or total number of commands performed per second since the last data point.",
	"name": "opcounters.command",
	"references": [
		"http://docs.mongodb.org/manual/reference/server-status/#server-status-example-opcounters"
	]
};

opcountersQueryData = {
	"data": generateTsData(),
	"description": "The number of queries performed per unit time.",
	"name": "opcounters.query",
	"references": [
		"http://docs.mongodb.org/manual/reference/server-status/#server-status-example-opcounters"
	]
};

opcountersUpdateData = {
	"data": generateTsData(),
	"description": "The number of updates performed per unit time.",
	"name": "opcounters.update",
	"references": [
		"http://docs.mongodb.org/manual/reference/server-status/#server-status-example-opcounters"
	]
};

opcountersDeleteData = {
	"data": generateTsData(),
	"description": "The number of deletes performed per unit time.",
	"name": "opcounters.delete",
	"references": [
		"http://docs.mongodb.org/manual/reference/server-status/#server-status-example-opcounters"
	]
};

opcountersGetmoreData = {
	"data": generateTsData(),
	"description": "The number of times getMore has been called on any cursor per unit time. On a primary, this number can be high even if the query count is low as the secondaries 'getMore' from the primary often as part of replication.",
	"name": "opcounters.getmore",
	"references": [
		"http://docs.mongodb.org/manual/reference/server-status/#server-status-example-opcounters"
	]
};

opcountersInsertData = {
	"data": generateTsData(),
	"description": "The number of inserts performed per unit time.",
	"name": "opcounters.insert",
	"references": [
		"http://docs.mongodb.org/manual/reference/server-status/#server-status-example-opcounters"
	]
};

describe("Controller Test", function() {
	// Arrange
	var mockScope, controller, backend, mockInterval, mockTimeout, mockLog;

	beforeEach(angular.mock.module("statsGraphApp"));

	beforeEach(angular.mock.inject(function($httpBackend) {
		backend = $httpBackend;
		backend.whenGET("http://127.0.0.1:5000/serverStatus/opcounters.command").respond(
			opcountersCommandData
		);

		backend.whenGET("http://127.0.0.1:5000/serverStatus/opcounters.query").respond(
			opcountersQueryData
		);

		backend.whenGET("http://127.0.0.1:5000/serverStatus/opcounters.update").respond(
			opcountersUpdateData
		);

		backend.whenGET("http://127.0.0.1:5000/serverStatus/opcounters.delete").respond(
			opcountersDeleteData
		);

		backend.whenGET("http://127.0.0.1:5000/serverStatus/opcounters.getmore").respond(
			opcountersGetmoreData
		);

		backend.whenGET("http://127.0.0.1:5000/serverStatus/opcounters.insert").respond(
			opcountersInsertData
		);
	}));

	beforeEach(angular.mock.inject(function($controller, $rootScope, $http, $interval, $timeout, $log) {
		mockScope = $rootScope.$new();
		mockInterval = $interval;
		mockTimeout = $timeout;
		mockLog = $log;
		$controller("OpcounterCtrl", {
			$scope: mockScope,
			$http: $http,
			$interval: mockInterval,
			$timeout: mockTimeout,
			$log: mockLog
		});
		backend.flush();
	}));

	// Act and Assess
	it("Creates legendDetails", function() {
		expect(mockScope.legendDetails).toBeDefined();
	});

	it("Makes an Ajax request", function() {
		backend.verifyNoOutstandingExpectation();
	});

	it("Processes API data", function() {
		expect(mockScope.insertQueryData).toBeDefined();
		expect(mockScope.insertQueryData.length).toEqual(2);

		expect(mockScope.commandGetmoreData).toBeDefined();
		expect(mockScope.commandGetmoreData.length).toEqual(2);

		expect(mockScope.deleteUpdateData).toBeDefined();
		expect(mockScope.deleteUpdateData.length).toEqual(2);
	});

	it("Inserts insertQueryData into scope", function() {
		expect(mockScope.insertQueryData[0].key).toEqual("opcounters.insert");
		expect(mockScope.insertQueryData[1].key).toEqual("opcounters.query");
	});

	it("Inserts commandGetmoreData into scope", function() {
		expect(mockScope.commandGetmoreData[0].key).toEqual("opcounters.command");
		expect(mockScope.commandGetmoreData[1].key).toEqual("opcounters.getmore");
	});

	it("Inserts deleteUpdateData into scope", function() {
		expect(mockScope.deleteUpdateData[0].key).toEqual("opcounters.delete");
		expect(mockScope.deleteUpdateData[1].key).toEqual("opcounters.update");
	});

	it("Defines xFunction", function() {
		expect(mockScope.xFunction).toBeDefined();
	});

	it("xFunction returns first item in list", function() {
		expect(mockScope.xFunction()([0, 1])).toBe(0);
	});

	it("Defines yFunction", function() {
		expect(mockScope.yFunction).toBeDefined();
	});

	it("yFunction returns second item in list", function() {
		expect(mockScope.yFunction()([0, 1])).toBe(1);
	});

	it("Defines toolTipContentFunction", function() {
		expect(mockScope.toolTipContentFunction).toBeDefined();
	});

	it("Defines xAxisTickFormatFunction", function() {
		expect(mockScope.xAxisTickFormatFunction).toBeDefined();
	});

	it("xAxisTickFormatFunction returns formatted date", function() {
		expect(mockScope.xAxisTickFormatFunction()(1410159453.0)).toMatch("09/08/14 01:57:33");
	});

	it("toolTipContentFunction returns formatted string", function() {
		expect(mockScope.toolTipContentFunction()("key", "x", "y", {}, "")).toMatch(/key: y events at x/);
	});
});
