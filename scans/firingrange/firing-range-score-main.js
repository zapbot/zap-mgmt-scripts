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

function nodeGetAlerts(node, rules) {
   var matchedRules = [];
   var alerts = node.getAlerts();
   for (var a in alerts) {
       var pluginId = alerts.get(a).getPluginId();
       if (rules.includes(pluginId) && !matchedRules.includes(pluginId)) {
           matchedRules.push(pluginId);
       }
   }
   return matchedRules;
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
               if (!(path in results)) {
                   results[path] = [];
               }
               var matchedRules = nodeGetAlerts(child, RULES);
               for (var r = 0; r < matchedRules.length; r++) {
                   if (!results[path].includes(matchedRules[r])) {
                       results[path].push(matchedRules[r]);
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

var paths = Object.keys(results).sort();
for (var i = 0; i < paths.length; i++) {
    var path = paths[i];
    var matchedRules = results[path];
    var passed = matchedRules.length > 0;
    totalUrls++;
    pw.println('- path: ' + path);
    if (BROKEN_PATHS.includes(path)) {
        if (passed) {
            // Not really broken, would be good to flag in some way?
            totalAlerts++;
            pw.println('  result: Pass');
            pw.println('  rules: [' + matchedRules.join(', ') + ']');
        } else {
            totalUrls--;
            pw.println('  result: Broken');
        }
    } else if (passed) {
        totalAlerts++;
        pw.println('  result: Pass');
        pw.println('  rules: [' + matchedRules.join(', ') + ']');
    } else {
        pw.println('  result: FAIL');
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
