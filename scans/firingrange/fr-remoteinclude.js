var DIR = "/zap/wrk/";
var NAME = "Remote Inclusion XSS";
var TARGET = "remoteinclude";
var RULES = [40012, 40026, 200002, 200007, 200023, 210000, 220000, 220009];
var MIN_LEVEL = 1;
var INCLUDE_PATHS = [
	'/object_hash.html',
	'/parameter/object/application_x-shockwave-flash',
	'/parameter/object_raw',
	'/parameter/script',
	'/script_hash.html',
];
var BROKEN_PATHS = [];
