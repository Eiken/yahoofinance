import requests
import urllib
import sys
from datetime import datetime
from datetime import timedelta
import re
import json

try:
    from willie import module
    from willie import formatting
except:
    module = None
    formatting = None


def getTicker(name):
    url = "http://d.yimg.com/autoc.finance.yahoo.com/autoc?query={0}&callback=YAHOO.Finance.SymbolSuggest.ssCallback".format(name)
    response = requests.get(url)
    html = response.content.lstrip("YAHOO.Finance.SymbolSuggest.ssCallback(").rstrip(")")
    data = json.loads(html)
    result = data.get('ResultSet').get('Result')
    if result:
        #try to find swedish stocks first
        for r in result:
            if r.get('exch') == 'STO':
                return r.get('symbol'), r.get('name')

        return result[0].get('symbol'), result[0].get('name')
    else:
        return None, None


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
        latest = float(latest)
        change = float(quote.get('Change'))
        o = latest - change
        percentage = (latest / o) - 1.0
        percentage *= 100.0
        
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

        if not type(quoteList) is dict:
            latest = float(quoteList[0].get('Close'))
            old = float(quoteList[-1].get('Close'))    

            percentage = (latest - old) / old
            percentage *= 100.0

            return latest, old, percentage
    return None, None, None

def output(bot, out):
    if bot is not None:
        bot.say(out)
    else:
        print out

def runMe(bot, tickers, arg):
    if not tickers:
        output(bot, "No arguments passed")
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


            ticker, name = getTicker(ticker)
            latest, old, percentage = getQuoteForRange(ticker, startDateString, endDateString)

            if percentage:
                totalPercentage.append(percentage)
            else:
                percentage = 0.0

            out = '{0} '.format(name)
            if formatting:
                out = formatting.bold(out)
            out += "({5}) period quote: startdate: {0}; quote: {1}, enddate {2}; quote {3}. change: ({4:.2f}%)".format(startDateString, old, endDateString, latest, percentage, ticker)
            output(bot, out)         

        else:
            ticker, name = getTicker(ticker)
            latest, percentage = getCurrentQuote(ticker)
            if percentage:
                totalPercentage.append(percentage)
            else:
                percentage = 0.0
            out = '{0} '.format(name)
            if formatting:
                out = formatting.bold(out)
            out += '({2}) quote is: {0} ({1:.2f}%)'.format(latest, percentage, ticker)
            output(bot, out)

    #if len(totalPercentage) > 1:
    #    out = 'Average change: {0:.2f}%'.format(sum(totalPercentage)/float(len(totalPercentage)))
    #    output(bot, out)

try:
    @module.commands('yf')
    def yf(bot, trigger):    
        tickers = trigger.group(3)
        arg = trigger.group(4)
        runMe(bot, tickers, arg)
except:
    #module not available
    pass

def test():
    #tickers = 'PRIC-B.ST'
    #tickers = 'G5EN.ST'
    #tickers = 'G5EN.ST,PRIC-B.ST'
    tickers = 'apple,pricer'
    tickers = 'microsoft,fingerprint,pricer'
    tickers = 'pricer,bahnhof'

    #arg = '3m'
    #arg = '1y'
    #arg = '15d'
    arg = None
    #arg = '3d'

    runMe(None, tickers, arg)

if __name__ == "__main__":
    test()
