#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
import urllib
import sys
from datetime import datetime
from datetime import timedelta
import re
import json
import sys
import os
import time
import inspect
from pprint import pprint
import importlib.machinery

current_folder = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
get_yahoo_quotes = importlib.machinery.SourceFileLoader(
    "get_yahoo_quotes", os.path.join(current_folder, "get_yahoo_quotes.py")
).load_module()

try:
    from sopel import module
    from sopel import formatting
except:
    module = None
    formatting = None
    # import traceback
    # traceback.print_exc(file=sys.stdout)

botten = None


def output(out):
    global botten
    if botten is not None:
        botten.say(out)
    else:
        print(out)


def getTicker(name, gimme=False):
    if int(sys.version[0]) == 2:
        if not type(name) is unicode:
            name = name.decode("utf-8")

    name = name.replace(u"ö", u"o")
    name = name.replace(u"ä", u"a")
    name = name.replace(u"å", u"a")

    # url = u"http://d.yimg.com/autoc.finance.yahoo.com/autoc?query={0}&callback=YAHOO.Finance.SymbolSuggest.ssCallback".format(name)
    url = u"https://s.yimg.com/aq/autoc?query={0}&region=CA&lang=en-CA&callback=YAHOO.util.ScriptNodeDataSource.callbacks".format(
        name
    )

    try:
        response = requests.get(url)
    except requests.exceptions.RequestException as e:
        output("Failed to connect to yahoo")
        return None, None

    # html = response.content.lstrip("YAHOO.Finance.SymbolSuggest.ssCallback(").rstrip(")")
    html = response.content
    if int(sys.version[0]) > 2:
        html = html.decode("UTF-8")

    html = html.lstrip("YAHOO.util.ScriptNodeDataSource.callbacks(")
    html = html.rstrip(");")
    data = json.loads(html)
    result = data.get("ResultSet").get("Result")
    results = []
    sortOrder = {}
    sortOrder["Index"] = 0
    sortOrder["Equity"] = 1
    sortOrder["Futures"] = 2
    sortOrder["ETF"] = 3

    if result:
        if gimme is True:
            for r in sorted(result, key=lambda x: sortOrder.get(x.get("typeDisp"), 999)):
                results.append([r.get("symbol"), r.get("name"), r.get("typeDisp")])

            return results
        else:
            # try to find swedish stocks first
            for r in sorted(result, key=lambda x: sortOrder.get(x.get("typeDisp"), 999)):
                if r.get("exch") == "STO":
                    return r.get("symbol"), r.get("name")

            return result[0].get("symbol"), result[0].get("name")
    else:
        return None, None


def findTickers(ticker, maxresult=5):
    res = getTicker(ticker, gimme=True)
    if res[0] is None:
        out = "Found no tickers"
        output(out)
        return
    out = "Found {0} tickers. Max result is {1}.".format(len(res), maxresult)
    output(out)
    count = 0
    for r in res:
        if count == maxresult:
            break
        out = r[1]
        if formatting:
            out = formatting.bold(out)

        out += " ({0})".format(r[0])
        out += " of type {0}".format(r[2])

        output(out)
        count += 1


def getCurrentQuote(ticker):
    url = "https://query1.finance.yahoo.com/v7/finance/quote?symbols={0}&view=detail&format=json".format(
        ticker
    )
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; MotoE2(4G-LTE) Build/MPI24.65-39) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.81 Mobile Safari/537.36"
    }
    try:
        result = requests.get(url, headers=headers)
    except requests.exceptions.RequestException as e:
        output("Failed to connect to yahoo")
        return None

    html = result.content
    if int(sys.version[0]) > 2:
        html = html.decode("UTF-8")

    dic = json.loads(html, strict=False)
    if dic is None:
        output("Failed to connect to yahoo")
        return None

    resources = dic.get("quoteResponse").get("result")
    if not resources:
        return None

    resource = resources[0]
    return resource


def formatPercentage(percentage):
    pf = "{0:.2f}%".format(percentage)

    if percentage > 0:
        pf = "+" + pf

    if formatting:
        if percentage < 0:
            pf = formatting.color(pf, formatting.colors.RED)
        elif percentage > 0:
            pf = formatting.color(pf, formatting.colors.GREEN)

    pf = "(" + pf + ")"

    return pf


def formatBold(name):
    out = u"{0} ".format(name).replace("\n", "")
    if formatting:
        out = formatting.bold(out)
    return out


