// Score ZAP against WAVSEP

var DIR = "/zap/wrk/res/";
var IGNORE_PATHS = [];
var BROKEN_PATHS = [];

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

var totalPass = 0;
var totalFail = 0;
var sectionPass;
var sectionFail;

var FileWriter = Java.type('java.io.FileWriter');
var PrintWriter = Java.type('java.io.PrintWriter');

root = org.parosproxy.paros.model.Model.getSingleton().
       getSession().getSiteTree().getRoot();

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

function isBroken(url) {
   for (i=0;i<BROKEN_PATHS.length;i++) {
      if (url.indexOf(BROKEN_PATHS[i]) > 0) {
         return true;
      }
   }
   // Mass check for broken LFI tests - all odd numbers 37+
   var paths = url.split("/");
   if (paths[5] === "LFI") {
      // The 7th element will be like Case08-LFI-...
      var c = paths[7];
      var dash = c.indexOf("-");
      var idx = parseInt(c.substring(4, dash));
      if (idx >= 37 && (idx & 1)) {
         return true;
      }
   }
   return false;
}

function listChildren(pw, node, type, rules) {
   var j;
   for (j=0;j<node.getChildCount();j++) {
       var child = node.getChildAt(j);
       if (child.getChildCount() == 0) {
           var path = child.getHierarchicNodeName();
           if (path.indexOf(type) > -1 && path.indexOf("Case") > -1) {
             // All good
           } else {
             continue;
           }
           if (path.indexOf("POST") > -1 && child.getNodeName().startsWith("GET")) {
             continue;
           }
           if (! IGNORE_PATHS.includes(path)) {
             pw.println('- path: ' + path);
             var pluginId = nodeHasAlert(child, rules);
             // Following test is JS equiv of XOR
             if (path.indexOf("FalsePositives") > 0 ? !pluginId : pluginId) {
                 sectionPass++;
                 pw.println('  result: Pass');
                 pw.println('  rule: ' + pluginId);
             } else if (isBroken(path)) {
                 pw.println('  result: Broken');
                 pw.println('  rule: ' + rules[0]);
             } else {
                 sectionFail++;
                 pw.println('  result: FAIL');
                 pw.println('  rule: ' + rules[0]);
             }
           }
       } else {
           listChildren(pw, child, type, rules);
       }
   }
}

function scoreChildren(file, name, type, rules) {
   var YAML_FILE = DIR + "/" + file + ".yml";
   var fw = new FileWriter(YAML_FILE);
   var pw = new PrintWriter(fw);

   pw.println('section: ' + name);
   pw.println('url: ' + type);
   pw.println('details:');

   sectionPass = 0;
   sectionFail = 0;

   listChildren(pw, root, type, rules);

   var sectionTotal = sectionPass + sectionFail;
   pw.println('tests: ' + sectionTotal);
   pw.println('passes: ' + sectionPass);
   pw.println('fails: ' + sectionFail);
   pw.println('score: ' + Math.round(sectionPass * 100 / sectionTotal) + '%');
   
   totalPass += sectionPass;
   totalFail += sectionFail;

   pw.close();
}

function scoreTotal() {
   var YAML_FILE = DIR + "/totals.yml";
   var fw = new FileWriter(YAML_FILE);
   var pw = new PrintWriter(fw);

   var total = totalPass + totalFail;
   pw.println('tests: ' + total);
   pw.println('passes: ' + totalPass);
   pw.println('fails: ' + totalFail);
   pw.println('score: ' + Math.round(totalPass * 100 / total) + '%');

   pw.close();
}

scoreChildren("dom-xss-get-exp", "DOM XSS GET Experimental", "/DXSS-Detection-Evaluation-GET-Experimental/", [40026]);

