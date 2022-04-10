#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: RogerRordo

from ast import keyword
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
from pyairtable.formulas import match
from pyairtable import *

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


async def worker(id: int, st: datetime, ed: datetime, proxypool: str, delay: float, timeout: float,topic:str,keyword:str,index:int,table:Table) -> dict:
    workerRes = {}  # e.g. {'22.3.4.5': '2021-04-26 03:53:41'}
    # proxy = await popProxy(id, proxypool, timeout)

    
    item_list = []
    j=index
    global signalTag
    while not signalTag:
        proxy = requests.get(proxypool).text
        print('proxypool',proxypool,proxy)           
        try:

            url = "https://api.github.com/search/repositories?q={}&sort=updated&per_page=30&page={}".format(topic,j)
                # client.get() may get stuck due to unknown reasons
                # resp = await client.get(url=url, headers=HEADERS, timeout=timeout)
            resp = requests.get(url,proxies={'http': proxy})
            req = resp.json()
            items = req["items"]
            print("第{}轮，爬取{}条".format( j, len(items)))

            save(table,keyword,topic,items)
            item_list.extend(items)
        except Exception as e:
            print("网络发生错误", e)
            newProxy = requests.get(proxypool).text
            log.warning('[{}] Proxy EXP: proxy={} newProxy={} st={} ed={}'.format(id, proxy, newProxy, time2str(st),
                                                                                    time2str(ed)))
            log.debug('[{}] Proxy EXP: {}'.format(id, e))
            proxy = newProxy

async def main(opts):
    # Catch signal to exit gracefully
    signal.signal(signal.SIGINT, signalHandler)
    timeSt = '2021-05-01 00:00:00'
    timeEd = '2021-05-01 01:00:00'
    keywords=[]
    print('keywords list ',opts.keywords)
    
    if ',' in opts.keywords:
        keywords=opts.keywords.split(',')
    else:
        keywords.append(opts.keywords)
    topic=opts.topic
    print('keywords list ',keywords)
    apikey=os.environ['AIRTABLE_API_KEY']
    baseid=os.environ[topic.upper()+'_AIRTABLE_BASE_KEY']
    tableid=os.environ[topic.upper()+'_AIRTABLE_TABLE_KEY']
    api = Api(apikey)
    table = Table(apikey, baseid, tableid)

    for k in keywords:
        # Assign tasks
        coroutines = []
        timeSt = str2time(timeSt)
        timeEd = str2time(timeEd)
        dt = (timeEd - timeSt) / opts.threads
        try:
            url = "https://api.github.com/search/repositories?q={}&sort=updated".format(topic)

            reqtem = requests.get(url).json()
            # print('raw json',reqtem)
            total_count = reqtem["total_count"]
            if total_count<30:
                for_count=0
            for_count = math.ceil(total_count / 30) + 1

            if total_count<30:
                for_count=0
            for_count = math.ceil(total_count / 30) + 1
            print(total_count)
        except:
            print('here=========')

        for i in range(total_count):
            coroutines.append(
                worker(id=i,
                    st=timeSt + dt * i,
                    ed=timeSt + dt * (i + 1),
                    proxypool=opts.proxypool,
                    delay=opts.delay,
                    timeout=opts.timeout,
                    topic=topic,
                    keyword=k,
                    index=i,
                    table=table))

        # Run tasks
        workerRes = await asyncio.gather(*coroutines)
        print('======',workerRes)
        page(table,topic)

def write_file(new_contents,topic):
    if not os.path.exists("web/README-{}.md".format(topic)):
        open("web/README-{}.md".format(topic),'w').write('')
    with open("web/README-{}.md".format(topic),'r',encoding='utf8') as f:
        #去除标题
        for _ in range(7):
            f.readline()

        old = f.read()
    new = new_contents + old
    with open("web/README-{}.md".format(topic), "w") as f:
        f.write(new)
def url_ok(url):
    try:
        response = requests.head(url)
    except Exception as e:
        # print(f"NOT OK: {str(e)}")
        return False
    else:
        if response.status_code == 400 or response.status_code==404:
            # print("OK")
            print(f"NOT OK: HTTP response code {response.status_code}")

            return False
        else:

            return True   

