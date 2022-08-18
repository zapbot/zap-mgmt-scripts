var extAuto = control.getExtensionLoader().getExtension("ExtensionAutomation")
var envVars = extAuto.getPlan(0).getEnv().getData().getVars()

var OUTPUT_DIR = envVars.get('OUTPUT_DIR')
var NAME = envVars.get('NAME')
var VULNERABILITY = envVars.get('VULNERABILITY')
var SCAN_RULES = envVars.get('SCAN_RULES').split(',')
var NESTED_NODE_LEVEL = envVars.get('NESTED_NODE_LEVEL')
var IGNORE_TREE_PATHS = envVars.get('IGNORE_TREE_PATHS').split(',')

var totalUrls = 0;
var totalAlerts = 0;
var target = 'https://localhost:8443/';

var FileWriter = Java.type('java.io.FileWriter');
var PrintWriter = Java.type('java.io.PrintWriter');

var YAML_FILE = OUTPUT_DIR + "/" + VULNERABILITY + ".yaml";
var fw = new FileWriter(YAML_FILE);
var pw = new PrintWriter(fw);

pw.println('section: ' + NAME);
pw.println('url: ' + target);
pw.println('details:');

function nodeHasAlert(node, rules) {
    var alerts = node.getAlerts();
    for (var a in alerts) {
        var pluginId = String(alerts.get(a).getPluginId());
        if (rules.indexOf(pluginId) >= 0) {
            return pluginId;
        }
    }
    return null;
}

function listChildren(node, level) {
    var j;
    for (j = 0; j < node.getChildCount(); j++) {
        var child = node.getChildAt(j);
        if (child.getChildCount() == 0 && level > NESTED_NODE_LEVEL) {
            var path = child.getHierarchicNodeName().substring(target.length).replace('()', '');
            if (!IGNORE_TREE_PATHS.indexOf(path) >= 0) {
                totalUrls++;
                pw.println('- path: ' + path);
                var pluginId = nodeHasAlert(child, SCAN_RULES);
                if (pluginId) {
                    totalAlerts++;
                    pw.println('  result: Pass');
                    pw.println('  rule: ' + pluginId);
                } else {
                    pw.println('  result: FAIL');
                    pw.println('  rule: ' + SCAN_RULES[0]);
                }
            }
        } else {
            listChildren(child, level + 1);
        }
    }
}

root = org.parosproxy.paros.model.Model.getSingleton().
    getSession().getSiteTree().getRoot();

listChildren(root, 0);

pw.println('tests: ' + totalUrls);
pw.println('passes: ' + totalAlerts);
pw.println('fails: ' + (totalUrls - totalAlerts));
pw.println('score: ' + Math.round(totalAlerts * 100 / totalUrls) + '%');
pw.close();

print('Wrote output to', YAML_FILE);
