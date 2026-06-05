// This script will _not_ run on its own - it needs a set of fields prepended to it

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
var totalAlerts = 0;
var target = 'https://public-firing-range.appspot.com/' + TARGET;

var FileWriter = Java.type('java.io.FileWriter');
var PrintWriter = Java.type('java.io.PrintWriter');

var YAML_FILE = DIR + "/" + TARGET + ".yml";
var fw = new FileWriter(YAML_FILE);
var pw = new PrintWriter(fw);

pw.println('section: ' + NAME);
pw.println('url: ' + target);
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

var results = {};

function listChildren(node, level) {
   var j;
   for (j=0;j<node.getChildCount();j++) {
       var child = node.getChildAt(j);
       if (child.getChildCount() == 0 && level > MIN_LEVEL) {
           if (j + 1<node.getChildCount()) {
               // Check for sibling with same name - those will be GETs to parent nodes, which we can ignore
               var sibling = node.getChildAt(j+1);
               if (child.getHierarchicNodeName() === sibling.getHierarchicNodeName() && sibling.getChildCount() > 0) {
                   continue;
               }
           }

           var path = child.getHierarchicNodeName();
           if (!path.startsWith(target)) {
               continue;
           }
           path = path.substring(target.length);
           if (INCLUDE_PATHS.length === 0 || INCLUDE_PATHS.includes(path)) {
               var pluginId = nodeHasAlert(child, RULES);
               if (!(path in results)) {
                   results[path] = null;
               }
               if (pluginId && !results[path]) {
                   results[path] = pluginId;
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

var paths = Object.keys(results).sort();
for (var i = 0; i < paths.length; i++) {
    var path = paths[i];
    var pluginId = results[path];
    totalUrls++;
    pw.println('- path: ' + path);
    if (BROKEN_PATHS.includes(path)) {
        if (pluginId) {
            // Not really broken, would be good to flag in some way?
            totalAlerts++;
            pw.println('  result: Pass');
            pw.println('  rule: ' + pluginId);
        } else {
            totalUrls--;
            pw.println('  result: Broken');
            pw.println('  rule: ' + pluginId);
        }
    } else if (pluginId) {
        totalAlerts++;
        pw.println('  result: Pass');
        pw.println('  rule: ' + pluginId);
    } else {
        pw.println('  result: FAIL');
        pw.println('  rule: ' + RULES[0]);
    }
}

var score = Math.round(totalAlerts * 100 / totalUrls);
pw.println('tests: ' + totalUrls);
pw.println('passes: ' + totalAlerts);
pw.println('fails: ' + (totalUrls - totalAlerts));
pw.println('score: ' + score + '%');

print('Done');
print('Done: ' + NAME + ' score: ' + score);

pw.close();
