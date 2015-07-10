import requests
import urllib
import sys
from datetime import datetime
from datetime import timedelta
import re
import json
from willie import module

#tickers = 'PRIC-B.ST'
#tickers = 'G5EN.ST'
#tickers = 'G5EN.ST,PRIC-B.ST'
#tickers = 'apple,pricer'

#arg = '3m'
#arg = '1y'
#arg = '15d'
#arg = None

def getTicker(name):
    url = "http://d.yimg.com/autoc.finance.yahoo.com/autoc?query={0}&callback=YAHOO.Finance.SymbolSuggest.ssCallback".format(name)
    response = requests.get(url)
    #print response.content
    html = response.content.lstrip("YAHOO.Finance.SymbolSuggest.ssCallback(").rstrip(")")
    data = json.loads(html)
    result = data.get('ResultSet').get('Result')
    if result:
        #try to find swedish stocks first
        for r in result:
            if r.get('exch') == 'STO':
                return r.get('symbol')

        return result[0].get('symbol')
    else:
        return None


def getCurrentQuote(ticker):
    url = 'https://query.yahooapis.com/v1/public/yql?'
    q = {
        'q': 'select * from yahoo.finance.quote where symbol in ("{0}")'.format(ticker),
        'format': 'json',
        'env': 'store://datatables.org/alltableswithkeys'
    }

    query = url + urllib.urlencode(q)
    result = requests.get(query)
    dic = json.loads(result.content)
    quote = dic.get('query').get('results').get('quote')
    if type(quote)  == list:
        return None, None

    latest = quote.get('LastTradePriceOnly')
    if latest:
        percentage = float(quote.get('Change'))
    else:
        percentage = None

    return latest, percentage


def getQuoteForRange(ticker, start, end):
    url = 'https://query.yahooapis.com/v1/public/yql?'
    q = {
        'q': 'select * from yahoo.finance.historicaldata where symbol = "{0}" and startDate = "{1}" and endDate = "{2}"'.format(ticker, start, end),
        'format': 'json',
        'env': 'store://datatables.org/alltableswithkeys'
    }
    query = url + urllib.urlencode(q)
    result = requests.get(query)
    dic = json.loads(result.content)
    results = dic.get('query').get('results')
    if results:
        quoteList = results.get('quote')

        if len(quoteList) > 1:
            latest = float(quoteList[0].get('Close'))
            old = float(quoteList[-1].get('Close'))    

            percentage = (latest - old) / old
            percentage *= 100.0

        return latest, old, percentage
    else:
        return None, None, None

@module.commands('yftest')
def yf(bot, trigger):  
#def test(arg, tickers):

    
    tickers = trigger.group(3)
    arg = trigger.group(4)
    if not tickers:
        bot.say("No arguments passed")
        #pass
        return

    tickers = tickers.split(',')
    totalPercentage = []

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


            latest, old, percentage = getQuoteForRange(ticker, startDateString, endDateString)
            if not latest:
                ticker = getTicker(ticker)
                latest, old, percentage = getQuoteForRange(ticker, startDateString, endDateString)
            if percentage:
                totalPercentage.append(percentage)
            else:
                percentage = 0.0
            out = "{0} period quote: startdate: {1}; quote: {2}, enddate {3}; quote {4}. change: ({5:.2f}%)".format(ticker, startDateString, old, endDateString, latest, percentage)
            #print out
            bot.say(out)
            
            
            

        else:
            latest, percentage = getCurrentQuote(ticker)
            if not latest:
                ticker = getTicker(ticker)
                latest, percentage = getCurrentQuote(ticker)
            if percentage:
                totalPercentage.append(percentage)

            out = 'Latest {0} quote is: {1} ({2}%)'.format(ticker, latest, percentage)
            #print out
            bot.say(out)

    if len(totalPercentage) > 1:
        out = 'Average change: {0:.2f}%'.format(sum(totalPercentage)/float(len(totalPercentage)))
        #print out
        bot.say(out)

#test(arg, tickers)
