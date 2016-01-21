#!/usr/bin/env python
# Time how long it takes to backup and recover the current ZAP session
# with a basic sanity check (counting the number of messages before and after recovery)
   
import datetime, time, sys, getopt
from pprint import pprint
from zapv2 import ZAPv2
   
def main(argv):
   # -------------------------------------------------------------------------
   # Default Configurations - use -z/-zap and -w/-wavsep for different IP addrs
   # -------------------------------------------------------------------------
   zapHostPort = 'http://localhost:8090'
   
   try:
      opts, args = getopt.getopt(argv,"z:",["zap="])
   except getopt.GetoptError:
      # TODO
      print 'zap-backup-test.py -z <ZAPhostPort>'
      sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
         print 'zap-backup-test.py -z <ZAPhostPort>'
         sys.exit()
      elif opt in ("-z", "--zap"):
         zapHostPort = arg
   
   zap = ZAPv2(proxies={'http': zapHostPort, 'https': zapHostPort})
   
   # Count number of messages
   old_count = zap.core.number_of_messages()
   print 'Initial msg count: %s' % old_count

   # Time backup
   start_time = time.time()
   zap.core.save_session(name='backup-test', overwrite='true')
   backup_time = (time.time() - start_time)
   print 'Backed up: %s' % str(time.strftime('%H:%M:%S', time.gmtime(int(backup_time))))

   # Time new session
   start_time = time.time()
   zap.core.new_session(name='backup-empty', overwrite='true')
   new_time = (time.time() - start_time)
   print 'New session: %s' % str(time.strftime('%H:%M:%S', time.gmtime(int(new_time))))

   # Sanity check new session
   new_count = zap.core.number_of_messages()
   if (new_count != '0'):
     print 'Unexpected empty count: %s' % new_count

   # Time restore
   start_time = time.time()
   zap.core.load_session(name='backup-test')
   rec_time = (time.time() - start_time)
   print 'Loaded: %s' % str(time.strftime('%H:%M:%S', time.gmtime(int(rec_time))))

   rec_count = zap.core.number_of_messages()
   if (old_count == rec_count):
     print 'PASS: counts match'
   else:
     print 'FAIL: Counts differ - original: %s recovered: %s' % old_count, new_count


if __name__ == "__main__":
   main(sys.argv[1:])   
