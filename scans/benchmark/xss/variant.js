/*
Variant Script for ignoring OWASP Benchmark pages that we don't want to attack.
*/

const List = Java.type("java.util.List");

function parseParameters(helper, msg) { }

function setParameter(helper, msg, param, value, escaped) { }

function getLeafName(helper, nodeName, msg) {
	if (helper.getParamList().isEmpty()) {
		return null;
	}
	return helper.getStandardLeafName(nodeName, msg, helper.getParamList());
}

var ignored_paths = [
]

function getTreePath(helper, msg) {
	var uri = msg.getRequestHeader().getURI();
	var path = uri.getPath()
	if (/^\/benchmark\/xss-\d\d\/BenchmarkTest\d\d\d\d\d.html$/.test(path)) {
		return List.of();
	}
	var method = msg.getRequestHeader().getMethod()
	if (method == "GET" && ignored_paths.indexOf(path) >= 0) {
		return List.of();
	}
	return null;
}
