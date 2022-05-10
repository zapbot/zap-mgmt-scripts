var TARGET = "xss/reflect";
var RULES = [40012];
var MIN_LEVEL = 1;
var IGNORE_PATHS = ['', 'write', 'write_hash', 'write_hash_urlstyle', 'node_hash', 'node_hash_unencoded', 'node_hash_urlstyle',
	'/post1', '/post1_splash', '/raw1', '/raw1_fp', '/full_cookies1', '/full_headers1', '/full_useragent1', 
	'/xyz', '/xyz/*http:', '/xyz//example.com'];

// Polyfill for Nashorn c/o https://stackoverflow.com/questions/47543566/scriptengine-javascript-doesnt-support-includes
if (!Array.prototype.includes) { 
  Object.defineProperty(Array.prototype, 'includes', { 
    value: function(valueToFind, fromIndex) { 
      if (this == null) { 
        throw new TypeError('\"this\" is null or not defined'); 
      } 
      var o = Object(this); 
      var len = o.length >>> 0; 
      if (len === 0) { return false; } 
      var n = fromIndex | 0; 
      var k = Math.max(n >= 0 ? n : len - Math.abs(n), 0); 
      function sameValueZero(x, y) { return x === y || (typeof x === 'number' && typeof y === 'number' && isNaN(x) && isNaN(y)); } 
      while (k < len) { if (sameValueZero(o[k], valueToFind)) { return true; } k++; } return false; 
    } 
   });
}

var totalUrls = 0;
var passes = 0;
var fps = 0;
var fns = 0;
var target = 'http://localhost:9090/' + TARGET;

var FileWriter = Java.type('java.io.FileWriter');
var PrintWriter = Java.type('java.io.PrintWriter');

var yamlFile = "/zap/wrk/reflected.yml";
var fw = new FileWriter(yamlFile);
var pw = new PrintWriter(fw);

pw.println('section: Reflected JavaScript');
pw.println('details:');

function nodeHasAlert(node, rules) {
   var alerts = node.getAlerts();
   for (var a in alerts) {
       var pluginId = alerts.get(a).getPluginId();
       if (rules.includes(pluginId)) {
           return pluginId;
       }
   }
   return null;
}

function listChildren(node, level) {
   var j;
   var results = {};
   for (j=0;j<node.getChildCount();j++) {
       var child = node.getChildAt(j);
       if (child.getChildCount() == 0 && level > MIN_LEVEL) {
           var path = child.getHierarchicNodeName().substring(target.length);
           if (! IGNORE_PATHS.includes(path)) {
             totalUrls++;
             pw.println('- path: ' + path);

             output = path + '\t\t';
             var fp = false;
             if (path.endsWith('_fp')) {
               output += 'FP\t';
               fp = true;
               pw.println('  notes: \'Not Vulnerable\'');
             } else {
               output += '\t';
               pw.println('  notes: \'\'');
             }
             var pluginId = nodeHasAlert(child, RULES);
             var result;
             if (pluginId) {
                 pw.println('  rule: ' + pluginId);
                 if (fp) {
                   result = 'FAIL';
                   pw.println('  result: FAIL');
                 } else {
                   result = 'Pass';
                   pw.println('  result: Pass');
                 }
             } else {
                 pw.println('  rule:');
                 if (fp) {
                   result = 'Pass';
                   pw.println('  result: Pass');
                 } else {
                   result = 'FAIL';
                   pw.println('  result: FAIL');
                 }
             }
             output += result;
             if (! (path in results)) {
                 print(output);
                 results[path] = result;
                 if (result == 'Pass') {
                   passes++;
                 } else if (fp) {
                   fps++;
                 } else {
                   fns++;
                 }
             }
           }
       } else {
           listChildren(child, level+1);
       }
   }
}

root = org.parosproxy.paros.model.Model.getSingleton().
       getSession().getSiteTree().getRoot();

listChildren(root, 0);

print('URLs: ' + totalUrls);
print('passes: ' + passes);
print('FPs: ' + fps);
print('FNs: ' + fns);
print('score: ' + Math.round(passes * 100 / (passes + fps + fns)) + '%');

pw.println('tests: ' + totalUrls);
pw.println('passes: ' + passes);
pw.println('fails: ' + (fps + fns));
pw.println('fps: ' + fps);
pw.println('fns: ' + fps);
pw.println('score: ' + Math.round(passes * 100 / (passes + fps + fns)) + '%');

print('Done');

pw.close();
