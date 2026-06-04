var DIR = "/zap/wrk/";
var NAME = "Reverse ClickJacking";
var TARGET = "reverseclickjacking";
var RULES = [10020];
var MIN_LEVEL = 1;
var INCLUDE_PATHS = [
	'/multipage/ParameterInFragment/InCallback/WithXFO/',
	'/multipage/ParameterInFragment/InCallback/WithoutXFO/',
	'/multipage/ParameterInFragment/OtherParameter/WithXFO/',
	'/multipage/ParameterInFragment/OtherParameter/WithoutXFO/',
	'/multipage/ParameterInQuery/InCallback/WithXFO/',
	'/multipage/ParameterInQuery/InCallback/WithoutXFO/',
	'/multipage/ParameterInQuery/OtherParameter/WithXFO/',
	'/multipage/ParameterInQuery/OtherParameter/WithoutXFO/',
	'/singlepage/ParameterInFragment/InCallback/',
	'/singlepage/ParameterInFragment/OtherParameter/',
	'/singlepage/ParameterInQuery/InCallback/',
	'/singlepage/ParameterInQuery/OtherParameter/',
];
var BROKEN_PATHS = [];
