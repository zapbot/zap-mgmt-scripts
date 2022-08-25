/*
Variant Script for ignoring OWASP Benchmark pages that we don't want to attack.
*/

function parseParameters(helper, msg) { }

function setParameter(helper, msg, param, value, escaped) { }

function getLeafName(helper, nodeName, msg) {
	if (helper.getParamList().isEmpty()) {
		return null;
	}
	return helper.getStandardLeafName(nodeName, msg, helper.getParamList());
}

var ignored_paths = [
	"/benchmark/cmdi-00/BenchmarkTest00077",
	"/benchmark/cmdi-00/BenchmarkTest00090",
	"/benchmark/cmdi-00/BenchmarkTest00091",
	"/benchmark/cmdi-00/BenchmarkTest00092",
	"/benchmark/cmdi-00/BenchmarkTest00093",
	"/benchmark/cmdi-01/BenchmarkTest00968",
	"/benchmark/cmdi-01/BenchmarkTest00969",
	"/benchmark/cmdi-01/BenchmarkTest00970",
	"/benchmark/cmdi-01/BenchmarkTest00978",
	"/benchmark/cmdi-01/BenchmarkTest00979",
	"/benchmark/cmdi-01/BenchmarkTest00980",
	"/benchmark/cmdi-01/BenchmarkTest00981",
	"/benchmark/cmdi-01/BenchmarkTest00982",
	"/benchmark/cmdi-01/BenchmarkTest00983",
	"/benchmark/cmdi-02/BenchmarkTest01850",
	"/benchmark/cmdi-02/BenchmarkTest01851",
	"/benchmark/cmdi-02/BenchmarkTest01852",
	"/benchmark/cmdi-02/BenchmarkTest01864",
	"/benchmark/cmdi-02/BenchmarkTest01865",
]

function getTreePath(helper, msg) {
	var uri = msg.getRequestHeader().getURI();
	var path = uri.getPath()
	if (/^\/benchmark\/cmdi-\d\d\/BenchmarkTest\d\d\d\d\d.html$/.test(path)) {
		return []
	}
	var method = msg.getRequestHeader().getMethod()
	if (method == "GET" && ignored_paths.indexOf(path) >= 0) {
		return []
	}
	return null;
}
