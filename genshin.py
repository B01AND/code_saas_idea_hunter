'''
Description: Editor's info in the top of the file
Author: wanghaisheng
Date: 2022-04-08 23:53:55
LastEditor: wanghaisheng
LastEditTime: 2022-04-08 23:53:55
Email: tiktoka@gmail.com
'''

from unittest import result
import requests
from peewee import *
from datetime import datetime
import time
import random
import math
import json
import os
from pyairtable.formulas import match
from pyairtable import *
import platform
import asyncio
from playwright.async_api import async_playwright


keywords=''
# from .util import *
async def get_playright(url,proxy,headless:bool=True):
    print('proxy',proxy,'headless',headless)
    browser=''
    playwright =await  async_playwright().start()
    PROXY_SOCKS5 = "socks5://127.0.0.1:1080"
    browser=''
    if proxy==False:
        try:
            browser = await  playwright.firefox.launch(headless=headless)
            print('start is ok')
            return browser

        except:
            print('pl no proxy start failed')
            browserLaunchOptionDict = {
            "headless": headless,
            "proxy": {
                    "server": PROXY_SOCKS5,
            }
            } 
            browser = await playwright.firefox.launch(**browserLaunchOptionDict)
            # Open new page    
            return browser
    else: 
        print('proxy===',headless)
        browserLaunchOptionDict = {
        "headless": headless,
        "proxy": {
                "server": PROXY_SOCKS5,
        }
        } 
        browser = await playwright.firefox.launch(**browserLaunchOptionDict)
        # Open new page    

        return browser

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

def update_daily_json(filename,data_all):
    if not os.path.exists(filename):
        open(filename,'w').write('')
    with open(filename,"r") as f:
        content = f.read()
        if not content:
            m = {}
        else:
            m = json.loads(content)
    
    #将datas更新到m中
    for data in data_all:
        m.update(data)

    # save data to daily.json

    with open(filename,"w") as f:
        json.dump(m,f)
    
async def craw_all_pl(topic):
    item_list = []
    datall=[]

    start = time.time()
    url = "https://github.com/search?o=desc&q={}&s=updated&type=Repositories".format(topic)
    try:
        browser = await get_playright(False,False)
        context = await browser.new_context()
        page = await browser.new_page()
        res=await page.goto(url)
        print('user home url',url)
        count =  page.locator('div.flex-column:nth-child(1) > h3:nth-child(1)')
        count = await count.text_content()
        print(count.strip())
        count=count.strip().split(' ')[0].replace(',','')
        print(count)
        total_count = int(count)
        if total_count<30:
            for_count=0
        for_count = math.ceil(total_count / 30) + 1

        print('total count',total_count)
        filters=page.locator("a.filter-item")
        
        filterscount=await filters.count()
        print(filterscount,type(filterscount))
        if filterscount>0:
            for i in range(filterscount):
                element =filters.nth(i)
                href="https:github.com"+await element.get_attribute("href")
                keyword=href.split('=')[1]
                count = await element.locator('span').text_content()
                print(keyword,count)
                total_count=int(count)
                pages=int(total_count/10)+1
                urls=[]
                for i in range(pages):
                    url=href+'&s=updated&p='+str(i)
                    print('keyword',keyword,'page-',url)
                    try:
                        res=await page.goto(url)
                        items = page.locator('li.repo-list-item')
                        for i in range(await items.count()):
                            full_name =await items.nth(i).locator('a.v-align-middle').text_content()
                            print('fullname',full_name)
                            des =items.nth(i).locator('p.mb-1')
                            if await des.count()>0:
                                description=await des.text_content()
                            url ="https:github.com"+await items.nth(i).locator('a.v-align-middle').get_attribute("href")
                            ife=items.nth(i).locator("div > div > div >a.topic-tag")
                            topics =topic

                            if await ife.count()>0:
                                for i in range(await ife.count()):
                                    tmp =await ife.nth(i).get_attribute("title")
                                    topics=topics+','+tmp.split(":")[1]
                            language=keyword.split('&')[0]
                            FORMAT='%Y-%m-%dT%H:%M:%S%z'

                            row ={
                                "name": full_name,
                                "description": description.strip(),
                                "url": url,
                                "topic":topics,
                                "language":language,
                                "created_at": datetime.now().strftime(FORMAT)
                            }
                            print(row,'============')
                            datall.append(row)
                            updaterow(table,[row])

                    
                    except Exception as e:
                        print("网络发生错误", e)
                        continue

                    time.sleep(random.randint(30, 60))    
        
    except:
        print("请求数量的时候发生错误")
    update_daily_json("data/{}.json".format(topic),datall)

    return item_list



