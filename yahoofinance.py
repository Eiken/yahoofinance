#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import time
import json
import requests
import sys
import inspect
from datetime import datetime
from datetime import timedelta
from pprint import pprint

import yahooquery

from sopel import module
from sopel import formatting

botten = None


def output(out):
    global botten
    if botten is not None:
        botten.say(out)
    else:
        # Debug print for development outside of sopel
        print(repr(out))
        print(out)


def getTicker(name):
    """
    Get symbol ticker from arbitrary name. Return first search result
    """
    search_result = yahooquery.search(name)

    quotes = search_result.get("quotes")

    if not quotes:
        return None, None

    first_quote = quotes[0]

    return first_quote.get("symbol"), first_quote.get("longname")


def findTickers(ticker, maxresult=5):
    search_result = yahooquery.search(ticker)
    quotes = search_result.get("quotes")
    if not quotes:
        out = "Found no tickers"
        output(out)
        return

    out = "Found {0} tickers. Max result is {1}.".format(len(quotes), maxresult)
    output(out)
    for r in quotes[:maxresult]:
        out = formatting.bold(r.get("symbol"))

        out += " ({0})".format(r.get("longname"))
        out += " of type {0}".format(r.get("typeDisp"))

        output(out)


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


def runMe(tickers, arg=None):
    if not tickers:
        output("No arguments passed")
        return

    tickers = tickers.split(",")
    totalPercentage = []

    base_out_period = "{shortName} ({symbol}): {startdate:%Y-%m-%d} - {enddate:%Y-%m-%d}: {old_quote:.2f} - {regularMarketPrice} {currency} "
    base_out = "{shortName} ({symbol}): {regularMarketPrice} {currency} "

    for ticker in tickers:
        res = {}
        fticker, name = getTicker(ticker)
        if not fticker:
            fticker = ticker

        t = yahooquery.Ticker(fticker)

        res.update(t.summary_detail)

        price_info = t.price
        price_info_ticker = price_info.get(fticker)
        if isinstance(price_info_ticker, str):
            output(price_info_ticker)
            continue

        res.update(price_info_ticker)

        if arg:
            out = base_out_period

            history = t.history(arg, "1d")
            history_as_dict = history.to_dict()

            close = history_as_dict.get("close")
            close_keys = list(close.keys())
            start_key = close_keys[0]
            end_key = close_keys[-1]
            start_info = close.get(start_key)
            end_info = close.get(end_key)

            res["startdate"] = start_key[1]
            res["enddate"] = end_key[1]
            res["old_quote"] = start_info

            percentage = (res.get("regularMarketPrice") - start_info) / start_info

        else:
            out = base_out
            percentage = res["regularMarketChangePercent"]

        percentage *= 100.0
        out += formatPercentage(percentage)
        out = out.format(**res)
        output(out)


def set_current_bot(bot):
    global botten
    botten = bot


@module.commands("yf", "y")
def yf(bot, trigger):
    args = trigger.group(2)
    tickers, arg = parse_args(args)

    set_current_bot(bot)
    runMe(tickers, arg)


@module.commands("yfind")
def yfind(bot, trigger):
    set_current_bot(bot)
    ticker = trigger.group(2)
    findTickers(ticker)


@module.commands("aud")
def audsek(bot, trigger):
    tickers = "audsek=x"
    set_current_bot(bot)
    runMe(tickers)


@module.commands("bitte", "btcusd", "btc")
def bitte(bot, trigger):
    tickers = "BTC-USD"
    set_current_bot(bot)
    runMe(tickers)


@module.commands("ada", "cardano")
def adan(bot, trigger):
    tickers = "BTC-USD"
    set_current_bot(bot)
    runMe(tickers)


@module.commands("eth", "ether")
def eth(bot, trigger):
    tickers = "ETH-USD"
    set_current_bot(bot)
    runMe(tickers)


@module.commands("doge")
def doggi(bot, trigger):
    tickers = "DOGE-USD"
    set_current_bot(bot)
    runMe(tickers)


@module.commands("wsb", "wallstreetbets", "yesorno")
def wsb(bot, trigger):
    tickers = "GME,AMC,TSLA,NOK,RKT,PLTR,NIO"
    set_current_bot(bot)
    runMe(tickers)


@module.commands("crypto")
def crypto(bot, trigger):
    tickers = "BTC-USD,ETH-USD,XRP-USD,DOGE-USD"
    set_current_bot(bot)
    runMe(tickers)


@module.commands("metal")
def metal(bot, trigger):
    tickers = "GC=F,SI=F,HG=F"
    set_current_bot(bot)
    runMe(tickers)


@module.commands("oil")
def olja(bot, trigger):
    tickers = "CL=F,BZ=F,HO=F"
    set_current_bot(bot)
    runMe(tickers)


@module.commands("asien")
def asia(bot, trigger):
    tickers = "399001.SZ,^HSI,^N225"
    set_current_bot(bot)
    runMe(tickers)


@module.commands("börsen")
def borsen(bot, trigger):
    tickers = "^OMX,^GDAXI,^GSPC,BTC-USD"
    set_current_bot(bot)
    runMe(tickers)


@module.commands("omx")
def omxen(bot, trigger):
    tickers = "^OMX"
    set_current_bot(bot)
    runMe(tickers)


def parse_args(args):
    splitargs = args.split(" ")

    if len(splitargs) == 1:
        return splitargs[0], None
    else:
        return " ".join(splitargs[:-1]), splitargs[-1]


def test_current_quote():
    args = [
        "PRIC-B.ST",
        "G5EN.ST",
        "G5EN.ST,PRIC-B.ST",
        "apple,pricer",
        "microsoft,fingerprint,pricer",
        "pricer,BTC-USD",
        "DOGE-USD",
        "foooooobar.st",
    ]
    for a in args:
        print(a)
        tickers, arg = parse_args(a)
        runMe(tickers, arg)


def test_find_tickers():
    findTickers("baba")


def test_historical_quotes():
    hist = ["1m", "1mo", "5d", "1y", "1wk", "max"]
    for h in hist:
        args = "pricer " + h
        print(args)
        tickers, arg = parse_args(args)
        runMe(tickers, arg)


if __name__ == "__main__":
    # test_current_quote()
    # test_historical_quotes()
    test_find_tickers()
