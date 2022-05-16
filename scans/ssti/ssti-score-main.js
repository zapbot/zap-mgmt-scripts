// This script will _not_ run on its own - it needs a set of fields prepended to it
var YAML_FILE = "/zap/wrk/all.yml";
var RULES = [40012, 40026, 90019, 90025, 90035, 90036];
var target = 'http://localhost:' + PORT + '/';
  
var FileWriter = Java.type('java.io.FileWriter');
var PrintWriter = Java.type('java.io.PrintWriter');
  
var fw = new FileWriter(YAML_FILE, true);
var pw = new PrintWriter(fw);

function nodeHasAlert(node, pluginId) {
        var alerts = node.getAlerts();
        for (var a in alerts) {
                if (pluginId == alerts.get(a).getPluginId()) {
                        return true;
                }
        }
        return false;
}

function hasAlert(node, pluginId) {
        var j;
        for (j = 0; j < node.getChildCount(); j++) {
                var child = node.getChildAt(j);
                if (child.getChildCount() == 0) {
                        if (nodeHasAlert(child, pluginId)) {
                                return true;
                        }
                } else {
                        if (hasAlert(child, pluginId)) {
                                return true;
                        }
                }
        }
        return false;
}

var root = org.parosproxy.paros.model.Model.getSingleton().
        getSession().getSiteTree().getRoot();
var any = 'FAIL';

pw.println('- title: \'' + TITLE + '\'');

for (var i in RULES) {
        var pluginId = RULES[i];
        if (hasAlert(root, pluginId)) {
                pw.println('  rule_' + pluginId + ': Pass');
                any = 'Pass';
        } else {
                pw.println('  rule_' + pluginId + ': FAIL');
        }
}
pw.println('  any: ' + any);
pw.close();

print('Done');
