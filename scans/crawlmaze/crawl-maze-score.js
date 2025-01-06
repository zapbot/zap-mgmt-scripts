// Score ZAP against Google Security Crawl Maze
//
// You will need to have run one or both of the ZAP spiders against https://security-crawl-maze.app/

// Expected results sourced from:
// https://raw.githubusercontent.com/google/security-crawl-maze/master/blueprints/utils/resources/expected-results.json

var expectedResults = [
	"/javascript/frameworks/angular/event-handler.found",
	"/javascript/frameworks/angular/router-outlet.found",
	"/javascript/frameworks/angularjs/index.html#!/ng-href.found",
	"/javascript/frameworks/polymer/event-handler.found",
	"/javascript/frameworks/polymer/polymer-router.found",
	"/javascript/frameworks/react/search.found",
	"/javascript/frameworks/react/route-path.found",
	"/test/css/font-face.found",
	"/test/headers/content-location.found",
	"/test/headers/link.found",
	"/test/headers/location.found",
	"/test/headers/refresh.found",
	"/test/html/body/a/href.found",
	"/test/html/body/a/ping.found",
	"/test/html/body/applet/archive.found",
	"/test/html/body/applet/codebase.found",
	"/test/html/body/audio/source/src.found",
	"/test/html/body/audio/source/srcset1x.found",
	"/test/html/body/audio/source/srcset2x.found",
	"/test/html/body/audio/src.found",
	"/test/html/body/background.found",
	"/test/html/body/blockquote/cite.found",
	"/test/html/body/embed/src.found",
	"/test/html/body/form/action-get.found",
	"/test/html/body/form/action-post.found",
	"/test/html/body/form/button/formaction.found",
	"/test/html/body/frameset/frame/src.found",
	"/test/html/body/iframe/src.found",
	"/test/html/body/iframe/srcdoc.found",
	"/test/html/body/img/dynsrc.found",
	"/test/html/body/img/longdesc.found",
	"/test/html/body/img/lowsrc.found",
	"/test/html/body/img/src-data.found",
	"/test/html/body/img/src.found",
	"/test/html/body/img/srcset1x.found",
	"/test/html/body/img/srcset2x.found",
	"/test/html/body/input/src.found",
	"/test/html/body/isindex/action.found",
	"/test/html/body/map/area/ping.found",
	"/test/html/body/object/codebase.found",
	"/test/html/body/object/data.found",
	"/test/html/body/object/param/value.found",
	"/test/html/body/script/src.found",
	"/test/html/body/svg/image/xlink.found",
	"/test/html/body/svg/script/xlink.found",
	"/test/html/body/table/background.found",
	"/test/html/body/table/td/background.found",
	"/test/html/body/video/poster.found",
	"/test/html/body/video/src.found",
	"/test/html/body/video/track/src.found",
	"/test/html/doctype.found",
	"/test/html/head/base/href.found",
	"/test/html/head/comment-conditional.found",
	"/test/html/head/import/implementation.found",
	"/test/html/head/link/href.found",
	"/test/html/head/meta/content-csp.found",
	"/test/html/head/meta/content-pinned-websites.found",
	"/test/html/head/meta/content-reading-view.found",
	"/test/html/head/meta/content-redirect.found",
	"/test/html/head/profile.found",
	"/test/html/manifest.found",
	"/test/html/misc/string/dot-dot-slash-prefix.found",
	"/test/html/misc/string/dot-slash-prefix.found",
	"/test/html/misc/string/string-known-extension.pdf",
	"/test/html/misc/string/url-string.found",
	"/test/html/misc/url/full-url.found",
	"/test/html/misc/url/path-relative-url.found",
	"/test/html/misc/url/protocol-relative-url.found",
	"/test/html/misc/url/root-relative-url.found",
	"/test/javascript/interactive/js-delete.found",
	"/test/javascript/interactive/js-post-event-listener.found",
	"/test/javascript/interactive/js-post.found",
	"/test/javascript/interactive/js-put.found",
	"/test/javascript/interactive/listener-and-event-attribute-first.found",
	"/test/javascript/interactive/listener-and-event-attribute-second.found",
	"/test/javascript/interactive/multi-step-request-event-attribute.found",
	"/test/javascript/interactive/multi-step-request-event-listener-div-dom.found",
	"/test/javascript/interactive/multi-step-request-event-listener-div.found",
	"/test/javascript/interactive/multi-step-request-event-listener-dom.found",
	"/test/javascript/interactive/multi-step-request-event-listener.found",
	"/test/javascript/interactive/multi-step-request-redefine-event-attribute.found",
	"/test/javascript/interactive/multi-step-request-remove-button.found",
	"/test/javascript/interactive/multi-step-request-remove-event-listener.found",
	"/test/javascript/interactive/two-listeners-first.found",
	"/test/javascript/interactive/two-listeners-second.found",
	"/test/javascript/misc/automatic-post.found",
	"/test/javascript/misc/comment.found",
	"/test/javascript/misc/string-concat-variable.found",
	"/test/javascript/misc/string-variable.found",
	"/test/misc/known-files/robots.txt.found",
	"/test/misc/known-files/sitemap.xml.found"
]


