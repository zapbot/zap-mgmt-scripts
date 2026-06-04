var DIR = "/zap/wrk/";
var NAME = "Address DOM XSS";
var TARGET = "address";
var RULES = [40012, 40026, 200002, 200007, 210000, 220000, 220001, 220002, 220003, 220005, 220009, 2200011];
var MIN_LEVEL = 2;
var INCLUDE_PATHS = [
	'/URL/documentwrite',
	'/URLUnencoded/documentwrite',
	'/baseURI/documentwrite',
	'/documentURI/documentwrite',
	'/location/assign',
	'/location/documentwrite',
	'/location/documentwriteln',
	'/location/eval',
	'/location/innerHtml',
	'/location/rangeCreateContextualFragment',
	'/location/replace',
	'/location/setTimeout',
	'/location.hash/assign',
	'/location.hash/documentwrite',
	'/location.hash/documentwriteln',
	'/location.hash/eval',
	'/location.hash/formaction',
	'/location.hash/function',
	'/location.hash/inlineevent',
	'/location.hash/innerHtml',
	'/location.hash/jshref',
	'/location.hash/onclickAddEventListener',
	'/location.hash/onclickSetAttribute',
	'/location.hash/rangeCreateContextualFragment',
	'/location.hash/replace',
	'/location.hash/setTimeout',
	'/locationhref/documentwrite',
	'/locationpathname/documentwrite',
	'/locationsearch/documentwrite',
];
var BROKEN_PATHS = [];
