#!/usr/bin/python

import sys
import os
import requests, json
from willie import module

# Print difference
@module.commands('yahoo', 'yahoofinance', 'yf')
def ig(bot, trigger):

   ticker = trigger.group(2)

   # Get latest close from Yahoo Finance
   r = requests.get('http://download.finance.yahoo.com/d/quotes.csv?s=' + ticker + '&f=l1nc')
   try:
      x_close = float(r.text.split(',')[0][:7])
   except:
      x_close = 0.000

   try:
      x_change = r.text.split(',')[2][1:-2].split(' - ')[1]
   except:
      x_change = '000%'

   if x_close > 0:
      longname = r.text.split(',')[1][1:-1]
      bot.say("Latest " + str(longname) + " quote is: " + str(x_close) + " (" + str(x_change) + ")")
   else:
      bot.say("Invalid ticker: " + ticker.upper())
