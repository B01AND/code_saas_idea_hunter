'''
Description: Editor's info in the top of the file
Author: wanghaisheng
Date: 2022-04-08 23:53:55
LastEditor: wanghaisheng
LastEditTime: 2022-04-08 23:53:55
Email: tiktoka@gmail.com
'''

import requests
from peewee import *
from datetime import datetime
import time
import random
import math
import os
db = SqliteDatabase("vercel.sqlite")

keywords=''

class DB(Model):
    id = IntegerField()
    full_name = CharField(max_length=1024)
    description = CharField(max_length=4098)
    url = CharField(max_length=1024)
    created_at = CharField(max_length=128)

    class Meta:
        database = db


db.connect()
db.create_tables([DB])


def write_file(new_contents,topic):
    if not os.path.exists("web/README-{}.md".format(topic)):
        open("web/README-{}.md".format(topic),'w').write('')
    # with open("web/README-{}.md".format(topic),'r',encoding='utf8') as f:
    #     #去除标题
    #     for _ in range(7):
    #         f.readline()

    #     old = f.read()
    # new = new_contents + old
    with open("web/README-{}.md".format(topic), "w") as f:
        f.write(new_contents)


def craw_all(topic):
    # 这是爬取所有的,github api限制每分钟请求最多30次
    api = "https://api.github.com/search/repositories?q={}&sort=updated".format(topic)
    item_list = []
    try:
        reqtem = requests.get(api).json()
        total_count = reqtem["total_count"]
        for_count = math.ceil(total_count / 30) + 1
        print(total_count)
        items = reqtem["items"]
        for j in range(0, for_count, 1):
            try:
                api = "https://api.github.com/search/repositories?q={}&sort=updated&per_page=30&page={}".format(topic,j)

                req = requests.get(api).json()
                items = req["items"]
                item_list.extend(items)
                print("第{}轮，爬取{}条".format( j, len(items)))
                time.sleep(random.randint(3, 15))
            except Exception as e:
                print("网络发生错误", e)
                continue

            time.sleep(random.randint(3, 15))
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


def db_match(items):
    # print(items)
    r_list = []
    for item in items:
        if not item["id"]=='':
            id = int(item["id"])
            
            if DB.select().where(DB.id == id).count() != 0:
                continue
            full_name = item["full_name"]
            description = item["description"]
            if description == "" or description == None:
                description = 'no description'
            else:
                description = description.strip()
            url = item["html_url"]
            created_at = item["created_at"]
            r_list.append({
                "id": id,
                "full_name": full_name,
                "description": description,
                "url": url,
                "created_at": created_at
            })
            DB.create(id=id,
                        full_name=full_name,
                        description=description,
                        url=url,
                        created_at=created_at)

    return sorted(r_list, key=lambda e: e.__getitem__('created_at'))


def main(keyword,topic):
    # 下面是监控用的
    year = datetime.now().year
    sorted_list = []
    total_count = get_info(keyword)
    sorted = db_match(craw_all(keyword))

    if total_count is None or len(sorted) == total_count:
        pass
    else:
        print("获取原始数据:{}条".format(total_count))
        if len(sorted) != 0:
            print("更新{}条".format(len(sorted)))
            sorted_list.extend(sorted)
        count = random.randint(3, 15)
        time.sleep(count)
        # print(sorted_list)
        DateToday = datetime.today()
        day = str(DateToday)    
        newline = ""
        newline=newline+f"## {day}\n"
        newline=newline+"|id|name|url|update_at|description|\n" + "|---|---|---|---|---|\n"        
        for idx,s in enumerate(sorted_list):
            line = "|{}|{}|{}|{}|{}|\n".format(str(idx),
                s["full_name"], s["url"], s["created_at"],s["description"])    

            newline = newline+line
        # print(newline)
        if newline != "":
            newline = "# Automatic monitor github {} using Github Actions \n\n > update time: {}  total: {} \n\n \n ![star me](https://img.shields.io/badge/star%20me-click%20--%3E-orange) [code saas idea monitor](https://github.com/wanghaisheng/code_saas_idea_monitor-)  [Browsing through the web](https://p1ay8y3ar.github.io/cve_monitor/)  ![visitors](https://visitor-badge.glitch.me/badge?page_id=cve_monitor) \n\n".format(
                topic,
                datetime.now(),
                DB.select().where(DB.id != None).count()) + newline

            write_file(newline,topic)


if __name__ == "__main__":
    keywords=['vercel']
    topic='vercel'
    for k in keywords:
        main(k,topic)
