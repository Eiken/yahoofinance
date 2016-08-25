#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
import urllib
import sys
from datetime import datetime
from datetime import timedelta
import re
import json

try:
    from sopel import module
    from sopel import formatting
except:
    module = None
    formatting = None
    #import traceback
    #traceback.print_exc(file=sys.stdout)

botten = None

def output(out):
    global botten
    if botten is not None:
        botten.say(out)
    else:
        print out

def getTicker(name, gimme=False):
    if not type(name) is unicode:
        name = name.decode('utf-8')
    name = name.replace(u'ö', u'o')
    name = name.replace(u'ä', u'a')
    name = name.replace(u'å', u'a')

    #url = u"http://d.yimg.com/autoc.finance.yahoo.com/autoc?query={0}&callback=YAHOO.Finance.SymbolSuggest.ssCallback".format(name)
    url = u"https://s.yimg.com/aq/autoc?query={0}&region=CA&lang=en-CA&callback=YAHOO.util.ScriptNodeDataSource.callbacks".format(name)

    try:
        response = requests.get(url)
    except requests.exceptions.RequestException as e:
        output("Failed to connect to yahoo")
        return None, None

    #html = response.content.lstrip("YAHOO.Finance.SymbolSuggest.ssCallback(").rstrip(")")
    html = response.content.lstrip("YAHOO.util.ScriptNodeDataSource.callbacks(").rstrip(");")
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




def findTickers(ticker, maxresult=5):
    res = getTicker(ticker, gimme=True)
    if res[0] is None:
        out = 'Found no tickers'
        output(out)
        return
    out = 'Found {0} tickers. Max result is {1}.'.format(len(res), maxresult)
    output(out)
    count = 0
    for r in res:
        if count == maxresult:
            break
        out = r[1]
        if formatting:
            out = formatting.bold(out)

        out += ' ({0})'.format(r[0])
        out += ' of type {0}'.format(r[2])

        output(out)
        count += 1

def getCurrentQuoteAlternative(ticker):
    url = 'http://finance.yahoo.com/webservice/v1/symbols/{0}/quote?'.format(ticker)
    q = {
        'format': 'json',
        'view': 'detail',
    }

    query = url + urllib.urlencode(q)
    headers = {
            "User-Agent": 
            "Mozilla/5.0 (Linux; Android 6.0; MotoE2(4G-LTE) Build/MPI24.65-39) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.81 Mobile Safari/537.36"
            }
    try:
        result = requests.get(query, headers=headers)
    except requests.exceptions.RequestException as e:
        output("Failed to connect to yahoo")
        return None, None, None

    dic = json.loads(result.content, strict=False)
    if dic is None:
        output("Failed to connect to yahoo")
        return None, None, None
    
    resources = dic.get('list').get('resources')
    resource = resources[0]
    quote = resource.get('resource').get('fields')

    latest = quote.get('price')
    if latest:
        latest = float(latest)
        change = quote.get('change')
        if change:
            change = float(change)
        else:
            change = 0.0
        o = latest - change
        percentage = (latest / o) - 1.0
        percentage *= 100.0
        #currency = quote.get('Currency')
        currency = ''
    else:
        percentage = None
        currency = None

    return latest, percentage, currency

