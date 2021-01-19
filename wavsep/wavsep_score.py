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

# This script tests ZAP against wavsep: http://code.google.com/p/wavsep/
# Note wavsep has to be installed somewhere - the above link is to the 
# project not the test suite!
#
# To this script:
# * Install the ZAP Python API: 
#     Use 'pip install python-owasp-zap-v2' or
#     download from https://github.com/zaproxy/zaproxy/wiki/Downloads
# * Start ZAP (as this is for testing purposes you might not want the
#     'standard' ZAP to be started)
# * Access wavsep via your browser, proxying through ZAP
# * Vist all of the wavsep top level URLs, eg
#     http://localhost:8080/wavsep/index-active.jsp
#     http://localhost:8080/wavsep/index-passive.jsp
# * Run the Spider against http://localhost:8080
# * Run the Active Scanner against http://localhost:8080/wavsep
# * Run this script
# * Open the report.html file generated in your browser
#
# Notes:
# This has been tested against wavsep 1.5

from zapv2 import ZAPv2
import datetime, sys, getopt, html

def listToLinks(l):
	s = ''
	if l:
		for i in l:
			s += '<a href="#' + i + '">' + i + '</a> '
	return s

def main(argv):
	# -------------------------------------------------------------------------
	# Default Configurations - use -h and -p for different host and port
	# -------------------------------------------------------------------------
	zapHost = '127.0.0.1'
	zapPort = '8090'

	try:
		opts, args = getopt.getopt(argv,"h:p:")
	except getopt.GetoptError:
		print('wavsep.py -h <ZAPhost> -p <ZAPport>')
		sys.exit(2)
	for opt, arg in opts:
		if opt == '-h':
			zapHost = arg
		elif opt == '-p':
			zapPort = arg

	zapUrl = 'http://' + zapHost + ':' + zapPort

	# Dictionary of abbreviation to keep the output a bit shorter
	abbrev = {
			'10020': ["X-Frame-Options Header Not Set", "XFrame"], \
			'10021': ["X-Content-Type-Options Header Missing", "XContent"], \
			'10024': ["Information Disclosure - Sensitive Information in URL", "URLinfo"], \
			'10028': ["Open Redirect", "OpenRedir"], \
			'10029': ["Cookie Poisoning", "CookiePoison"], \
			'10031': ["User Controllable HTML Element Attribute (Potential XSS)", "MaybeXSS"], \
			'10036': ["Server Leaks Version Information via \"Server\" HTTP Response Header Field", "ServerLeak"], \
			'10038': ["Content Security Policy (CSP) Header Not Set", "NoCSP"], \
			'10043': ["User Controllable JavaScript Event (XSS)", "UserJsEvent"], \
			'10058': ["GET for POST", "GetForPost"], \
			'10062': ["PII Disclosure", "PII"], \
			'10096': ["Timestamp Disclosure - Unix", "Timestamp"], \
			'10104': ["User Agent Fuzzer", "UAfuzz"], \
			'10109': ["Modern Web Application", "ModernApp"], \
			'10202': ["Absence of Anti-CSRF Tokens", "NoCSRF"], \
			'20012': ["Anti CSRF Tokens Scanner", "ACSRF"], \
			'20019': ["External Redirect", "ExtRedir"], \
			'30001': ["Buffer Overflow", "Buffer"], \
			'30002': ["Format String Error", "Format"], \
			'30003': ["Integer Overflow Error", "IntOver"], \
			'40012': ["Cross Site Scripting (Reflected)", "RXSS"], \
			'40014': ["Cross Site Scripting (Persistent)", "PXSS"], \
			'40018': ["SQL Injection - MySQL", "SqlMySql"], \
			'40018': ["SQL Injection", "SQLi"], \
			'40019': ["SQL Injection - MySQL", "SqlMySql"], \
			'40026': ["Cross Site Scripting (DOM Based)", "DXSS"], \
			'43': ["Source Code Disclosure - File Inclusion", "SrcInc"], \
			'6': ["Path Traversal", "PathTrav"], \
			'7': ["Remote File Inclusion", "RFI"], \
			'90022': ["Application Error Disclosure", "AppError"], \
			'90024': ["Generic Padding Oracle", "PaddingOracle"], \
			'90027': ["Cookie Slack Detector", "CookieSlack"], \
			'90033': ["Loosely Scoped Cookie", "CookieLoose"], \
		}
	# Want to keep these for mapping some of the rules that were not run during testing...
	oldAbbrev = {
			'Active Vulnerability title' : 'Ex',\
			'Cross Site Scripting (DOM Based)' : 'DXSS',\
			'Cross Site Scripting (Persistent)' : 'PXSS',\
			'Cross Site Scripting (Reflected)' : 'RXSS',\
			'Absence of Anti-CSRF Tokens' : 'NoCSRF',\
			'Application Error Disclosure' : 'AppError',\
			'Anti CSRF Tokens Scanner' : 'ACSRF',\
			'Buffer Overflow' : 'Buffer',\
			'Cookie set without HttpOnly flag' : 'HttpOnly',\
			'Cookie No HttpOnly Flag' : 'HttpOnly',\
			'Cookie Slack Detector' : 'CookieSlack',\
			'Cross Site Request Forgery' : 'CSRF',\
			'External Redirect' : 'ExtRedir',\
			'Format String Error' : 'Format',\
			'HTTP Parameter Override' : 'ParamOver',\
			'Information disclosure - database error messages' : 'InfoDb',\
			'Information disclosure - debug error messages' : 'InfoDebug',\
			'Information Disclosure - Sensitive Informations in URL' : 'InfoUrl',\
			'Integer Overflow Error' : 'IntOver',\
			'LDAP Injection' : 'LDAP',\
			'Loosely Scoped Cookie' : 'CookieLoose',\
			'None. Warning only.' : 'NoCSRF2',\
			'Password Autocomplete in Browser' : 'Auto',\
			'Password Autocomplete in browser' : 'Auto',\
			'Path Traversal' : 'PathTrav',\
			'Private IP Disclosure' : 'PrivIP',\
			'Remote File Inclusion' : 'RFI',\
			'Remote OS Command Injection' : 'RCI',\
			'Session ID in URL Rewrite' : 'SessRewrite',\
			'Source Code Disclosure - File Inclusion' : 'SrcInc',\
			'SQL Injection' : 'SQLi',\
			'SQL Injection - MySQL' : 'SqlMySql',\
			'SQL Injection - Generic SQL RDBMS' : 'SqlGen',\
			'SQL Injection - Boolean Based' : 'SqlBool',\
			'SQL Injection - Error Based - Generic SQL RDBMS' : 'SqlGenE',\
			'SQL Injection - Error Based - MySQL' : 'SqlMySqlE',\
			'SQL Injection - Error Based - Java' : 'SqlJavaE',\
			'SQL Injection - Hypersonic SQL - Time Based' : 'SqlHyperT',\
			'SQL Injection - MySQL - Time Based' : 'SqlMySqlT',\
			'SQL Injection - Oracle - Time Based' : 'SqlOracleT',\
			'SQL Injection - PostgreSQL - Time Based' : 'SqlPostgreT',\
			'URL Redirector Abuse' : 'UrlRedir',\
			'User Agent Fuzzer' : 'UAfuzz',\
			'Viewstate without MAC Signature (Unsure)' : 'ViewstateNoMac',\
			'Weak Authentication Method' : 'WeakAuth',\
			'Web Browser XSS Protection Not Enabled' : 'XSSoff',\
			'X-Content-Type-Options Header Missing' : 'XContent',\
			'X-Frame-Options Header Not Set' : 'XFrame'}

	# The rules to apply:
	# Column 1:	String to match against an alert URL
	# Column 2: Alert abbreviation to match
	# Column 3: pass, fail, ignore
	# 
	rules = [ \
			# Should check again that all of these are valid...
			['-', 'ACSRF', 'ignore'], \
			['-', 'ACSRF', 'ignore'], \
			['-', 'Ex', 'ignore'], \
			['-', 'CookieLoose', 'ignore'], \
			['-', 'CookieSlack', 'ignore'], \
			['-', 'GetForPost', 'ignore'], \
			['-', 'InfoDebug', 'ignore'], \
			['-', 'InfoUrl', 'ignore'], \
			#['-', 'IntOver', 'ignore'], \
			['-', 'NoCSP', 'ignore'], \
			['-', 'NoCSRF2', 'ignore'], \
			['-', 'ParamOver', 'ignore'], \
			['-', 'PrivIP', 'ignore'], \
			['-', 'ServerLeak', 'ignore'], \
			['-', 'SrcInc', 'ignore'], \
			['-', 'Timestamp', 'ignore'], \
			#['-', 'UAfuzz', 'ignore'], \
			['-', 'URLinfo', 'ignore'], \
			['-', 'XFrame', 'ignore'], \
			['-', 'XContent', 'ignore'], \
			['-', 'XSSoff', 'ignore'], \
			#
			['LFI-', 'AppError', 'ignore'], \
			['LFI-', 'Buffer', 'ignore'], \
			['LFI-', 'Format', 'ignore'], \
			['LFI-', 'NoCSRF', 'ignore'], \
			['LFI-', 'RFI', 'ignore'], \
			['LFI-', 'DXSS', 'ignore'], \
			['LFI-', 'RXSS', 'ignore'], \
			['LFI-', 'SqlHyperT', 'ignore'], \
			['LFI-', 'SqlMySql', 'ignore'], \
			['LFI-', 'SqlOracleT', 'ignore'], \
			['LFI-', 'SqlPostgreT', 'ignore'], \
			['Redirect-', 'LDAP', 'ignore'], \
			['Redirect-', 'NoCSRF', 'ignore'], \
			['Redirect-', 'RFI', 'ignore'], \
			['Redirect-', 'DXSS', 'ignore'], \
			['Redirect-', 'RXSS', 'ignore'], \
			['Redirect-', 'SqlHyperT', 'ignore'], \
			['Redirect-', 'SqlMySql', 'ignore'], \
			['Redirect-', 'SqlOracleT', 'ignore'], \
			['Redirect-', 'SqlPostgreT', 'ignore'], \
			['RFI-', 'AppError', 'ignore'], \
			['RFI-', 'Buffer', 'ignore'], \
			['RFI-', 'Format', 'ignore'], \
			['RFI-', 'NoCSRF', 'ignore'], \
			['RFI-', 'DXSS', 'ignore'], \
			['RFI-', 'RXSS', 'ignore'], \
			['RFI-', 'SqlHyperT', 'ignore'], \
			['RFI-', 'SqlMySql', 'ignore'], \
			['RFI-', 'SqlOracleT', 'ignore'], \
			['RFI-', 'SqlPostgreT', 'ignore'], \
			['RXSS-', 'Auto', 'ignore'], \
			['RXSS-', 'Buffer', 'ignore'], \
			['RXSS-', 'Format', 'ignore'], \
			['RXSS-', 'HttpOnly', 'ignore'], \
			['RXSS-', 'NoCSRF', 'ignore'], \
			['RXSS-', 'SqlOracleT', 'ignore'], \
			['RXSS-', 'SqlPostgreT', 'ignore'], \
			['RXSS-', 'SqlMySql', 'ignore'], \
			['RXSS-', 'SqlOracleT', 'ignore'], \
			['RXSS-', 'ViewstateNoMac', 'ignore'], \
			['SInjection-', 'AppError', 'ignore'], \
			['SInjection-', 'Auto', 'ignore'], \
			['SInjection-', 'Buffer', 'ignore'], \
			['SInjection-', 'NoCSRF', 'ignore'], \
			['SInjection-', 'Format', 'ignore'], \
			['SInjection-', 'LDAP', 'ignore'], \
			['SInjection-', 'RXSS', 'ignore'], \
			['SInjection-', 'SqlHyperT', 'ignore'], \
			['LoginBypass', 'Auto', 'ignore'], \
			['CrlfRemovalInHttpHeader', 'HttpOnly', 'ignore'], \
			['Tag2HtmlPageScopeValidViewstateRequired', 'ViewstateNoMac', 'ignore'], \
			['session-password-autocomplete', 'NoCSRF', 'ignore'], \
			#
			['DXSS-Detection-Evaluation', 'DXSS', 'pass'], \
			['LFI-Detection-Evaluation', 'PathTrav', 'pass'], \
			['LFI-FalsePositives', 'PathTrav', 'fail'], \
			['Redirect-', 'ExtRedir', 'pass'], \
			['RFI-Detection-Evaluation', 'RFI', 'pass'], \
			['RFI-FalsePositives', 'RFI', 'fail'], \
			['RXSS-Detection-Evaluation', 'DXSS', 'pass'], \
			['RXSS-Detection-Evaluation', 'PXSS', 'pass'], \
			['RXSS-Detection-Evaluation', 'RXSS', 'pass'], \
			['RXSS-FalsePositives-GET', 'DXSS', 'fail'], \
			['RXSS-FalsePositives-GET', 'PXSS', 'fail'], \
			['RXSS-FalsePositives-GET', 'RXSS', 'fail'], \
		
			['SInjection-Detection-Evaluation', 'SQLfp', 'pass'], \
			['SInjection-Detection-Evaluation', 'SQLi', 'pass'], \
			#['SInjection-Detection-Evaluation', 'SqlHyper', 'pass'], \
			['SInjection-Detection-Evaluation', 'SqlBool', 'pass'], \
			['SInjection-Detection-Evaluation', 'SqlGen', 'pass'], \
			['SInjection-Detection-Evaluation', 'SqlGenE', 'pass'], \
			['SInjection-Detection-Evaluation', 'SqlMySql', 'pass'], \
			['SInjection-Detection-Evaluation', 'SqlMySqlE', 'pass'], \
			['SInjection-Detection-Evaluation', 'SqlMySqlT', 'pass'], \
			['SInjection-Detection-Evaluation', 'SqlOracleT', 'pass'], \
			['SInjection-Detection-Evaluation', 'SqlPostgreT', 'pass'], \
			['SInjection-FalsePositives', 'SQLfp', 'fail'], \
			['SInjection-FalsePositives', 'SQLi', 'fail'], \
			['SInjection-FalsePositives', 'SqlBool', 'fail'], \
			['SInjection-FalsePositives', 'SqlGen', 'fail'], \
			['SInjection-FalsePositives', 'SqlGenE', 'fail'], \
			['SInjection-FalsePositives', 'SqlMySql', 'fail'], \
			['SInjection-FalsePositives', 'SqlMySqlE', 'fail'], \
			['SInjection-FalsePositives', 'SqlMySqlT', 'fail'], \
			['SInjection-FalsePositives', 'SqlHyperT', 'fail'], \
			['SInjection-FalsePositives', 'SqlMySqlT', 'fail'], \
			['SInjection-FalsePositives', 'SqlOracleT', 'fail'], \
			['SInjection-FalsePositives', 'SqlPostgreT', 'fail'], \
		
			['info-cookie-no-httponly', 'HttpOnly', 'pass'], \
			['info-server-stack-trace', 'AppError', 'pass'], \
			['session-password-autocomplete', 'Auto', 'pass'], \
			['weak-authentication-basic', 'WeakAuth', 'pass'], \
			]

	zap = ZAPv2(proxies={'http': zapUrl, 'https': zapUrl})


	uniqueUrls = set([])
	# alertsPerUrl is a disctionary of urlsummary to a dictionary of type to set of alertshortnames ;)
	alertsPerUrl = {}
	plugins = set([])

	alertPassCount = {}
	alertFailCount = {}
	alertIgnoreCount = {}
	alertOtherCount = {}

	zapVersion = zap.core.version

	totalAlerts = 0
	offset = 0
	page = 1000
	# Page through the alerts as otherwise ZAP can hang...
	alerts = zap.core.alerts('', offset, page)
	while len(alerts) > 0:
		totalAlerts += len(alerts)
		for alert in alerts:
			url = alert.get('url')
			# Grab the url before any '?'
			url = url.split('?')[0]
			#print 'URL: ' + url
			urlEl = url.split('/')
			if (len(urlEl) > 6):
				#print 'URL 4:' + urlEl[4] + ' 6:' + urlEl[6].split('-')[0]
				if (urlEl[3] != 'wavsep'):
					print('Ignoring non wavsep URL 4:' + urlEl[4] + ' URL 5:' + urlEl[5]  + ' URL 6:' + urlEl[6])
					continue
				
				if (urlEl[6].split('-')[0][:9] == 'index.jsp'):
					#print 'Ignoring index URL 4:' + urlEl[4] + ' URL 5:' + urlEl[5]  + ' URL 6:' + urlEl[6]
					continue
				if (len(urlEl) > 7 and urlEl[4] == 'active'):
					if (urlEl[7].split('-')[0][:4] != 'Case'):
						#print 'Ignoring index URL 4:' + urlEl[4] + ' URL 5:' + urlEl[5] + ' URL 6:' + urlEl[6] + ' URL 7:' + urlEl[7]
						continue
					urlSummary = urlEl[4] + ' : ' + urlEl[5] + ' : ' + urlEl[6] + ' : ' + urlEl[7].split('-')[0]
				else:
					# Passive URLs have different format
					urlSummary = urlEl[4] + ' : ' + urlEl[5] + ' : ' + urlEl[6]
				
				#print 'URL summary:' + urlSummary
				titleAbrev = abbrev.get(alert.get('pluginId'))
				if (titleAbrev is None):
					short = str(alert.get('pluginId'))
					#print('Unknown alert: ' + short + ' ' + alert.get('alert'))
					print('`' + str(alert.get('pluginId')) + '\': [\'' + alert.get('alert') + '\', \'TBA\'], \\')
				else:
					short = titleAbrev[1]
				aDict = alertsPerUrl.get(urlSummary, {'pass' : set([]), 'fail' : set([]), 'ignore' : set([]), 'other' : set([])})
				added = False
				for rule in rules:
					if (rule[0] in urlSummary and rule[1] == short):
						aDict[rule[2]].add(short)
						# Counts per alert
						if (rule[2] == 'pass'):
							alertPassCount[short] = alertPassCount.get(short, 0) + 1
						elif (rule[2] == 'fail'):
							alertFailCount[short] = alertFailCount.get(short, 0) + 1
						elif (rule[2] == 'ignore'):
							alertIgnoreCount[short] = alertIgnoreCount.get(short, 0) + 1
						added = True
						break
				if (not added):
					aDict['other'].add(short)
					alertOtherCount[short] = alertOtherCount.get(short, 0) + 1
				alertsPerUrl[urlSummary] = aDict
				plugins.add(alert.get('alert'))
			uniqueUrls.add(url)
		offset += page
		alerts = zap.core.alerts('', offset, page)
	
	#for key, value in alertsPerUrl.iteritems():
	#	print key, value

	# Generate report file
	reportFile = open('report.html', 'w')
	reportFile.write("<html>\n")
	reportFile.write("  <head>\n")
	reportFile.write("    <title>ZAP Wavsep Report</title>\n")
	reportFile.write("    <!--Load the AJAX API-->\n")
	reportFile.write("    <script type=\"text/javascript\" src=\"https://www.google.com/jsapi\"></script>\n")
	reportFile.write("  </head>\n")
	reportFile.write("<body>\n")

	reportFile.write("<h1><img src=\"https://raw.githubusercontent.com/zaproxy/zaproxy/main/zap/src/main/resources/resource/zap64x64.png\" align=\"middle\">OWASP ZAP wavsep results</h1>\n")
	reportFile.write("Generated: " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M") + "\n")

	topResults = []
	thisTop = ['', 0, 0]

	groupResults = []
	thisGroup = ['', 0, 0]
	totalPass = 0
	totalFail = 0

	# Calculate the top level scores
	for key, value in sorted(alertsPerUrl.items()):
		top = key.split(' : ')[1]
		if ('-' in top):
			top = top.split('-')[0] + '-' + top.split('-')[1]
		
		if (top != thisTop[0]):
			thisTop = [top, 0, 0]	# top, pass, fail
			topResults.append(thisTop)
		if (len(value.get('pass')) > 0):
			thisTop[1] += 1
		elif (len(value.get('fail')) > 0):
			thisTop[2] += 1
		elif ('FalsePositive' in key):
			thisTop[1] += 1
		else:
			thisTop[2] += 1
		
	# Calculate the group scores
	for key, value in sorted(alertsPerUrl.items()):
		group = key.split(' : ')[1]
		if (group != thisGroup[0]):
			thisGroup = [group, 0, 0]	# group, pass, fail
			groupResults.append(thisGroup)
		if (len(value.get('pass')) > 0):
			totalPass += 1
			thisGroup[1] += 1
		elif (len(value.get('fail')) > 0):
			totalFail += 1
			thisGroup[2] += 1
		elif ('FalsePositive' in key):
			totalPass += 1
			thisGroup[1] += 1
		else:
			totalFail += 1
			thisGroup[2] += 1

	# Output the summary
	scale=8
	reportFile.write("<h3>Total Score</h3>\n")
	reportFile.write("<font style=\"BACKGROUND-COLOR: GREEN\">")
	for i in range (int(totalPass/scale)):
		reportFile.write("&nbsp;")
	reportFile.write("</font>")
	reportFile.write("<font style=\"BACKGROUND-COLOR: RED\">")
	for i in range (int(totalFail/scale)):
		reportFile.write("&nbsp;")
	reportFile.write("</font>")
	total = 100 * totalPass / (totalPass + totalFail)
	reportFile.write("{:.2f}%<br/><br/>\n".format(total))

	reportFile.write('ZAP Version: ' + zapVersion + '<br/>\n')
	reportFile.write('URLs found: ' + str(len(uniqueUrls)))

	# Output the top level table
	reportFile.write("<h3>Top Level Scores</h3>\n")
	reportFile.write("<table border=\"1\">\n")
	reportFile.write("<tr><th>Top Level</th><th>Pass</th><th>Fail</th><th>Score</th><th>Chart</th></tr>\n")

	scale=6
	for topResult in topResults:
	    #print "%s Pass: %i Fail: %i Score: %i\%" % (topResult[0], topResult[1], topResult[2], (100*topResult[1]/topResult[1]+topResult[2]))
		reportFile.write("<tr>")
		reportFile.write("<td>{0}</td>".format(html.escape(topResult[0])))
		reportFile.write("<td align=\"right\">" + str(topResult[1]) + "</td>")
		reportFile.write("<td align=\"right\">" + str(topResult[2]) + "</td>")
		score = 100 * topResult[1] / (topResult[1] + topResult[2])
		reportFile.write("<td align=\"right\">{:.2f}%</td>".format(score))
		reportFile.write("<td>")
		reportFile.write("<font style=\"BACKGROUND-COLOR: GREEN\">")
		for i in range (int(topResult[1]/scale)):
			reportFile.write("&nbsp;")
		reportFile.write("</font>")
		reportFile.write("<font style=\"BACKGROUND-COLOR: RED\">")
		for i in range (int(topResult[2]/scale)):
			reportFile.write("&nbsp;")
		reportFile.write("</font>")
		reportFile.write("</td>")
		reportFile.write("</tr>\n")

	reportFile.write("</table><br/>\n")

	reportFile.write("<h3>Alerts</h3>\n")
	reportFile.write("<table border=\"1\">\n")
	reportFile.write("<tr><th>Alert</th><th>Description</th><th>Pass</th><th>Fail</th><th>Ignore</th><th>Other</th></tr>\n")

	#for key, value in abbrev.items():
	#for (k, v) in sorted(list(abbrev.items()), key=lambda k_v: k_v[1]):
	for k, v in sorted(abbrev.items()):
		reportFile.write("<tr>")
		reportFile.write("<td>" + v[1] + "</td>")
		reportFile.write("<td><a name=\"" + v[1] + "\" href=\"https://www.zaproxy.org/docs/alerts/" + k + "/\">" + v[0] + "</a></td>")
		reportFile.write("<td>" + str(alertPassCount.get(v[1], 0)) +"&nbsp;</td>")
		reportFile.write("<td>" + str(alertFailCount.get(v[1], 0)) +"&nbsp;</td>")
		reportFile.write("<td>" + str(alertIgnoreCount.get(v[1], 0)) +"&nbsp;</td>")
		reportFile.write("<td>" + str(alertOtherCount.get(v[1], 0)) +"&nbsp;</td>")
		reportFile.write("</tr>\n")

	reportFile.write("</table><br/>\n")

	# Output the group table
	reportFile.write("<h3>Group Scores</h3>\n")
	reportFile.write("<table border=\"1\">\n")
	reportFile.write("<tr><th>Group</th><th>Pass</th><th>Fail</th><th>Score</th><th>Chart</th></tr>\n")

	scale=4
	for groupResult in groupResults:
		#print "%s Pass: %i Fail: %i Score: %i\%" % (groupResult[0], groupResult[1], groupResult[2], (100*groupResult[1]/groupResult[1]+groupResult[2]))
		reportFile.write("<tr>")
		reportFile.write("<td>{0}</td>".format(html.escape(groupResult[0])))
		reportFile.write("<td align=\"right\">" + str(groupResult[1]) + "</td>")
		reportFile.write("<td align=\"right\">" + str(groupResult[2]) + "</td>")
		score = 100 * groupResult[1] / (groupResult[1] + groupResult[2])
		reportFile.write("<td align=\"right\">{:.2f}%</td>".format(score))
		reportFile.write("<td>")
		reportFile.write("<font style=\"BACKGROUND-COLOR: GREEN\">")
		for i in range (int(groupResult[1]/scale)):
			reportFile.write("&nbsp;")
		reportFile.write("</font>")
		reportFile.write("<font style=\"BACKGROUND-COLOR: RED\">")
		for i in range (int(groupResult[2]/scale)):
			reportFile.write("&nbsp;")
		reportFile.write("</font>")
		reportFile.write("</td>")
		reportFile.write("</tr>\n")

	reportFile.write("</table><br/>\n")

	# Output the detail table
	reportFile.write("<h3>Detailed Results</h3>\n")
	reportFile.write("<table border=\"1\">\n")
	reportFile.write("<tr><th>Page</th><th>Result</th><th>Pass</th><th>Fail</th><th>Ignore</th><th>Other</th></tr>\n")

	for key, value in sorted(alertsPerUrl.items()):
		reportFile.write("<tr>")
		keyArray = key.split(':')
		if (len(keyArray) == 4):
			reportFile.write("<td>{0}</td>".format(html.escape(keyArray[0] + keyArray[2] + keyArray[3])))
		else:
			reportFile.write("<td>{0}</td>".format(html.escape(keyArray[0] + keyArray[2])))
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
	
	#for key, value in sorted(alertsPerUrl.iteritems()):
	#    print "%s: %s" % (key, value)

	#print ''	
	
	print('')
	print('ZAP ' + zapVersion)
	print('Got ' + str(totalAlerts) + ' alerts')
	print('Got ' + str(len(uniqueUrls)) + ' unique urls')
	print('Took ' + time)
	print('Score ' + str(int(total)))

if __name__ == "__main__":
	main(sys.argv[1:])   