def craw_all(topic):
    # 这是爬取所有的,github api限制每分钟请求最多30次
    api = "https://api.github.com/search/repositories?q={}&sort=updated".format(topic)
    item_list = []
    try:
        reqtem = requests.get(api).json()
        total_count = reqtem["total_count"]
        total_count =1000
#         github api limit
        if total_count<30:
            for_count=0
        for_count = math.ceil(total_count / 30) + 1
        print(total_count)
        # item_list = reqtem["items"]
        proxypool='https://proxypool.scrape.center/random'

        for j in range(0, for_count, 1):
            proxy = requests.get(proxypool).text
            print('proxypool',proxypool,proxy)   
            try:
                api = "https://api.github.com/search/repositories?q={}&sort=updated&per_page=30&page={}".format(topic,j)

                req = requests.get(api,proxies={'http': proxy}).json()
                items = req["items"]
                item_list.extend(items)
                print("第{}轮，爬取{}条".format( j, len(items)))
            except Exception as e:
                print("网络发生错误", e)
                continue

            time.sleep(random.randint(3, 15)*(math.ceil(for_count / 300) + 1))
    except Exception as e:
        print("请求数量的时候发生错误", e)
    # print(item_list)

    return item_list


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

def db_match_airtable(table,items,topic):
    print('waiting to check',len(items))
    r_list = []
    for item in items:
        if item['id'] == "" or item['id']  == None:
            pass
        else:
            full_name = item["full_name"]
            description = item["description"]
            if description == "" or description == None:
                description = 'no description'
            else:
                description = description.strip()
            url = item["html_url"]
            created_at = item["created_at"]
            topics=','.join(item["topics"])
            if topics == "" or topics == None:
                topics=topic
            language=item['language']
            if language == "" or language == None:
                language='unknown'
            row =[{
                "name": full_name,
                "description": description,
                "url": url,
                "topic":topic,
                "language":language,
                "created_at": created_at
            }]
            updaterow(table,row)
    result=[]
    # print(type(table.all(),len(table.all())))
    for idx,item in enumerate(table.all()):
        print(idx,item['fields'])
        result.append(item['fields'])
    return result

def save(table,keyword,topic,items):
    # 下面是监控用的
    year = datetime.now().year
    sorted_list = []
    total_count = get_info(keyword)
    print("获取原始数据:{}条".format(total_count))
    items=craw_all_pl(keyword)
    print("获取dao原始数据:{}条".format(len(items)))


    if total_count is None or len(items) == total_count:
        pass
    else:
        sorted = db_match_airtable(table,items,topic)
        print("record in db:{}条".format(len(sorted)))

        if len(sorted) != 0:
            print("更新{}条".format(len(sorted)))
            sorted_list.extend(sorted)
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


if __name__ == "__main__":
# def gitcode(apikey,baseid,tableid,keywords,topic):
    keywords=['genshin']
    topic='genshin'
    apikey=os.environ.get('AIRTABLE_API_KEY')
    baseid=os.environ.get(topic.upper()+'_AIRTABLE_BASE_KEY')
    tableid=os.environ.get(topic.upper()+'_AIRTABLE_TABLE_KEY')
    api = Api(apikey)
    table = Table(apikey, baseid, tableid)

    for k in keywords:

        # save(table,k,topic)
        
        # await run(playwright)
        asyncio.run(craw_all_pl('genshin'))