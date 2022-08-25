var extAuto = control.getExtensionLoader().getExtension("ExtensionAutomation")
var envVars = extAuto.getPlan(0).getEnv().getData().getVars()

var OUTPUT_DIR = envVars.get('OUTPUT_DIR')
var NAME = envVars.get('NAME')
var VULNERABILITY = envVars.get('VULNERABILITY')
var SCAN_RULES = envVars.get('SCAN_RULES').split(',')
var NESTED_NODE_LEVEL = envVars.get('NESTED_NODE_LEVEL')
var IGNORE_TREE_PATHS = envVars.get('IGNORE_TREE_PATHS').split(',')
var VULNERABLE_TESTS = envVars.get('VULNERABLE_TESTS').split(',')

var totalUrls = 0;
var totalPassed = 0;
var target = 'https://localhost:8443/benchmark';

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
                let testName = path.split('/')[2]
                let testNumber = testName.substr(testName.length - 5)
                let vulnerable = VULNERABLE_TESTS.indexOf(testNumber) >= 0;
                let reported = false;
                pw.println('  vulnerable: ' + vulnerable);
                var pluginId = nodeHasAlert(child, SCAN_RULES);
                if (pluginId) {
                    reported = true;
                    pw.println('  reported: true');
                    pw.println('  rule: ' + pluginId);
                } else {
                    reported = false;
                    pw.println('  reported: false');
                    pw.println('  rule: ' + SCAN_RULES[0]);
                }
                if (vulnerable == reported) {
                    totalPassed++;
                    pw.println('  result: Pass')
                } else {
                    pw.println('  result: FAIL')
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
pw.println('passes: ' + totalPassed);
pw.println('fails: ' + (totalUrls - totalPassed));
pw.println('score: ' + Math.round(totalPassed * 100 / totalUrls) + '%');
pw.close();

print('Wrote output to', YAML_FILE);