def getCurrentQuote(ticker):
    #temp use this function
    return  getCurrentQuoteAlternative(ticker)
    url = 'https://query.yahooapis.com/v1/public/yql?'
    q = {
        'q': 'select * from yahoo.finance.quotes where symbol in ("{0}")'.format(ticker),
        'format': 'json',
        'diagnostics': 'true',
        'env': 'store://datatables.org/alltableswithkeys'
    }

    query = url + urllib.urlencode(q)
    #print query
    try:
        result = requests.get(query)
    except requests.exceptions.RequestException as e:
        output("Failed to connect to yahoo")
        return None, None, None

        
    dic = json.loads(result.content)
    if dic is None:
        output("Failed to connect to yahoo")
        return None, None, None

    quote = dic.get('query').get('results').get('quote')
    if type(quote)  == list:
        return None, None, None

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
        'diagnostics': 'true',
        'env': 'store://datatables.org/alltableswithkeys'
    }
    query = url + urllib.urlencode(q)
    result = requests.get(query)

    try:
        result = requests.get(query)
    except requests.exceptions.RequestException as e:
        output("Failed to connect to yahoo")
        return None

    dic = json.loads(result.content)
    if dic is None:
        output("Failed to connect to yahoo")
        return None, None, None

    results = dic.get('query').get('results')

    old = None

    if results is not None:
        quoteList = results.get('quote')

        if not type(quoteList) is dict:
            old = float(quoteList[-1].get('Close'))    
        else:
            old = float(quoteList.get('Close'))  
            
    return old


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
    out = u'{0} '.format(name).replace('\n', '')
    if formatting:
        out = formatting.bold(out)
    return out


def runMe(tickers, arg=None):
    if not tickers:
        output("No arguments passed")
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

        timeDelta2 = timedelta(days=30)
        endDate2 = startDate + timeDelta2
        endDateString2 = endDate2.strftime("%Y-%m-%d")

    for ticker in tickers:
        fticker, name = getTicker(ticker)
        if fticker:
            latest, percentage, currency = getCurrentQuote(fticker)

            if arg is not None:
                old = getQuoteForRange(fticker, startDateString, endDateString2)

                if old:
                    percentage = (latest - old) / old
                    percentage *= 100.0

                    out = formatName(name)
                    out += "({4}) period quote: startdate: {0}; quote: {1}, enddate {2}; quote {3}. change: ".format(startDateString, old, endDateString, latest, fticker)
                    out += formatPercentage(percentage)
                    output(out)         
                    return

               
            if not percentage:
                percentage = 0.0
            
            out = formatName(name)
            out += '({1}) quote is: {0:.2f} {2} '.format(latest, fticker, currency)
            out += formatPercentage(percentage)
        else:
            out = 'Found no ticker for ' + formatName(ticker) + 'at yahoo finance'
        
        output(out)

try:
    @module.commands('yf', 'y')
    def yf(bot, trigger):
        args = trigger.group(2)
        splitargs = args.split(' ')

        if re.search('\d+d|\d+m|\d+y', splitargs[-1]):
            arg = splitargs[-1]
            tickers = ' '.join(splitargs[:-1])
        else:
            arg = None
            tickers = ' '.join(splitargs)
        
        global botten
        botten = bot
        runMe(tickers, arg)

    @module.commands('aud')
    def audsek(bot, trigger):    
        tickers = 'audsek=x'
        global botten
        botten = bot
        runMe(tickers)

    @module.commands('yfind')
    def yfind(bot, trigger):    
        global botten
        botten = bot
        ticker = trigger.group(2)
        findTickers(ticker)

    @module.commands('curre', 'kurredutt')
    def curre(bot, trigger):    
        global botten
        botten = bot
        ticker = 'CUR'
        runMe(ticker)
except:
    #module not available
    #import traceback
    #traceback.print_exc(file=sys.stdout)
    pass

def test():
    #tickers = 'PRIC-B.ST'
    #tickers = 'G5EN.ST'
    #tickers = 'G5EN.ST,PRIC-B.ST'
    #tickers = 'apple,pricer'
    #tickers = 'microsoft,fingerprint,pricer'
    #tickers = 'pricer,interfox'
    #tickers = 'cur'
    #tickers = 'indu-c'
    #tickers = 'sas.st'
    tickers = 'fingerprint'
    #tickers = u'nilörngruppen'

    #arg = '12m'
    #arg = '1y'
    #arg = yt'15d'
    arg = None
    #arg = '3d'

    runMe(tickers, arg)

def test2():
    da = 'omxs30'
    res = findTickers(da, maxresult=20)

if __name__ == "__main__":
    test()
    #test2()
