#!/usr/bin/env python
   
import time, sys, getopt
from pprint import pprint
from zapv2 import ZAPv2
   
def main(argv):
   # -------------------------------------------------------------------------
   # Default Configurations - use -z/-zap and -w/-vulnerableApp for different IP addrs
   # -------------------------------------------------------------------------
   vulnerableAppHostIp = '172.17.0.2'
   zapHostIp = '172.17.0.3'
   ajax = False
   policy = None
   
   try:
      opts, args = getopt.getopt(argv,"haz:w:p:",["zap=","wavsep=","ajax","policy="])
   except getopt.GetoptError:
      print('test.py -z <ZAPipaddr> -w <VulnerableAppipaddr>')
      sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
         print('test.py -z <ZAPipaddr> -w <VulnerableAppipaddr> -p <scanPolicy> -a')
         sys.exit()
      elif opt in ("-z", "--zap"):
         zapHostIp = arg
      elif opt in ("-w", "--vulnerableApp"):
         vulnerableAppHostIp = arg
      elif opt in ("-a", "--ajax"):
         ajax = True
      elif opt in ("-p", "--policy"):
         policy = arg
   print('zap is', zapHostIp)
   print('vulnerableApp is ', vulnerableAppHostIp)
   
   # change this IP according to your environment
   
   target = 'http://' + vulnerableAppHostIp + ':9090/'

   print('Target %s' % target)
   print('ZAP %s' % zapHostIp)
   
   # change this IP according to your environment
   
   zap = ZAPv2(proxies={'http': 'http://' + zapHostIp + ':8090', 'https': 'http://' + zapHostIp + ':8090'})
   
   zap.urlopen(target)
   time.sleep(2)
   
   print('Spidering %s' % target)
   zap.spider.scan(target)
   # Give the Spider a chance to start
   time.sleep(5)
   while (int(zap.spider.status()) < 100):
       print('Spider progress %: ' + zap.spider.status())
       time.sleep(5)

   print('Spider completed')
   time.sleep(5)

   if (ajax):
       # Run the Ajax Spider
       print('Ajax Spidering %s' % target)
       zap.ajaxSpider.scan(target)
       # Give the Ajax Spider a chance to start
       time.sleep(5)
       while (zap.ajaxSpider.status == 'running'):
           print('Ajax spider still running, results: ' + zap.ajaxSpider.number_of_results)
           time.sleep(5)
       print('Ajax Spider completed')
       time.sleep(5)

   # Create the policy

   print('Scanning target %s' % target)
   if (policy):
       zap.ascan.scan(target, scanpolicyname=policy)
   else:
       zap.ascan.scan(target)
   # Give the Scanner a chance to start
   time.sleep(5)
   while (int(zap.ascan.status()) < 100):
       print('Scan progress %: ' + zap.ascan.status())
       time.sleep(5)
       
   print('Scan completed')

if __name__ == "__main__":
   main(sys.argv[1:])   