scoreChildren("lfi-get-200-err", "Local File Include GET 200 Error", "/LFI-Detection-Evaluation-GET-200Error/", [6]);
scoreChildren("lfi-get-200-id", "Local File Include GET 200 Identical", "/LFI-Detection-Evaluation-GET-200Identical/", [6]);
scoreChildren("lfi-get-200-valid", "Local File Include GET 200 Valid", "/LFI-Detection-Evaluation-GET-200Valid/", [6]);
scoreChildren("lfi-get-302-redir", "Local File Include GET 302 Redirect", "/LFI-Detection-Evaluation-GET-302Redirect/", [6]);
scoreChildren("lfi-get-400-err", "Local File Include GET 404 Error", "/LFI-Detection-Evaluation-GET-404Error/", [6]);
scoreChildren("lfi-get-500-err", "Local File Include GET 500 Error", "/LFI-Detection-Evaluation-GET-500Error/", [6]);
scoreChildren("lfi-post-200-err", "Local File Include POST 200 Error", "/LFI-Detection-Evaluation-POST-200Error/", [6]);
scoreChildren("lfi-post-200-id", "Local File Include POST 200 Identical", "/LFI-Detection-Evaluation-POST-200Identical/", [6]);
scoreChildren("lfi-post-200-valid", "Local File Include POST 200 Valid", "/LFI-Detection-Evaluation-POST-200Valid/", [6]);
scoreChildren("lfi-post-302-redir", "Local File Include POST 302 Redirect", "/LFI-Detection-Evaluation-POST-302Redirect/", [6]);
scoreChildren("lfi-post-404-err", "Local File Include POST 404 Error", "/LFI-Detection-Evaluation-POST-404Error/", [6]);
scoreChildren("lfi-post-500-err", "Local File Include POST 500 Error", "/LFI-Detection-Evaluation-POST-500Error/", [6]);
scoreChildren("lfi-get-fp", "Local File Include GET False Positives ", "/LFI-FalsePositives-GET/", [6]);

scoreChildren("rfi-get-200-err", "Remote File Include GET 200 Error", "/RFI-Detection-Evaluation-GET-200Error/", [7]);
scoreChildren("rfi-get-200-id", "Remote File Include GET 200 Identical", "/RFI-Detection-Evaluation-GET-200Identical/", [7]);
scoreChildren("rfi-get-200-valid", "Remote File Include GET 200 Valid", "/RFI-Detection-Evaluation-GET-200Valid/", [7]);
scoreChildren("rfi-get-302-redir", "Remote File Include GET 302 Redirect", "/RFI-Detection-Evaluation-GET-302Redirect/", [7]);
scoreChildren("rfi-get-404-err", "Remote File Include GET 404 Error", "/RFI-Detection-Evaluation-GET-404Error/", [7]);
scoreChildren("rfi-get-500-err", "Remote File Include GET 500 Error", "/RFI-Detection-Evaluation-GET-500Error/", [7]);
scoreChildren("rfi-post-200-err", "Remote File Include POST 200 Error", "/RFI-Detection-Evaluation-POST-200Error/", [7]);
scoreChildren("rfi-post-200-id", "Remote File Include POST 200 Identical", "/RFI-Detection-Evaluation-POST-200Identical/", [7]);
scoreChildren("rfi-post-200-valid", "Remote File Include POST 200 Valid", "/RFI-Detection-Evaluation-POST-200Valid/", [7]);
scoreChildren("rfi-post-302-redir", "Remote File Include POST 302 Redirect", "/RFI-Detection-Evaluation-POST-302Redirect/", [7]);
scoreChildren("rfi-post-400-err", "Remote File Include POST 404 Error", "/RFI-Detection-Evaluation-POST-404Error/", [7]);
scoreChildren("rfi-post-402-err", "Remote File Include POST 500 Error", "/RFI-Detection-Evaluation-POST-500Error/", [7]);
scoreChildren("rfi-get-fp", "Remote File Include GET False Positives", "/RFI-FalsePositives-GET/", [7]);

scoreChildren("rxss-cookie-exp", "Reflected XSS Cookie Experimental", "/RXSS-Detection-Evaluation-COOKIE-Experimental/", [40012]);
scoreChildren("rxss-get", "Reflected XSS GET", "/RXSS-Detection-Evaluation-GET/", [40012]);
scoreChildren("rxss-get-exp", "Reflected XSS GET Experimental", "/RXSS-Detection-Evaluation-GET-Experimental/", [40012]);
scoreChildren("rxss-post", "Reflected XSS POST", "/RXSS-Detection-Evaluation-POST/", [40012]);
scoreChildren("rxss-post-exp", "Reflected XSS POST Experimental", "/RXSS-Detection-Evaluation-POST-Experimental/", [40012]);
scoreChildren("rxss-fps", "Reflected XSS GET False Positives", "/RXSS-FalsePositives-GET/", [40012]);

