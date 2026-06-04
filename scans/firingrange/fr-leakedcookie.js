var DIR = "/zap/wrk/";
var NAME = "Leaked httpOnly cookie";
var TARGET = "leakedcookie";
var RULES = [10011];
var MIN_LEVEL = 1;
var INCLUDE_PATHS = [
	'/leakedcookie',
	'/leakedinresource',
];
var BROKEN_PATHS = [];
