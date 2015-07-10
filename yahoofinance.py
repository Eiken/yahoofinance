import requests
import urllib
from datetime import datetime
from datetime import timedelta
import re

ticker = 'PRIC-B.ST'
ticker = 'G5EN.ST'

arg = '3m'
arg = '1y3m'
arg = '15d'
arg = None

url = 'https://query.yahooapis.com/v1/public/yql?'


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
    dic = eval(result.content)
    quoteList = dic.get('query').get('results').get('quote')

    if len(quoteList) > 1:
        latest = float(quoteList[0].get('Close'))
        old = float(quoteList[-1].get('Close'))    

        percentage = (latest - old) / old
        percentage *= 100.0


        out = "{0} period quote: startdate: {1}; quote: {2}, enddate {3}; quote {4}. change: ({5:.2f}%)".format(ticker, startDateString, old, endDateString, latest, percentage)
        print out
    
        
        

else:
    q = {
        'q': 'select * from yahoo.finance.quote where symbol in ("{0}")'.format(ticker),
        'format': 'json',
        'env': 'store://datatables.org/alltableswithkeys'
    }

    query = url + urllib.urlencode(q)
    result = requests.get(query)
    dic = eval(result.content)
    quote = dic.get('query').get('results').get('quote')
    latest = quote.get('LastTradePriceOnly')
    percentage = quote.get('Change')

    out = 'Latest {0} quote is: {1} ({2}%)'.format(ticker, latest, percentage)
    print out