def get_info(topic):
    # 监控用的
    try:

        api = "https://api.github.com/search/repositories?q={}".format(topic)
        # 请求API
        req = requests.get(api).json()
        items = req["items"]
        total_count = req["total_count"]
        for_count = math.ceil(total_count / 100) + 1
        # print(total_count)
        return total_count
    except Exception as e:
        print("网络请求发生错误", e)
        return None
def newbase(dbname):
    db=Base('apikey', dbname)    
    return dbname
def newtable(db,table_name):
    api_key = os.environ['AIRTABLE_API_KEY']

    table = Table(api_key, db, table_name)
    return table
def insert2airtable(table,rows):
    # print(rows,'====',type(rows[0]))
    if len(rows)==1:

        table.create(rows[0])
    else:
        table.create(rows)


def getrowid(table,row):

    formula = match(row)
    try:
        id =table.first(formula=formula)['id']
    except:
        id = None
    return id

def updaterow(table,rows):
    if len(rows)==1:
        id =getrowid(table,rows[0])
        if id is None:
            insert2airtable(table,rows)            
        else:
            table.update(id,rows[0])
    else:
        for row in rows:
            id =getrowid(table,[row])
            if id is None:
                insert2airtable(table,[row])            
            else:
                table.update(id,[row])      

def db_match_airtable(table,items,keyword):
    print('waiting to check',len(items))
    r_list = []
    for item in items:
        if item['id'] == "" or item['id']  == None:
            pass
        else:
            print('valid  to save',item)

            full_name = item["full_name"]
            description = item["description"]
            if description == "" or description == None:
                description = 'no description'
            else:
                description = description.strip()
            url = item["html_url"]
            created_at = item["created_at"]
            topics=''
            if item["topics"] == "" or item["topics"] == None:
                topics=keyword
            else:
                topics=','.join(item["topics"])
            language=item['language']
            if language == "" or language == None:
                language='unknown'
            row =[{
                "name": full_name,
                "description": description,
                "url": url,
                "topic":topics,
                "language":language,
                "created_at": created_at
            }]
            updaterow(table,row)

    return ''

def save(table,keyword,topic,items):
    # 下面是监控用的
    year = datetime.now().year
    sorted_list = []
    total_count = get_info(keyword)
    print("获取原始数据:{}条".format(total_count))
    # items=craw_all(keyword)
    print("获取dao原始数据:{}条".format(len(items)))


    if total_count is None or len(items) == total_count:
        pass
    else:
        sorted = db_match_airtable(table,items,keyword)
        print("record in db:{}条".format(len(sorted)))

def page(table,topic):
    result=[]
    for idx,item in enumerate(table.all()):
        print(idx,item['fields'])
        result.append(item['fields'])    
    # print(sorted_list)
    DateToday = datetime.today()
    day = str(DateToday)    
    newline = ""

    for idx,s in enumerate(sorted):
        print(s,'-')
        line = "|{}|{}|{}|{}|{}|{}|{}|\n".format(str(idx),
            s["name"], s["description"], s["created_at"],s["url"],s["topic"],s["language"])    

        newline = newline+line
    # print(newline)
    if newline != "":
        old=f"## {day}\n"
        old=old+"|id|name|description|update_at|url|topic|language|\n" + "|---|---|---|---|---|---|---|\n"                   
        newline = "# Automatic monitor github {} using Github Actions \n\n > update time: {}  total: {} \n\n \n ![star me](https://img.shields.io/badge/star%20me-click%20--%3E-orange) [code saas idea monitor](https://github.com/wanghaisheng/code_saas_idea_hunter)  [Browsing through the web](https://wanghaisheng.github.io/code_saas_idea_hunter/)  ![visitors](https://visitor-badge.glitch.me/badge?page_id=code_saas_idea_hunter) \n\n{}".format(
            topic,
            datetime.now(),
            len(sorted)
            ,old) + newline

        write_file(newline,topic)


def getOpts():
    parser = optparse.OptionParser()
    parser.add_option('-m', '--module', dest='module', default='ruijie_eg', type=str, help='Module name')
    parser.add_option('-k', '--keywords', dest='keywords', default='genshin', type=str, help='keyword list')
    parser.add_option('-n', '--topic', dest='topic', default='genshin', type=str, help='topic name')
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