def runMe(tickers, arg=None):
    if not tickers:
        output("No arguments passed")
        return

    tickers = tickers.split(",")
    totalPercentage = []

    if arg is not None:
        days = re.findall("(\d+)(d)", arg)
        months = re.findall("(\d+)(m)", arg)
        years = re.findall("(\d+)(y)", arg)

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

        startDateUnix = int(time.mktime(startDate.timetuple()))
        endDateUnix = int(time.mktime(endDate.timetuple()))

    base_out_period = "{shortName} ({symbol}): {startdate:%Y-%m-%d} - {enddate:%Y-%m-%d}: {old_quote} - {regularMarketPrice} {currency} "
    base_out = "{shortName} ({symbol}): {regularMarketPrice} {currency} "
    extra_out = "{dayRange}{dayVolume}{netWorth}{pe}"

    for ticker in tickers:
        fticker, name = getTicker(ticker)
        if not fticker:
            fticker = ticker

        res = getCurrentQuote(fticker)

        if res is None or "regularMarketChangePercent" not in res:
            out = "Found no data for " + formatBold(ticker) + "at yahoo finance"
            output(out)
            return

        percentage = res.get("regularMarketChangePercent")

        if "shortName" not in res and "longName" in res:
            res["shortName"] = res["longName"]
        elif "shortName" not in res:
            res["shortName"] = res["symbol"]

        if arg is not None:
            cookie, crumb = get_yahoo_quotes.get_cookie_crumb(fticker)
            data_list = get_yahoo_quotes.get_data_list(
                fticker, startDateUnix, endDateUnix, cookie, crumb
            )

            if data_list:
                old = data_list[0]["Close"]
                startDate = data_list[0]["Date"]
                percentage = (res.get("regularMarketPrice") - old) / old
                percentage *= 100.0

                res["startdate"] = startDate
                res["enddate"] = endDate
                res["old_quote"] = old

                out = base_out_period
                out += formatPercentage(percentage)
            else:
                out = (
                    "Found no historical data for "
                    + formatBold(ticker)
                    + "at yahoo finance"
                )
        else:
            out = base_out
            out += formatPercentage(percentage)
            out += extra_out

        res["shortName"] = formatBold(res["shortName"])
        res["dayRange"] = (
            ". "
            + formatBold("Day range")
            + ": {regularMarketDayLow}-{regularMarketDayHigh}".format(**res)
        )
        res["dayVolume"] = (
            ". " + formatBold("Day volume") + ": {regularMarketVolume}".format(**res)
        )
        if "marketCap" in res:
            res["marketCap"] = res["marketCap"] / 1000000.0
            res["netWorth"] = (
                ". "
                + formatBold("Net worth")
                + ": {marketCap:.2f} M{currency}".format(**res)
            )
        else:
            res["netWorth"] = ""

        if "trailingPE" in res:
            res["pe"] = (
                ". " + formatBold("Trailing P/E") + ": {trailingPE:.2f}".format(**res)
            )
        else:
            res["pe"] = ""

        if "currency" not in res:
            res["currency"] = ""
        out = out.format(**res)
        output(out)


try:

    @module.commands("yf", "y")
    def yf(bot, trigger):
        args = trigger.group(2)
        splitargs = args.split(" ")

        if re.search("\d+d|\d+m|\d+y", splitargs[-1]):
            arg = splitargs[-1]
            tickers = " ".join(splitargs[:-1])
        else:
            arg = None
            tickers = " ".join(splitargs)

        global botten
        botten = bot
        runMe(tickers, arg)

    @module.commands("yfind")
    def yfind(bot, trigger):
        global botten
        botten = bot
        ticker = trigger.group(2)
        findTickers(ticker)

    # shortcuts

    @module.commands("aud")
    def audsek(bot, trigger):
        tickers = "audsek=x"
        global botten
        botten = bot
        runMe(tickers)

    @module.commands("bitte", "btcusd", "btc")
    def bitte(bot, trigger):
        tickers = "BTC-USD"
        global botten
        botten = bot
        runMe(tickers)

    @module.commands("doge")
    def doggi(bot, trigger):
        tickers = "DOGE-USD"
        global botten
        botten = bot
        runMe(tickers)

    @module.commands("crypto")
    def crypto(bot, trigger):
        tickers = "BTC-USD,ETH-USD,XRP-USD,DOGE-USD"
        global botten
        botten = bot
        runMe(tickers)

    @module.commands("curre", "kurredutt")
    def curre(bot, trigger):
        global botten
        botten = bot
        ticker = "CUR"
        runMe(ticker)


except:
    # module not available
    # import traceback
    # traceback.print_exc(file=sys.stdout)
    pass


def test():
    tickers = "PRIC-B.ST"
    # tickers = 'G5EN.ST'
    # tickers = 'G5EN.ST,PRIC-B.ST'
    # tickers = 'apple,pricer'
    # tickers = 'microsoft,fingerprint,pricer'
    # tickers = 'pricer,BTCUSD=X'
    # tickers = 'DOGE-USD'
    # tickers = 'indu-c'
    # tickers = 'kkd'
    # tickers = 'fingerprint'
    # tickers = u'marketing group'

    # arg = '1m'
    # arg = '1y'
    # arg = yt'15d'
    # arg = None
    arg = "3d"

    runMe(tickers, arg)


def test2():
    da = "omxs30"
    res = findTickers(da, maxresult=20)


if __name__ == "__main__":
    test()
    # test2()
