var DIR = "/zap/wrk/";
var NAME = "URL-based DOM XSS";
var TARGET = "urldom";
var RULES = [
	40012, 40026, 200002, 200007, 210000, 220000, 220001, 
	220002, 220003, 220005, 220006, 220009, 2200010, 2200011, 2200013];
var MIN_LEVEL = 1;
var INCLUDE_PATHS = [
	'/location/hash/a.href',
	'/location/hash/base.href',
	'/location/hash/document.location',
	'/location/hash/embed.src',
	'/location/hash/fetch',
	'/location/hash/form.action',
	'/location/hash/iframe.src',
	'/location/hash/input.formaction',
	'/location/hash/link.href',
	'/location/hash/object.data',
	'/location/hash/param.code.value',
	'/location/hash/param.movie.value',
	'/location/hash/param.src.value',
	'/location/hash/param.url.value',
	'/location/hash/script.href',
	'/location/hash/script.src',
	'/location/hash/script.src.partial_domain',
	'/location/hash/script.src.partial_path',
	'/location/hash/script.src.partial_query',
	'/location/hash/window.open',
	'/location/hash/xhr.open',
	'/location/search/area.href',
	'/location/search/button.formaction',
	'/location/search/frame.src',
	'/location/search/location.assign',
	'/location/search/svg.a',
];
var BROKEN_PATHS = [];
