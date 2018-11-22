#!/usr/bin/env python
# This script runs the ZAP traditional and ajax spiders against wivet
# Wivet can be installed manually or via the docker image https://hub.docker.com/r/andresriancho/wivet/
# eg using:
#		docker pull andresriancho/wivet
#		docker run -i -p 443:443 andresriancho/wivet
#
# The following options should be used when running ZAP:
#		ajaxSpider.clickDefaultElems=False
# these will be set by API calls in the future (when supported).
# Other ajaxSpider options will also affect the results - please let us know if any others improve the score :)
#
# If running ZAP via docker use a command like:
# 		docker run -u zap -p 8090:8090 -d owasp/zap2docker-weekly zap-x.sh \
#			-daemon -port 8090 -host 0.0.0.0 -config api.disablekey=true \
#			-config ajaxSpider.clickDefaultElems=False
# 
# The script assumes wivet is reset after each test - otherwise you'll need to work out which result
# you're really interested in - right now the script just picks the best result
   
import time, sys, getopt, re
from pprint import pprint
from zapv2 import ZAPv2
   
def main(argv):
   # -------------------------------------------------------------------------
   # Default Configurations - use -z/-zap and -w/-wivet for different IP addrs
   # -------------------------------------------------------------------------
   wivitHostIp = '172.17.0.2'
   zapHostIp = '172.17.0.3'
   name = 'wivet-default'
   
   try:
      opts, args = getopt.getopt(argv,"hn:z:w:",["zap=","wivet=","name="])
   except getopt.GetoptError:
      print('test.py -z <ZAPipaddr> -w <WIVITipaddr>')
      sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
         print('test.py -z <ZAPipaddr> -w <WIVITipaddr>')
         sys.exit()
      elif opt in ("-n", "--name"):
         name = arg
      elif opt in ("-z", "--zap"):
         zapHostIp = arg
      elif opt in ("-w", "--wivit"):
         wivitHostIp = arg
   print('zap is', zapHostIp)
   print('wivit is ', wivitHostIp)
   
   # change this IP according to your environment
   
   target = 'http://' + wivitHostIp + '/'
   
   zap = ZAPv2(proxies={'http': 'http://' + zapHostIp + ':8090', 'https': 'http://' + zapHostIp + ':8090'})
   zapVersion = zap.core.version
   
   # Access the top page
   zap.urlopen(target)
   time.sleep(2)
   
   # Exclude pages out of scope and the logout one
   zap.spider.exclude_from_scan(target + 'offscanpages.*')
   zap.spider.exclude_from_scan(target + 'logout.*')

   zap.spider.scan(target)
   print('Spider started')
   # Give the Spider a chance to start
   time.sleep(5)
   while (int(zap.spider.status()) < 100):
       print('Spider progress %: ' + zap.spider.status())
       time.sleep(5)

   print('Spider completed')

   time.sleep(5)

   # Just interested in the time the ajax spider takes
   start = time.time()

   zap.ajaxSpider.scan(target)
   print('Ajax Spider started')
   # Give the Ajax Spider a chance to start
   time.sleep(5)
   while (zap.ajaxSpider.status == 'running'):
       print('Ajax spider still running, results: ' + zap.ajaxSpider.number_of_results)
       time.sleep(5)

   print('Ajax Spider completed')

   end = time.time()
   print('ZAP: ' + zapVersion)
   print('Time: ' + time.strftime('%H:%M:%S', time.gmtime(end - start)))
   print('Pages: ' + zap.ajaxSpider.number_of_results)

   # parse and extract score
   stats = zap.urlopen(target + 'offscanpages/statistics.php')
   scores = re.findall('Coverage: \%(.+?)\)', stats)
   top_score = 0
   for score in scores:
      # This assumes wivet is reset after each test
      if int(score) > top_score:
         top_score = int(score)
         # find and extract the right url for the results
         backstop = stats.find('Coverage: %' + score + ')')
         frontstop = stats.rfind('statistics', 0, backstop)
         backstop = stats.find('"', frontstop)
         # print('Front: ' + str(frontstop) + ' Back: ' + str(backstop))
         results = stats[frontstop:backstop]
   print('Score: ' + str(top_score))

   # Output the results page
   res = zap.urlopen(target + 'offscanpages/' + results)
   resfile = open(name + '.html', 'w')
   # fix the style page and remove the BACK button (which wont work in isolation)
   res = res.replace('/style.css', 'wivet-style.css').replace('<br/><a href=\'statistics.php\'>BACK</a><br/>', '')
   resfile.write(res)
   resfile.close()

   # Output the style page
   style = zap.urlopen(target + 'style.css')
   stylefile = open('wivet-style.css', 'w')
   stylefile.write(style)
   stylefile.close()

if __name__ == "__main__":
   main(sys.argv[1:])   
