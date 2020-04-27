from local_settings import *
import twitter
import random

total_ok = 0
total_not = 0
lines = []

# Read file in
with open('tweets.txt', 'r') as f:
  for l in f:
    if len(l) > 280:
      total_not += 1
      print('Line too long: ' + str(len(l)) + ': ' + l)
    elif len(l) > 0:
      total_ok += 1
      lines.append(l)

# print('Total can tweet: ' + str(total_ok))
# print('Total cant tweet: ' + str(total_not))
# print('')

api = twitter.Api(consumer_key = CONSUMER_KEY,
                  consumer_secret = CONSUMER_SECRET,
                  access_token_key = ACCESS_TOKEN,
                  access_token_secret = ACCESS_TOKEN_SECRET)

tw = random.choice(lines)
print('Tweeting: ' + tw)

api.PostUpdate(tw)