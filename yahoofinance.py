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

def output(bot, out):
    if bot is not None:
        bot.say(out)
    else:
        print out

def getTicker(name, gimme=False):
    url = "http://d.yimg.com/autoc.finance.yahoo.com/autoc?query={0}&callback=YAHOO.Finance.SymbolSuggest.ssCallback".format(name)
    response = requests.get(url)
    html = response.content.lstrip("YAHOO.Finance.SymbolSuggest.ssCallback(").rstrip(")")
    data = json.loads(html)
    result = data.get('ResultSet').get('Result')
    results = []
    sortOrder = {}
    sortOrder['Index'] = 0
    sortOrder['Equity'] = 1
    sortOrder['Futures'] = 2
    sortOrder['ETF'] = 3

    if result:
        if gimme is True:
            for r in sorted(result, key=lambda x: sortOrder.get(x.get('typeDisp'), 999)):
                results.append([r.get('symbol'), r.get('name'), r.get('typeDisp')])

            return results       
        else:
            #try to find swedish stocks first
            for r in sorted(result, key=lambda x: sortOrder.get(x.get('typeDisp'), 999)):
                if r.get('exch') == 'STO':
                    return r.get('symbol'), r.get('name')

            return result[0].get('symbol'), result[0].get('name')
    else:
        return None, None




def findTickers(bot, ticker, maxresult=5):
    res = getTicker(ticker, gimme=True)
    if res[0] is None:
        out = 'Found no tickers'
        output(bot, out)
        return
    out = 'Found {0} tickers. Max result is {1}.'.format(len(res), maxresult)
    output(bot, out)
    count = 0
    for r in res:
        if count == maxresult:
            break
        out = r[1]
        if formatting:
            out = formatting.bold(out)

        out += ' ({0})'.format(r[0])
        out += ' of type {0}'.format(r[2])

        output(bot, out)
        count += 1


def getCurrentQuote(ticker):
    url = 'https://query.yahooapis.com/v1/public/yql?'
    q = {
        'q': 'select * from yahoo.finance.quotes where symbol in ("{0}")'.format(ticker),
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
        change = quote.get('Change')
        if change:
            change = float(change)
        else:
            change = 0.0
        o = latest - change
        percentage = (latest / o) - 1.0
        percentage *= 100.0
        currency = quote.get('Currency')
    else:
        percentage = None
        currency = None

    return latest, percentage, currency


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



def formatPercentage(percentage):
    pf = '{0:.2f}%'.format(percentage)

    if percentage > 0:
        pf = '+' + pf

    if formatting:
        if percentage < 0:
            pf = formatting.color(pf, formatting.colors.RED)
        elif percentage > 0:
            pf = formatting.color(pf, formatting.colors.GREEN)

    pf = '(' + pf + ')'    

    return pf

def formatName(name):
    out = '{0} '.format(name)
    if formatting:
        out = formatting.bold(out)
    return out


def runMe(bot, tickers, arg):
    if not tickers:
        output(bot, "No arguments passed")
        return

    tickers = tickers.split(',')
    totalPercentage = []

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

    for ticker in tickers:

        if arg is not None:


            ticker, name = getTicker(ticker)
            latest, old, percentage = getQuoteForRange(ticker, startDateString, endDateString)

            if percentage:
                totalPercentage.append(percentage)
            else:
                percentage = 0.0

            out = formatName(name)
            out += "({4}) period quote: startdate: {0}; quote: {1}, enddate {2}; quote {3}. change: ".format(startDateString, old, endDateString, latest, ticker)
            out += formatPercentage(percentage)
            output(bot, out)         

        else:
            ticker, name = getTicker(ticker)
            latest, percentage, currency = getCurrentQuote(ticker)
            if percentage:
                totalPercentage.append(percentage)
            else:
                percentage = 0.0
            
            out = formatName(name)
            out += '({1}) quote is: {0} {2} '.format(latest, ticker, currency)
            out += formatPercentage(percentage)
            
            output(bot, out)

    #if len(totalPercentage) > 1:
    #    out = 'Average change: {0:.2f}%'.format(sum(totalPercentage)/float(len(totalPercentage)))
    #    output(bot, out)

try:
    @module.commands('yf')
    def yf(bot, trigger):
        args = trigger.group(2)
        splitargs = args.split(' ')

        if re.search('\d+d|\d+m|\d+y', splitargs[-1]):
            arg = splitargs[-1]
            tickers = ' '.join(splitargs[:-1])
        else:
            arg = None
            tickers = ' '.join(splitargs)
        
        #tickers = trigger.group(3)
        #arg = trigger.group(4)
        runMe(bot, tickers, arg)

    @module.commands('eursek')
    def eursek(bot, trigger):    
        tickers = 'eursek=x'
        arg = None
        runMe(bot, tickers, arg)

    @module.commands('usdsek')
    def usdsek(bot, trigger):    
        tickers = 'usdsek=x'
        arg = None
        runMe(bot, tickers, arg)

    @module.commands('eurusd')
    def eurusd(bot, trigger):    
        tickers = 'eurusd=x'
        arg = None
        runMe(bot, tickers, arg)

    @module.commands('yfind')
    def yfind(bot, trigger):    
        ticker = trigger.group(2)
        findTickers(bot, ticker)


except:
    #module not available
    pass

def test():
    #tickers = 'PRIC-B.ST'
    #tickers = 'G5EN.ST'
    #tickers = 'G5EN.ST,PRIC-B.ST'
    #tickers = 'apple,pricer'
    tickers = 'microsoft,fingerprint,pricer'
    #tickers = 'pricer,bahnhof'
    tickers = 'cur'

    #arg = '3m'
    #arg = '1y'
    #arg = yt'15d'
    arg = None
    #arg = '3d'

    runMe(None, tickers, arg)

def test2():
    da = 'omxs30'
    res = findTickers(None, da, maxresult=20)

if __name__ == "__main__":
    test()
    #test2()
