// Score ZAP against Google Security Crawl Maze
//
// You will need to have run one or both of the ZAP spiders against https://security-crawl-maze.app/

// Expected results sourced from:
// https://raw.githubusercontent.com/google/security-crawl-maze/master/blueprints/utils/resources/expected-results.json

var expectedResults = [
	"/css/font-face.found",
	"/headers/content-location.found",
	"/headers/link.found",
	"/headers/location.found",
	"/headers/refresh.found",
	"/html/doctype.found",
	"/html/manifest.found",
	"/html/body/background.found",
	"/html/body/a/href.found",
	"/html/body/a/ping.found",
	"/html/body/audio/src.found",
	"/html/body/applet/archive.found",
	"/html/body/applet/codebase.found",
	"/html/body/blockquote/cite.found",
	"/html/body/embed/src.found",
	"/html/body/form/action-get.found",
	"/html/body/form/action-post.found",
	"/html/body/form/button/formaction.found",
	"/html/body/frameset/frame/src.found",
	"/html/body/iframe/src.found",
	"/html/body/iframe/srcdoc.found",
	"/html/body/img/dynsrc.found",
	"/html/body/img/lowsrc.found",
	"/html/body/img/longdesc.found",
	"/html/body/img/src-data.found",
	"/html/body/img/src.found",
	"/html/body/img/srcset1x.found",
	"/html/body/img/srcset2x.found",
	"/html/body/input/src.found",
	"/html/body/isindex/action.found",
	"/html/body/map/area/ping.found",
	"/html/body/object/data.found",
	"/html/body/object/codebase.found",
	"/html/body/object/param/value.found",
	"/html/body/script/src.found",
	"/html/body/svg/image/xlink.found",
	"/html/body/svg/script/xlink.found",
	"/html/body/table/background.found",
	"/html/body/table/td/background.found",
	"/html/body/video/src.found",
	"/html/body/video/poster.found",
	"/html/head/profile.found",
	"/html/head/base/href.found",
	"/html/head/comment-conditional.found",
	"/html/head/import/implementation.found",
	"/html/head/link/href.found",
	"/html/head/meta/content-csp.found",
	"/html/head/meta/content-pinned-websites.found",
	"/html/head/meta/content-reading-view.found",
	"/html/head/meta/content-redirect.found",
	"/html/misc/url/full-url.found",
	"/html/misc/url/path-relative-url.found",
	"/html/misc/url/protocol-relative-url.found",
	"/html/misc/url/root-relative-url.found",
	"/html/misc/string/dot-dot-slash-prefix.found",
	"/html/misc/string/dot-slash-prefix.found",
	"/html/misc/string/url-string.found",
	"/html/misc/string/string-known-extension.pdf",
	"/javascript/misc/comment.found",
	"/javascript/misc/string-variable.found",
	"/javascript/misc/string-concat-variable.found",
	"/javascript/frameworks/angular/event-handler.found",
	"/javascript/frameworks/angular/router-outlet.found",
	"/javascript/frameworks/angularjs/ng-href.found",
	"/javascript/frameworks/polymer/event-handler.found",
	"/javascript/frameworks/polymer/polymer-router.found",
	"/javascript/frameworks/react/route-path.found",
	"/javascript/frameworks/react/index.html/search.found",
	"/misc/known-files/robots.txt.found",
	"/misc/known-files/sitemap.xml.found"
]
var HistoryReference = Java.type('org.parosproxy.paros.model.HistoryReference');
var URI = Java.type('org.apache.commons.httpclient.URI');

var found = 0;
var foundStandard = 0;
var foundAjax = 0;
var total = expectedResults.length;

var target = 'security-crawl-maze.app';
var httpResults = 'http://' + target + '/test';
var httpsResults = 'https://' + target + '/test';
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
	var node = siteTree.findNode(new URI(httpResults + res, true));
	if (!node) {
		node = siteTree.findNode(new URI(httpsResults + res, true));
		scheme = 'https';
	}

	pw.println('- path: /test' + res);
	var standardResult = "FAIL";
	var ajaxResult = "FAIL";
	if (node) {
		found++;
		if (node.hasHistoryType(HistoryReference.TYPE_SPIDER)) {
			standardResult = "Pass";
			foundStandard++;
		}
		if (node.hasHistoryType(HistoryReference.TYPE_SPIDER_AJAX)) {
			ajaxResult = "Pass";
			foundAjax++;
		}
	}
	pw.println('  scheme: ' + scheme);
	pw.println('  standard: ' + standardResult);
	pw.println('  ajax: ' + ajaxResult);
}

print('tests: ' + total);
print('passes: ' + found);
print('standardPasses: ' + foundStandard);
print('ajaxPasses: ' + foundAjax);
print('fails: ' + (total - found));

pw.println('tests: ' + total);
pw.println('passes: ' + found);
pw.println('standardPasses: ' + foundStandard);
pw.println('ajaxPasses: ' + foundAjax);
pw.println('fails: ' + (total - found));
pw.println('score: ' + Math.round(found * 100 / total) + '%');

print('Done');

pw.close();
