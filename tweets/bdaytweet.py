from local_settings import *
import twitter

api = twitter.Api(consumer_key = CONSUMER_KEY,
                  consumer_secret = CONSUMER_SECRET,
                  access_token_key = ACCESS_TOKEN,
                  access_token_secret = ACCESS_TOKEN_SECRET)

tw = 'Happy Birthday Zaproxy!  https://seclists.org/bugtraq/2010/Sep/38 Thank you to all of our contributors and supporters! #owasp #zaproxy'
print('Tweeting: ' + tw)

api.PostUpdate(tw)