function findNode(scheme, path) {
	var uri = new URI(scheme + '://' + target + path, true);
	var n = siteTree.findNode(uri);
	if (n == null) {
		// Find parent then loop through child nodes checking for the URL path
		var parent = siteTree.findClosestParent(uri);
		if (parent) {
			for (var j = 0; j < parent.getChildCount(); j++) {
				var child = parent.getChildAt(j);
				if (child.getHierarchicNodeName().indexOf(path) > 0) {
					n = child;
					break;
				}
			}
		}
	}
	return n;
}

var HistoryReference = Java.type('org.parosproxy.paros.model.HistoryReference');
var URI = Java.type('org.apache.commons.httpclient.URI');

var FieldUtils = Java.type('org.apache.commons.lang3.reflect.FieldUtils');

function clientUrlExists(node, url) {
	const nodeUrl = node.getUserObject().getUrl()
	if (url == nodeUrl) {
		return true;
	}
	if (nodeUrl && nodeUrl.startsWith(url)) {
		return true;
	}
	for (var i = 0; i < node.getChildCount(); i++) {
		if (clientUrlExists(node.getChildAt(i), url)) {
			return true;
		}
	}
	return false;
}

var extClient = control.getExtensionLoader().getExtension("ExtensionClientIntegration");
var clientRoot;
if (extClient) {
	clientRoot = FieldUtils.readField(extClient, "clientTree", true).getRoot();
}
var found = 0;
var foundStandard = 0;
var foundAjax = 0;
var foundClient = 0;
var total = expectedResults.length;

var target = 'security-crawl-maze.app';
var siteTree = org.parosproxy.paros.model.Model.getSingleton().getSession().getSiteTree();

var FileWriter = Java.type('java.io.FileWriter');
var PrintWriter = Java.type('java.io.PrintWriter');

var yamlFile = "/zap/wrk/all.yml";
var fw = new FileWriter(yamlFile);
var pw = new PrintWriter(fw);

pw.println('section: All URLs');
pw.println('target: ' + target);
pw.println('details:');

for (var i in expectedResults) {
	var res = expectedResults[i];
	var scheme = 'http';
	var node = findNode(scheme, res);
	if (!node) {
		scheme = 'https';
		node = findNode(scheme, res);
	}

	pw.println('- path: ' + res);
	var standardResult = "FAIL";
	var ajaxResult = "FAIL";
	var clientResult = "FAIL";
	var passed = false;
	if (node) {
		passed = true;
		if (node.hasHistoryType(HistoryReference.TYPE_SPIDER)) {
			standardResult = "Pass";
			foundStandard++;
		}
		if (node.hasHistoryType(HistoryReference.TYPE_SPIDER_AJAX)) {
			ajaxResult = "Pass";
			foundAjax++;
		}
		if (node.hasHistoryType(HistoryReference.TYPE_CLIENT_SPIDER)) {
			clientResult = "Pass";
			foundClient++;
		}
	}
	if (clientResult !== "Pass" && extClient && clientUrlExists(clientRoot, scheme + "://" + target + res)) {
		clientResult = "Pass";
		passed = true;
		foundClient++;
	}
	if (passed) {
		found++;
	}
	pw.println('  scheme: ' + scheme);
	pw.println('  standard: ' + standardResult);
	pw.println('  ajax: ' + ajaxResult);
	pw.println('  client: ' + clientResult);
}

print('tests: ' + total);
print('passes: ' + found);
print('standardPasses: ' + foundStandard);
print('ajaxPasses: ' + foundAjax);
print('clientPasses: ' + foundClient);
print('fails: ' + (total - found));

pw.println('tests: ' + total);
pw.println('passes: ' + found);
pw.println('standardPasses: ' + foundStandard);
pw.println('ajaxPasses: ' + foundAjax);
pw.println('clientPasses: ' + foundClient);
pw.println('fails: ' + (total - found));
pw.println('score: ' + Math.round(found * 100 / total) + '%');

print('Done');

pw.close();
