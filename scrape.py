#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: RogerRordo

import logging
import optparse
import asyncio
import base64
import signal
from datetime import datetime
from datetime import timedelta
from httpx import AsyncClient
from colorlog import ColoredFormatter
from urllib.parse import quote_plus
from utils import *
import requests
import math

HEADERS = {
    'User-Agent':
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
    'Accept': 'application/json, text/plain, */*'
}
LOG_LEVEL = logging.INFO
log = logging.getLogger('pythonConfig')

signalTag = False


def signalHandler(signal, frame):
    log.warning('Signal catched...')
    global signalTag
    signalTag = True


async def worker(id: int, st: datetime, ed: datetime, proxypool: str, delay: float, timeout: float) -> dict:
    workerRes = {}  # e.g. {'22.3.4.5': '2021-04-26 03:53:41'}
    # proxy = await popProxy(id, proxypool, timeout)
    proxy = requests.get(proxypool).text()
    
    log.info('[{}] Thread starts: proxy={} st={} ed={}'.format(id, proxy, st, ed))
    item_list = []
    topic='genshin'
    global signalTag
    while not signalTag:
        try:
            url = "https://api.github.com/search/repositories?q={}&sort=updated".format(topic)

            reqtem = requests.get(url).json()
            total_count = reqtem["total_count"]
            if total_count<30:
                for_count=0
            for_count = math.ceil(total_count / 30) + 1
            print(total_count)
        except Exception as e:
            print("请求数量的时候发生错误", e)
        reqtem = requests.get(url).json()
        total_count = reqtem["total_count"]
        if total_count<30:
            for_count=0
        for_count = math.ceil(total_count / 30) + 1
        print(total_count)
        for j in range(0, for_count, 1):
            try:
                url = "https://api.github.com/search/repositories?q={}&sort=updated&per_page=30&page={}".format(topic,j)
                async with AsyncClient(proxies="http://{}".format(proxy), verify=False, trust_env=False) as client:
                    # client.get() may get stuck due to unknown reasons
                    # resp = await client.get(url=url, headers=HEADERS, timeout=timeout)
                    resp = await asyncio.wait_for(client.get(url=url, headers=HEADERS), timeout=timeout)
                    req = resp.json()
                    items = req["items"]
                    item_list.extend(items)
                    print("第{}轮，爬取{}条".format( j, len(items)))

                    await asyncio.sleep(delay)

                    # ed = str2time(mtime) - timedelta(seconds=1)  # Update ed time

            except Exception as e:
                newProxy = requests.get("https://{}".format(proxypool)).text()
                log.warning('[{}] Proxy EXP: proxy={} newProxy={} st={} ed={}'.format(id, proxy, newProxy, time2str(st),
                                                                                    time2str(ed)))
                log.debug('[{}] Proxy EXP: {}'.format(id, e))
                proxy = newProxy
                continue
    return item_list


async def main(opts):
    # Catch signal to exit gracefully
    signal.signal(signal.SIGINT, signalHandler)

    # Load module
    # params, pocs = loadModule(opts.module)

    # Load original res.json
    # absResJson = 'module/{}/{}'.format(opts.module, params.resJson)
    # res = loadResJson(absResJson)

    timeSt = '2021-05-01 00:00:00'
    timeEd = '2021-05-01 01:00:00'

    # Assign tasks
    coroutines = []
    timeSt = str2time(timeSt)
    timeEd = str2time(timeEd)
    dt = (timeEd - timeSt) / opts.threads
    for i in range(opts.threads):
        coroutines.append(
            worker(id=i,
                   st=timeSt + dt * i,
                   ed=timeSt + dt * (i + 1),
                   proxypool=opts.proxypool,
                   delay=opts.delay,
                   timeout=opts.timeout))

    # Run tasks
    workerRes = await asyncio.gather(*coroutines)
    print(workerRes)
    # Update res
    # for it in workerRes:

    # Export hosts
    # saveResJson(res, absResJson)


def getOpts():
    parser = optparse.OptionParser()
    parser.add_option('-m', '--module', dest='module', default='ruijie_eg', type=str, help='Module name')
    parser.add_option('-p',
                      '--proxypool',
                      dest='proxypool',
                      default='https://proxypool.scrape.center/random',
                      type=str,
                      help='Host and port of ProxyPool (default = 127.0.0.1:5010)')
    parser.add_option('-d',
                      '--delay',
                      default=5,
                      type=float,
                      dest='delay',
                      help='Seconds to delay between requests for each proxy (default = 5)')
    parser.add_option('-T', '--threads', default=15, type=int, dest='threads', help='Number of threads (default = 15)')
    parser.add_option('-t', '--timeout', default=6, type=float, dest='timeout', help='Seconds of Timeout (default = 6)')

    (opts, args) = parser.parse_args()
    return opts, args


def initLog():
    LOGFORMAT = "  %(log_color)s%(asctime)s  %(levelname)-8s%(reset)s | %(log_color)s%(message)s%(reset)s"

    logging.root.setLevel(LOG_LEVEL)
    formatter = ColoredFormatter(LOGFORMAT)

    stream = logging.StreamHandler()
    stream.setLevel(LOG_LEVEL)
    stream.setFormatter(formatter)

    log.setLevel(LOG_LEVEL)
    log.addHandler(stream)


if __name__ == '__main__':
    initLog()
    opts, args = getOpts()
    if opts.module == '':
        log.error('Module name required')
    else:
        asyncio.run(main(opts))
