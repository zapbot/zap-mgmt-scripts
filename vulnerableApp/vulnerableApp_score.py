# Zed Attack Proxy (ZAP) and its related class files.
#
# ZAP is an HTTP/HTTPS proxy for assessing web application security.
#
# Copyright 2012 ZAP Development Team
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# This script tests ZAP against Owasp VulnerableApp: https://github.com/SasanLabs/VulnerableApp
# Note: Owasp VulnerableApp has to be installed somewhere - the above link is to the github
# project not the test suite!
#
# To use this script:
# * Install the ZAP Python API:
#     Use 'pip install zaproxy'
# * Start ZAP (as this is for testing purposes you might not want the
#     'standard' ZAP to be started)
# * Access Owasp VulnerableApp via your browser, proxying through ZAP
# * Visit all levels of vulnerabilities of the VulnerableApp e.g.
#     http://localhost:9090/
# * Run the Spider against http://localhost:9090
# * Run the Active Scanner against http://localhost:9090
# * Run this script
# * Open the report.html file generated in your browser
#
# Note: Owasp VulnerableApp exposes the definition of the vulnerability at '/scanner' endpoint so
# raising requests by understanding will give more accurate and better results.

from zapv2 import ZAPv2
import datetime, sys, getopt, html, requests, json

plugin_information = {
    '6': ['Path Traversal', 'PathTrav'],
    '43': ["Source Code Disclosure - File Inclusion", "SrcInc"],
    '10020': ["X-Frame-Options Header Not Set", "XFrame"],
    '10016': ["Web Browser XSS Protection Not Enabled", "XSSProtectionNotEnabled"],
    '10021': ["X-Content-Type-Options Header Missing", "XContent"],
    '10024': ["Information Disclosure - Sensitive Information in URL", "URLinfo"],
    '10028': ["Open Redirect", "OpenRedir"],
    '10029': ["Cookie Poisoning", "CookiePoison"],
    '10031': ["User Controllable HTML Element Attribute (Potential XSS)", "MaybeXSS"],
    '10036': ["Server Leaks Version Information via \"Server\" HTTP Response Header Field", "ServerLeak"],
    '10038': ["Content Security Policy (CSP) Header Not Set", "NoCSP"],
    '10043': ["User Controllable JavaScript Event (XSS)", "UserJsEvent"],
    '10049': ["Content Cacheability", "ContentCache"],
    '10058': ["GET for POST", "GetForPost"],
    '10062': ["PII Disclosure", "PII"],
    '10063': ["Feature Policy Header Not Set", "FeaturePolicyNotSet"],
    '10096': ["Timestamp Disclosure - Unix", "Timestamp"],
    '10104': ["User Agent Fuzzer", "UAfuzz"],
    '10109': ["Modern Web Application", "ModernApp"],
    '10202': ["Absence of Anti-CSRF Tokens", "NoCSRF"],
    '20012': ["Anti CSRF Tokens Scanner", "ACSRF"],
    '20019': ["External Redirect", "ExtRedir"],
    '30001': ["Buffer Overflow", "Buffer"],
    '30002': ["Format String Error", "Format"],
    '30003': ["Integer Overflow Error", "IntOver"],
    '40012': ['Cross Site Scripting (Reflected)', 'RXSS'],
    '40014': ['Cross Site Scripting (Persistent) - Prime', 'PXSS'],
    '40015': ['LDAP Injection', 'LDAPi'],
    '40016': ['Cross Site Scripting (Persistent)', 'PXSS'],
    '40017': ['Cross Site Scripting (Persistent) - Spider', 'PXSSS'],
    '40019': ['SQL Injection - MySQL', 'MysqlSqli'],
    '40024': ['SQL Injection - SQLite', 'SqliteSqli'],
    '40026': ["Cross Site Scripting (DOM Based)", "DXSS"],
    '40036': ['JWT Scan Rule', 'JWT'],
    '40041': ['FileUpload Scan Rule', 'FileUpload'],
    '90018': ['Advanced SQL Injection', 'AdvSqli'],
    '90020': ['Remote OS Command Injection', 'CommandInjection'],
    '90023': ['XML External Entity Attack', 'XXE'],
    '90022': ["Application Error Disclosure", "AppError"],
    '90024': ["Generic Padding Oracle", "PaddingOracle"],
    '90027': ["Cookie Slack Detector", "CookieSlack"],
    '90033': ["Loosely Scoped Cookie", "CookieLoose"]
}


