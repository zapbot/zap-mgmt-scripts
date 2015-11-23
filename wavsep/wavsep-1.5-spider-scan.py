#!/usr/bin/env python
   
import time, sys, getopt
from pprint import pprint
from zapv2 import ZAPv2
   
def main(argv):
   # -------------------------------------------------------------------------
   # Default Configurations - use -z/-zap and -w/-wavsep for different IP addrs
   # -------------------------------------------------------------------------
   wavsepHostIp = '172.17.0.2'
   zapHostIp = '172.17.0.3'
   
   try:
      opts, args = getopt.getopt(argv,"hz:w:",["zap=","wavsep="])
   except getopt.GetoptError:
      print 'test.py -z <ZAPipaddr> -w <WAVSEPipaddr>'
      sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
         print 'test.py -z <ZAPipaddr> -w <WAVSEPipaddr>'
         sys.exit()
      elif opt in ("-z", "--zap"):
         zapHostIp = arg
      elif opt in ("-w", "--wavsep"):
         wavsepHostIp = arg
   print 'zap is', zapHostIp
   print 'wavsep is ', wavsepHostIp
   
   # change this IP according to your environment
   
   target = 'http://' + wavsepHostIp + ':8080/wavsep'
   
   passiveIndexPage = target + '/index-passive.jsp'
   passiveInformationLeakage1 = target + '/passive/info/info-app-stack-trace.jsp'
   passiveInformationleakage2 = target + '/passive/info/info-server-stack-trace.jsp'
   passiveInformationleakage3 = target + '/passive/info/info-cookie-no-httponly.jsp'
   passiveSession1 = target + '/passive/session/session-password-autocomplete.jsp'
   passiveSession2 = target + '/passive/session/weak-authentication-basic.jsp'
   activeIndexPage = target + '/index-active.jsp'
   
   zap = ZAPv2()
   
   # change this IP according to your environment
   
   zap = ZAPv2(proxies={'http': 'http://' + zapHostIp + ':8090', 'https': 'http://' + zapHostIp + ':8090'})
   
   # -------------------------------------------------------------------------
   # PASSIVE MODE
   # open passive web pages, let zap detect vulnerabilities passively
   # -------------------------------------------------------------------------
   zap.urlopen(passiveIndexPage)
   zap.urlopen(passiveInformationLeakage1)
   zap.urlopen(passiveInformationleakage2)
   zap.urlopen(passiveInformationleakage3)
   zap.urlopen(passiveSession1)
   zap.urlopen(passiveSession2)
   time.sleep(2)
   
   # -------------------------------------------------------------------------
   # ACTIVE MODE
   # open active web pages, trigger spider and activeScan
   # -------------------------------------------------------------------------
   zap.urlopen(target)
   time.sleep(2)
   zap.urlopen(activeIndexPage)
   time.sleep(2)

   print 'Spider started'
   zap.spider.scan(activeIndexPage)
   # Give the Spider a chance to start
   time.sleep(5)
   while (int(zap.spider.status()) < 100):
       print 'Spider progress %: ' + zap.spider.status()
       time.sleep(5)

   print 'Spider completed'

   time.sleep(5)

   print 'Scanning target %s' % target
   zap.ascan.scan(target)
   while (int(zap.ascan.status()) < 100):
       print 'Scan progress %: ' + zap.ascan.status()
       time.sleep(5)
       
   print 'Scan completed'

if __name__ == "__main__":
   main(sys.argv[1:])   