scoreChildren("sqli-get-200-err", "SQL Injection GET 200 Error", "/SInjection-Detection-Evaluation-GET-200Error/", [40018,40019]);
scoreChildren("sqli-get-200-err-exp", "SQL Injection GET 200 Error Experimental", "/SInjection-Detection-Evaluation-GET-200Error-Experimental/", [40018,40019]);
scoreChildren("sqli-get-200-id", "SQL Injection GET 200 Identical", "/SInjection-Detection-Evaluation-GET-200Identical/", [40018,40019]);
scoreChildren("sqli-get-200-valid", "SQL Injection GET 200 Valid", "/SInjection-Detection-Evaluation-GET-200Valid/", [40018,40019]);
scoreChildren("sqli-get-500-err", "SQL Injection GET 500 Error", "/SInjection-Detection-Evaluation-GET-500Error/", [40018,40019]);
scoreChildren("sqli-post-200-err", "SQL Injection POST 200 Error", "/SInjection-Detection-Evaluation-POST-200Error/", [40018,40019]);
scoreChildren("sqli-post-200-err-exp", "SQL Injection POST 200 Error Experimental", "/SInjection-Detection-Evaluation-POST-200Error-Experimental/", [40018,40019]);
scoreChildren("sqli-post-200-id", "SQL Injection POST 200 Identical", "/SInjection-Detection-Evaluation-POST-200Identical/", [40018,40019]);
scoreChildren("sqli-post-200-valid", "SQL Injection POST 200 Valid", "/SInjection-Detection-Evaluation-POST-200Valid/", [40018,40019]);
scoreChildren("sqli-post-500-err", "SQL Injection POST 500 Error", "/SInjection-Detection-Evaluation-POST-500Error/", [40018,40019]);
scoreChildren("sqli-get-fp", "SQL Injection GET False Positives", "/SInjection-FalsePositives-GET/", [40018,40019]);

scoreChildren("redir-get-302", "Unvalidated Redirect GET 200", "/Redirect-Detection-Evaluation-GET-302Redirect/", [20019]);
scoreChildren("redir-post-302", "Unvalidated Redirect POST 302", "/Redirect-Detection-Evaluation-POST-302Redirect/", [20019]);
scoreChildren("redir-get-fp", "Unvalidated Redirect GET False Positives", "/Redirect-FalsePositives-GET/", [20019]);
scoreChildren("redir-get-200-valid", "Unvalidated Redirect GET 200 Valid", "/Redirect-JavaScript-Detection-Evaluation-GET-200Valid/", [20019]);
scoreChildren("redir-post-200-valid", "Unvalidated Redirect POST 200 Valid", "/Redirect-JavaScript-Detection-Evaluation-POST-200Valid/", [20019]);

scoreChildren("cmdi-get-200-error", "OS Command Injection GET 200 Error", "/OS-Command-Injection/OS-Command-Injection-GET-200Error", [90020]);
scoreChildren("cmdi-get-500-error", "OS Command Injection GET 500 Error", "/OS-Command-Injection/OS-Command-Injection-GET-500Error", [90020]);
scoreChildren("cmdi-post-200-error", "OS Command Injection POST 200 Error", "/OS-Command-Injection/OS-Command-Injection-POST-200Error", [90020]);
scoreChildren("cmdi-post-500-error", "OS Command Injection POST 500 Error", "/OS-Command-Injection/OS-Command-Injection-POST-500Error", [90020]);

scoreChildren("xxe-post-500-error", "XXE POST Error", "/XXE-POST-500Error", [90023]);
scoreChildren("xxe-post-input-500-error", "XXE POST Field Input Error", "/XXE-POST-Input-500Error", [90023]);
scoreChildren("xxe-post-intercept-500-error", "XXE POST Intercepted Request Error", "/XXE-POST-Intercept-500Error", [90023]);

scoreTotal();

print('Done');
