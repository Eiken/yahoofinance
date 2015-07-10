import requests
import urllib
from datetime import datetime
from datetime import timedelta
import re
import json
from willie import module

#tickers = 'PRIC-B.ST'
#tickers = 'G5EN.ST'
#tickers = 'G5EN.ST,PRIC-B.ST'

#arg = '3m'
#arg = '1y'
#arg = '15d'
#arg = None

@module.commands('yftest')
def yf(bot, trigger):  
#def test(arg, tickers):
    url = 'https://query.yahooapis.com/v1/public/yql?'
    
    tickers = trigger.group(3)
    arg = trigger.group(4)
    if not tickers:
        bot.say("No arguments passed")
        #pass
        return

    tickers = tickers.split(',')
    totalPercentage = 0.0    

    for ticker in tickers:

        if arg is not None:
            days = re.findall('(\d+)(d)', arg) 
            months = re.findall('(\d+)(m)', arg) 
            years = re.findall('(\d+)(y)', arg) 

            endDate = datetime.now()

            if years:
                years = int(years[0][0])
            else:
                years = 0

            if months:
                months = int(months[0][0])
            else:
                months = 0

            if days:
                days = int(days[0][0])
            else:
                days = 0

            timeDelta = timedelta(days=days + months * 30 + years * 365)

            startDate = endDate - timeDelta

            startDateString = startDate.strftime("%Y-%m-%d")
            endDateString = endDate.strftime("%Y-%m-%d")


            q = {
                'q': 'select * from yahoo.finance.historicaldata where symbol = "{0}" and startDate = "{1}" and endDate = "{2}"'.format(ticker, startDateString, endDateString),
                'format': 'json',
                'env': 'store://datatables.org/alltableswithkeys'
            }
            query = url + urllib.urlencode(q)
            result = requests.get(query)
            dic = json.loads(result.content)
            quoteList = dic.get('query').get('results').get('quote')

            if len(quoteList) > 1:
                latest = float(quoteList[0].get('Close'))
                old = float(quoteList[-1].get('Close'))    

                percentage = (latest - old) / old
                percentage *= 100.0

                totalPercentage += percentage


                out = "{0} period quote: startdate: {1}; quote: {2}, enddate {3}; quote {4}. change: ({5:.2f}%)".format(ticker, startDateString, old, endDateString, latest, percentage)
                #print out
                bot.say(out)
            
            
            

        else:
            q = {
                'q': 'select * from yahoo.finance.quote where symbol in ("{0}")'.format(ticker),
                'format': 'json',
                'env': 'store://datatables.org/alltableswithkeys'
            }

            query = url + urllib.urlencode(q)
            result = requests.get(query)
            dic = json.loads(result.content)
            quote = dic.get('query').get('results').get('quote')
            latest = quote.get('LastTradePriceOnly')
            percentage = float(quote.get('Change'))
            totalPercentage += percentage

            out = 'Latest {0} quote is: {1} ({2}%)'.format(ticker, latest, percentage)
            #print out
            bot.say(out)

    numTickers = len(tickers)
    if numTickers > 1:
        #print numTickers
        out = 'Average change: {0:.2f}%'.format(totalPercentage/float(numTickers))
        #print out
        bot.say(out)

#test(arg, tickers)