def listToLinks(l):
    s = ''
    if l:
        for i in l:
            if (i in plugin_information):
                s += '<a href="#' + i + '">' + plugin_information.get(i)[1] + '</a> '
            else:
                s += '<a href="#' + i + '">' + i + '</a> '
    return s


def main(argv):
    # -------------------------------------------------------------------------
    # Default Configurations - use -h and -p for different host and port
    # -------------------------------------------------------------------------
    zapHost = '127.0.0.1'
    zapPort = '8090'

    try:
        opts, args = getopt.getopt(argv, "h:p:")
    except getopt.GetoptError:
        print('vulnerableApp_score.py -h <ZAPhost> -p <ZAPport>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            zapHost = arg
        elif opt == '-p':
            zapPort = arg

    zapUrl = 'http://' + zapHost + ':' + zapPort

    # Reverse map which stores ZAP's plugin Id vs Owasp VulnerableApp's vulnerability types
    zap_plugin_id_vs_vulnapp_vulnerability_types = {
        '6': ['PATH_TRAVERSAL'],
        '10028': ['OPEN_REDIRECT_3XX_STATUS_CODE'],
        '40012': ['REFLECTED_XSS'],
        '40014': ['PERSISTENT_XSS'],
        '40016': ['PERSISTENT_XSS'],
        '40017': ['PERSISTENT_XSS'],
        '90020': ['COMMAND_INJECTION'],
        '40019': ['UNION_BASED_SQL_INJECTION', 'BLIND_SQL_INJECTION', 'ERROR_BASED_SQL_INJECTION'],
        '40024': ['UNION_BASED_SQL_INJECTION', 'BLIND_SQL_INJECTION', 'ERROR_BASED_SQL_INJECTION'],
        '90018': ['UNION_BASED_SQL_INJECTION', 'BLIND_SQL_INJECTION', 'ERROR_BASED_SQL_INJECTION'],
        '40036': ['SERVER_SIDE_VULNERABLE_JWT', 'INSECURE_CONFIGURATION_JWT', 'CLIENT_SIDE_VULNERABLE_JWT'],
        '90023': ['XXE'],
        '40041': ['UNRESTRICTED_FILE_UPLOAD','PERSISTENT_XSS','REFLECTED_XSS','PATH_TRAVERSAL']
    }

    zap = ZAPv2(proxies={'http': zapUrl, 'https': zapUrl})

    uniqueUrls = set([])

    # alertsPerUrl is a dictionary of urlsummary to a dictionary of type to set of alertshortnames ;)
    alerts_per_url = {}
    alert_pass_count = {}
    alert_fail_count = {}
    alert_ignore_count = {}
    alert_other_count = {}

    total_vulnerability_type_count = {}
    url_vs_vulnapp_vuln_info = {}

    zap_version = zap.core.version

    total_alerts = 0
    offset = 0
    page = 1000
    # Page through the alerts as otherwise ZAP can hang...
    alerts = zap.core.alerts('', offset, page)
    # Scanner endpoint of Owasp VulnerableApp which provides information related to vulnerabilities present.
    vulnerable_app_scanner_response = requests.get("http://127.0.0.1:9090/VulnerableApp/scanner",
                                                   proxies={'http': zapUrl, 'https': zapUrl}, verify=False)
    if vulnerable_app_scanner_response.status_code != 200:
        print("Failure while accessing scanner endpoint" + str(vulnerable_app_scanner_response))
        sys.exit(2)
    else:
        vulnerability_info = vulnerable_app_scanner_response.json()
        for vulnapp_vuln_info in vulnerability_info:
            if vulnapp_vuln_info["variant"] == "UNSECURE":
                url = vulnapp_vuln_info["url"]
                if url not in url_vs_vulnapp_vuln_info:
                    url_vs_vulnapp_vuln_info[url] = []
                url_vs_vulnapp_vuln_info[url].append(vulnapp_vuln_info)
                for vulnerabilityType in vulnapp_vuln_info['vulnerabilityTypes']:
                    total_vulnerability_type_count[vulnerabilityType] = total_vulnerability_type_count.get(
                        vulnerabilityType, 0) + 1

        while len(alerts) > 0:
            total_alerts += len(alerts)
            for alert in alerts:
                url = alert.get('url')
                print(url)
                # Grab the url before any '?'
                url_without_query_param = url.split('?')[0]
                aDict = alerts_per_url.get(url_without_query_param,
                                           {'pass': set([]), 'fail': set([]), 'ignore': set([]), 'other': set([])})
                if url_without_query_param in url_vs_vulnapp_vuln_info:
                    if alert.get('pluginId') in zap_plugin_id_vs_vulnapp_vulnerability_types:
                        vulnapp_vuln_types_for_pluginid = zap_plugin_id_vs_vulnapp_vulnerability_types.get(
                            alert.get('pluginId'))
                        for vulnapp_vuln_info in url_vs_vulnapp_vuln_info.get(url_without_query_param):
                            for vulnapp_vuln_type in vulnapp_vuln_info.get('vulnerabilityTypes'):
                                is_found = False
                                for zap_pluginid_vuln in vulnapp_vuln_types_for_pluginid:
                                    if vulnapp_vuln_type == zap_pluginid_vuln:
                                        is_found = True
                                        # print(zap_pluginid_vuln + "  " + alert.get('pluginId'))
                                        aDict['pass'].add(alert.get('pluginId'))
                                        alert_pass_count[alert.get('pluginId')] = alert_pass_count.get(
                                            alert.get('pluginId'), 0) + 1
                                if not is_found:
                                    alert_fail_count[alert.get('pluginId')] = alert_fail_count.get(
                                        alert.get('pluginId'), 0) + 1
                                    aDict['fail'].add(alert.get('pluginId'))
                        alerts_per_url[url_without_query_param] = aDict
                    else:
                        alert_ignore_count[alert.get('pluginId')] = alert_ignore_count.get(alert.get('pluginId'), 0) + 1
                        aDict['other'].add(alert.get('pluginId'))
                uniqueUrls.add(url_without_query_param)
            offset += page
            alerts = zap.core.alerts('', offset, page)

    # Generate report file
    reportFile = open('report.html', 'w')
    reportFile.write("<html>\n")
    reportFile.write("  <head>\n")
    reportFile.write("    <title>ZAP VulnerableApp Report</title>\n")
    reportFile.write("    <!--Load the AJAX API-->\n")
    reportFile.write("    <script type=\"text/javascript\" src=\"https://www.google.com/jsapi\"></script>\n")
    reportFile.write("  </head>\n")
    reportFile.write("<body>\n")

    reportFile.write(
        "<h1><img src=\"https://raw.githubusercontent.com/zaproxy/zaproxy/main/zap/src/main/resources/resource/zap64x64.png\" align=\"middle\">OWASP ZAP VulnerableApp results</h1>\n")
    reportFile.write("Generated: " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M") + "\n")

    top_level_results = []
    this_top = ['', 0, 0]
    totalPass = 0
    totalFail = 0

    # Calculate the top level scores
    for url in sorted(url_vs_vulnapp_vuln_info):
        top_level = url.split('/')[3]
        if url in alerts_per_url:
            value = alerts_per_url.get(url)
            if (top_level != this_top[0]):
                this_top = [top_level, 0, 0]  # top level, pass, fail
                top_level_results.append(this_top)
            if (len(value.get('pass')) > 0):
                totalPass += len(value.get('pass'))
                this_top[1] += len(value.get('pass'))
            if (len(value.get('fail')) > 0):
                totalFail += len(value.get('fail'))
                this_top[2] += len(value.get('fail'))
            if (len(value.get('ignore')) > 0):
                totalFail += len(value.get('ignore'))
                this_top[2] += len(value.get('ignore'))
            this_top[2] += len(url_vs_vulnapp_vuln_info.get(url)) - len(value.get('pass'))
        else:
            # These Vulnerabilities are the one's that are not spidered.
            if (top_level != this_top[0]):
                this_top = [top_level, 0, 0]  # top_level, pass, fail
                top_level_results.append(this_top)
            totalFail += len(url_vs_vulnapp_vuln_info.get(url))
            this_top[2] += len(url_vs_vulnapp_vuln_info.get(url))
    # Output the summary
    scale = 1
    reportFile.write("<h3>Total Score</h3>\n")
    reportFile.write("<font style=\"BACKGROUND-COLOR: GREEN\">")
    for i in range(int(totalPass / scale)):
        reportFile.write("&nbsp;")
    reportFile.write("</font>")
    reportFile.write("<font style=\"BACKGROUND-COLOR: RED\">")
    for i in range(int(totalFail / scale)):
        reportFile.write("&nbsp;")
    reportFile.write("</font>")
    total = 0
    if (totalPass + totalFail) != 0:
        total = 100 * totalPass / (totalPass + totalFail)
    reportFile.write("{:.2f}%<br/><br/>\n".format(total))

    reportFile.write('ZAP Version: ' + zap_version + '<br/>\n')
    reportFile.write('URLs found: ' + str(len(uniqueUrls)))

    # Output the top level table
    reportFile.write("<h3>Top Level Scores</h3>\n")
    reportFile.write("<table border=\"1\">\n")
    reportFile.write("<tr><th>Top Level</th><th>Pass</th><th>Fail</th><th>Score</th><th>Chart</th></tr>\n")

    scale = 1
    for top_level_result in top_level_results:
        reportFile.write("<tr>")
        reportFile.write("<td>{0}</td>".format(html.escape(top_level_result[0])))
        reportFile.write("<td align=\"right\">" + str(top_level_result[1]) + "</td>")
        reportFile.write("<td align=\"right\">" + str(top_level_result[2]) + "</td>")
        score = 100 * top_level_result[1] / (top_level_result[1] + top_level_result[2])
        reportFile.write("<td align=\"right\">" + "{:.2f}".format(score) + "%</td>")
        reportFile.write("<td>")
        reportFile.write("<font style=\"BACKGROUND-COLOR: GREEN\">")
        for i in range(int(top_level_result[1] / scale)):
            reportFile.write("&nbsp;")
        reportFile.write("</font>")
        reportFile.write("<font style=\"BACKGROUND-COLOR: RED\">")
        for i in range(int(top_level_result[2] / scale)):
            reportFile.write("&nbsp;")
        reportFile.write("</font>")
        reportFile.write("</td>")
        reportFile.write("</tr>\n")

    reportFile.write("</table><br/>\n")


    reportFile.write("<h3>Alerts</h3>\n")
    reportFile.write("<table border=\"1\">\n")
    reportFile.write(
        "<tr><th>Alert</th><th>Description</th><th>Pass</th><th>Fail</th><th>Ignore</th><th>Other</th></tr>\n")
    for pluginid, details in plugin_information.items():
        reportFile.write("<tr>")
        reportFile.write("<td>" + details[1] + "</td>")
        reportFile.write(
            "<td><a name=\"" + pluginid + "\" href=\"https://www.zaproxy.org/docs/alerts/" + pluginid + "/\">" +
            details[0]
            + "</a></td>")
        reportFile.write("<td>" + str(alert_pass_count.get(pluginid, 0)) + "&nbsp;</td>")
        reportFile.write("<td>" + str(alert_fail_count.get(pluginid, 0)) + "&nbsp;</td>")
        reportFile.write("<td>" + str(alert_ignore_count.get(pluginid, 0)) + "&nbsp;</td>")
        reportFile.write("<td>" + str(alert_other_count.get(pluginid, 0)) + "&nbsp;</td>")
        reportFile.write("</tr>\n")
    reportFile.write("</table><br/>\n")


    # Output the detail table
    reportFile.write("<h3>Detailed Results</h3>\n")
    reportFile.write("<table border=\"1\">\n")
    reportFile.write("<tr><th>Page</th><th>Result</th><th>Pass</th><th>Fail</th><th>Ignore</th><th>Other</th></tr>\n")

    # We are considering first plugin id only because VulnerableApp's Vulnerability Types don't have one-on-one
    # mapping with ZAP plugin id.
    vulnerable_app_vulnerability_type_vs_plugin_id = {}
    for plugin_id in zap_plugin_id_vs_vulnapp_vulnerability_types:
        for vulnerabilityType in zap_plugin_id_vs_vulnapp_vulnerability_types.get(plugin_id):
            vulnerable_app_vulnerability_type_vs_plugin_id[vulnerabilityType] = plugin_id
    for url in sorted(url_vs_vulnapp_vuln_info):
        key = url
        vulnerability_infos = url_vs_vulnapp_vuln_info.get(url)
        pluginids = set([])
        for vulnerability_info in vulnerability_infos:
            for vulnerabilityType in vulnerability_info["vulnerabilityTypes"]:
                if vulnerabilityType in vulnerable_app_vulnerability_type_vs_plugin_id.keys():
                    pluginids.add(vulnerable_app_vulnerability_type_vs_plugin_id.get(vulnerabilityType))
        value = alerts_per_url.get(url, {'pass': set([]), 'fail': pluginids, 'ignore': set([]), 'other': set([])});
        reportFile.write("<tr>")
        keyArray = key.split('/')
        if (len(keyArray) == 5):
            reportFile.write("<td>{0}</td>".format(html.escape(keyArray[3] + "-" + keyArray[4])))
        else:
            reportFile.write("<td>{0}</td>".format(html.escape(key)))
        reportFile.write("<td>")
        if (len(value.get('pass')) > 0):
            reportFile.write("<font style=\"BACKGROUND-COLOR: GREEN\">&nbsp;PASS&nbsp</font>")
        elif (len(value.get('fail')) > 0):
            reportFile.write("<font style=\"BACKGROUND-COLOR: RED\">&nbsp;FAIL&nbsp</font>")
        elif ('FalsePositive' in key):
            reportFile.write("<font style=\"BACKGROUND-COLOR: GREEN\">&nbsp;PASS&nbsp</font>")
        else:
            reportFile.write("<font style=\"BACKGROUND-COLOR: RED\">&nbsp;FAIL&nbsp</font>")
        reportFile.write("</td>")

        reportFile.write("<td>")
        if (value.get('pass') is not None):
            reportFile.write(listToLinks(value.get('pass')))
        reportFile.write("&nbsp;</td>")

        reportFile.write("<td>")
        if (value.get('fail') is not None):
            reportFile.write(listToLinks(value.get('fail')))
        reportFile.write("&nbsp;</td>")

        reportFile.write("<td>")
        if (value.get('ignore') is not None):
            reportFile.write(listToLinks(value.get('ignore')))
        reportFile.write("&nbsp;</td>")

        reportFile.write("<td>")
        if (value.get('other') is not None):
            reportFile.write(listToLinks(value.get('other')))
        reportFile.write("&nbsp;</td>")

        reportFile.write("</tr>\n")

    reportFile.write("</table><br/>\n")

    progress = zap.ascan.scan_progress()
    time = ''

    if not isinstance(progress, str):
        reportFile.write("<h3>Plugin Times</h3>\n")

        # The start of the chart script
        reportFile.write("<script type=\"text/javascript\">\n")
        reportFile.write("  // Load the Visualization API and the piechart package.\n")
        reportFile.write("  google.load('visualization', '1.0', {'packages':['corechart']});\n")
        reportFile.write("  // Set a callback to run when the Google Visualization API is loaded.\n")
        reportFile.write("  google.setOnLoadCallback(drawChart);\n")
        reportFile.write("  function drawChart() {\n")
        reportFile.write("    // Create the data table.\n")
        reportFile.write("    var data = new google.visualization.DataTable();\n")
        reportFile.write("    data.addColumn('string', 'Plugin');\n")
        reportFile.write("    data.addColumn('number', 'Time in ms');\n")
        reportFile.write("    data.addRows([\n")
        # Loop through first time for the chart
        for plugin in progress[1]['HostProcess']:
            reportFile.write("      ['" + plugin['Plugin'][0] + "', " + plugin['Plugin'][4] + "],\n")

        # The end of the first chart
        reportFile.write("    ]);\n")
        reportFile.write("    // Set chart options\n")
        reportFile.write("    var options = {'title':'Plugin times',\n")
        reportFile.write("                   'width':600,\n")
        reportFile.write("                   'height':500};\n")
        reportFile.write("    // Instantiate and draw our chart, passing in some options.\n")
        reportFile.write("    var chart = new google.visualization.PieChart(document.getElementById('chart_div'));\n")
        reportFile.write("    chart.draw(data, options);\n")
        reportFile.write("\n")
        reportFile.write("    // Create the 2nd data table.\n")
        reportFile.write("    var data2 = new google.visualization.DataTable();\n")
        reportFile.write("    data2.addColumn('string', 'Plugin');\n")
        reportFile.write("    data2.addColumn('number', 'Requests');\n")
        reportFile.write("    data2.addRows([\n")

        # Loop through 2nd time for the 2nd chart
        for plugin in progress[1]['HostProcess']:
            reportFile.write("      ['" + plugin['Plugin'][0] + "', " + plugin['Plugin'][5] + "],\n")

        # The end of the chart script
        reportFile.write("    ]);\n")
        reportFile.write("    // Set chart options\n")
        reportFile.write("    var options2 = {'title':'Request counts',\n")
        reportFile.write("                   'width':600,\n")
        reportFile.write("                   'height':500};\n")
        reportFile.write("    // Instantiate and draw our chart, passing in some options.\n")
        reportFile.write("    var chart2 = new google.visualization.PieChart(document.getElementById('chart_div2'));\n")
        reportFile.write("    chart2.draw(data2, options2);\n")
        reportFile.write("  }\n")
        reportFile.write("</script>\n")

        reportFile.write("<div id=\"chart_div\" style=\"width: 600px; float: left;\"></div>\n")
        reportFile.write("<div id=\"chart_div2\" style=\"margin-left: 620px;\"></div>\n")

        reportFile.write("<table border=\"1\">\n")
        reportFile.write("<tr><th>Plugin</th><th>ms</th><th>Reqs</th>")
        reportFile.write("<th>Quality</th>")
        reportFile.write("</tr>\n")

        # Loop through second time for the table
        totalTime = 0
        vulnDict = {}
        for plugin in progress[1]['HostProcess']:
            vulnDict[plugin['Plugin'][1]] = plugin['Plugin'][0];

        print(vulnDict)
        for plugin in progress[1]['HostProcess']:
            reportFile.write("<tr>")
            reportFile.write("<td>" + plugin['Plugin'][0] + "</td>")
            # Convert ms into something more readable
            t = int(plugin['Plugin'][4])
            totalTime += t
            s, ms = divmod(t, 1000)
            m, s = divmod(s, 60)
            h, m = divmod(m, 60)
            time = "%d:%02d:%02d.%03d" % (h, m, s, ms)
            reportFile.write("<td>" + time + "</td>")
            reportFile.write("<td>" + plugin['Plugin'][5] + "</td>")
            reportFile.write("<td>" + plugin['Plugin'][2] + "</td>")
            reportFile.write("</tr>\n")

        reportFile.write("<tr><td></td><td></td><td></td>")
        reportFile.write("<td></td>")
        reportFile.write("</tr>")
        reportFile.write("<tr>")
        reportFile.write("<td>Total</td>")
        # Convert ms into something more readable
        s, ms = divmod(totalTime, 1000)
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        time = "%d:%02d:%02d" % (h, m, s)
        reportFile.write("<td>" + time + "</td>")
        reportFile.write("<td>-</td>")
        reportFile.write("<td>-</td>")
        reportFile.write("</tr>\n")

        reportFile.write("</table><br/>\n")

    reportFile.write("</body></html>\n")
    reportFile.close()

    reportFile.close()
    print('')
    print('ZAP ' + zap_version)
    print('Got ' + str(total_alerts) + ' alerts')
    print('Got ' + str(len(uniqueUrls)) + ' unique urls')
    print('Took ' + time)
    print('Score ' + str(int(total)))


if __name__ == "__main__":
    main(sys.argv[1:])
