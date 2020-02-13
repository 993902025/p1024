"""
    执行时间做一下     暂时不用了，因为变成单线程在做
    下载图片功能做一下   完成，但要细化分页文件夹和命名
    反爬虫 ip 被封怎么搞    可能是代理ip解决的，可能是包头里加了coockie和accept解决的？
    多线程池问题暂时解决不是很好，待实现优化
    实现下载完，数据库修改状态
"""

# -*- coding: utf-8 -*-
import logging
import os
import random
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed, wait, ALL_COMPLETED
from logging import handlers
from pathlib import Path

import pymongo

import requests
import json
import time
import re
from bs4 import BeautifulSoup

# import p1_test

m_url = "https://get.xunfs.com/app/listapp.php"
m_urls = []

myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["p1024"]


# 日志模块
def get_logger():
    logger_obj = logging.getLogger(__name__)
    log_file = "p1024.log"
    logger_obj.setLevel(logging.INFO)
    # fh = logging.FileHandler(log_file)
    fh = handlers.TimedRotatingFileHandler(log_file, when="D", interval=1,
                                           backupCount=10, encoding='utf-8')  # filename定义将信息输入到指定的文件，
    # when指定单位是s(秒),interval是时间间隔的频率,单位是when所指定的哟（所以，你可以理解频率是5s）；backupCount表示备份的文件个数，我这里是指定的3个文件。
    fh.setLevel(logging.INFO)

    ch = logging.StreamHandler()
    ch.setLevel(logging.WARNING)

    formater = logging.Formatter("%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s")
    fh.setFormatter(formater)
    ch.setFormatter(formater)

    logger_obj.addHandler(fh)
    logger_obj.addHandler(ch)

    return logger_obj


# 获取主页
def GetMainUrl(url_s):
    url = url_s
    head = {
        "accept": "*/*",
        "connection": "Keep-Alive",
        "user-agent": "Mozilla/4.0 (compatible; MSIE 6.13; Windows NT 5.1;SV1)",
        "Host": "get.xunfs.com",
        "Accept-Encoding": "gzip",
        "Content-Type": "application/x-www-form-urlencoded",
        "Content-Length": "30"
    }
    data = "a=get18&system=android&v=2.2.4"
    response = requests.post(url, data=data, headers=head)
    data = response.json()
    code = response.status_code
    log.info(url + "return code(" + str(code) + ")")

    mainurltable = mydb["MainUrl"]
    # mainurltable.delete_many({})
    # 将data的json放到list中
    datalist = [
        {"name": "url1", "url": data["url1"], "status": 1},
        {"name": "url2", "url": data["url2"], "status": 1},
        {"name": "url3", "url": data["url3"], "status": 1},
    ]
    for d in datalist:
        if not IsHaveHashData(mydb, "MainUrl", d, {"_id": 0}):
            log.info("Need Insert:" + str(d))
            mainurltable.insert_one(d)  # 数据库中没有的则插入
            pass
    return datalist
    # print(data["url1"])


# 查询db中table有没有dat这条数据 hash比对
def IsHaveHashData(db, table, dat, datshowdict):
    result = False
    dat = dat
    mycol = db[table]
    for x in mycol.find({}, datshowdict):
        # print("xhash=" + str(hash(str(x))) + "\n" + "dhash=" + str(hash(str(dat))) + "\n")
        if hash(str(dat)) == hash(str(x)):
            result = True
            log.debug("数据库:" + str(db.name) + "\t表:" + str(table) + "\t已有数据:" + str(dat) + "数据hash值:" + str(
                hash(str(dat))) + "\tResult:" + str(result))
    # print(result)
    return result
    pass


# 根据主页url开始进入，操作处理
def main_page(host_url):
    url = "https://" + host_url + "//index.php"
    cookie = "__cfduid=dba705234c4d97a2955a497ea5c9827461581446271; UM_distinctid=170358b8538127-0ff0112ab3a28c-5373e62-144000-170358b8539331; PHPSESSID=o2ojaksdf5rl8praij15nrd1o1; serverInfo=cl.fc55.ga%7C114.216.127.160; 227c9_lastvisit=0%091581578981%09%2Fnotice.php%3F; CNZZDATA950900=cnzz_eid%3D941630872-1581441339-https%253A%252F%252Fcl.fc55.ga%252F%26ntime%3D1581576339"
    head = {
        "user-Agent": "Mozilla/4.0 (compatible; MSIE 6.13; Windows NT 5.1;SV1)",
        "Host": host_url,
        "Content-Type": "text/html;charset=utf-8",
        "Content-Length": "0",
        "Cookie": cookie,
    }
    data = ""
    log.info("抓取主页地址:" + url + "\n")
    print("抓取主页地址:" + url + "\n")
    response = requests.get(url, headers=head)
    # data = response.content
    # response.encoding = response.apparent_encoding
    html = response.content.decode('GBK')
    log.debug(html)

    content_soup = BeautifulSoup(html, 'lxml')
    p_list = content_soup.select('#main > .t > table > #cate_1 > .tr3 > th > h2 > a')
    p_list += content_soup.select('#main > .t > table > #cate_6 > .tr3 > th > h2 > a')
    # print(p_list)   > .tr3 > .icon > a
    if len(p_list) == 0:
        log.warning("页面反爬验证")

    return p_list


def GetAreaurUrl(arealist):
    '''
    解析 获取 分区url地址
    :param arealist:
    :return:
    '''

    areaurls = []
    fstr = ""

    for i in arealist:
        # fstr = fstr + i.text + "-" + i['href'] + "\n"
        areaurldict = {"name": i.text, "url": i['href']}  # , "isdid": 0}
        areaurls.append(areaurldict)

    # 入库
    areaurltable = mydb["AreaUrl"]
    # areaurltable.delete_many({})
    d_i = 0
    for d in areaurls:
        if not IsHaveHashData(mydb, "AreaUrl", d, {"_id": 0, "isdid": 0}):
            d["isdid"] = 0
            d_i += 1
            d["_id"] = d_i
            log.info("Need Insert:" + str(d))
            areaurltable.insert_one(d)  # 数据库中没有的则插入
    d_i = 0

    log.info("版块分区列表:" + str(areaurls))

    # 文件存储
    # f = open("F:\\123\\p1\\模块地址列表.txt", "w+", encoding="utf-8")
    # log.info("写入文件:F:\\123\\p1\\模块地址列表.txt,写入内容:" + fstr)
    # f.write(fstr)
    # log.info("写入文件:模块地址列表.txt,完成!")
    # f.close()

    # 每个板块区一个线程
    # t_page_cate1 = myThread(page_cate1, (host_url, p_list2[0]['href'], ))
    # t_page_cate2 = myThread(page_cate1, (host_url, p_list2[1]['href'],))      # 图片区的
    # t_page_cate1.start()
    # t_page_cate2.start()    # 图片区的


def GetPageUrlFromDb(hosturl, table):
    '''
    版块分区 页面处理
    :param hosturl:
    :param table:
    :return:
    '''
    areaurltable = mydb[table]
    allpages = []
    myquery = {"_id": 12, "isdid": 0}  # 根据id来设置处理的分区，这里以12【图片】分区先做
    for each in areaurltable.find(myquery, {"url": 1}):
        print("194" + str(each))
        result = each["url"]
    for i in range(1, 2):
        eachurl = result + "&search=&page=" + str(i)
        allpages.append(eachurl)
        # task = executor.submit(AreaurPage, hosturl, eachurl)
        # print(hosturl + "/" + eachurl)
    alltask = []

    # with ThreadPoolExecutor(3) as executor:
    for eachurl in allpages:
        # future = executor.submit(AreaurPage, hosturl, eachurl)
        AreaurPage(hosturl, eachurl)
        # alltask.append(future)
    # executor.submit()

    return alltask
    pass



def AreaurPage(host_url, eachurl):
    '''
    -从板块页（xx区）获取具体每一项页面    这里目前只有'图片'区，以后可以改成传入参数，或每个区不同函数
    :param host_url: -Host地址
    :param eachurl: -urlpath路径
    :return:    没啥用
    '''
    url = "https://" + host_url + "/" + eachurl  # GetPageUrlFromDb("AreaUrl")
    # url = "https://cl.fc55.ga/thread0806.php?fid=8&search=&page=1"
    cookie = "__cfduid=dba705234c4d97a2955a497ea5c9827461581446271; UM_distinctid=170358b8538127-0ff0112ab3a28c-5373e62-144000-170358b8539331; PHPSESSID=o2ojaksdf5rl8praij15nrd1o1; serverInfo=cl.fc55.ga%7C114.216.127.160; 227c9_lastvisit=0%091581578981%09%2Fnotice.php%3F; CNZZDATA950900=cnzz_eid%3D941630872-1581441339-https%253A%252F%252Fcl.fc55.ga%252F%26ntime%3D1581576339"
    head = {
        # "user-Agent": "Mozilla/4.0 (compatible; MSIE 6.13; Windows NT 5.1;SV1)",
        "user-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36",
        # "user-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36 cl_fc55_ga",
        "Host": host_url,
        "Content-Length": "0",
        "Accept": "accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
        "Cookie": cookie,
    }
    log.warning("抓取地址板块地址:" + url + "\n")
    log.info("抓取地址板块地址:" + url + "\n")

    proxy = '119.23.79.199:3128'  # 本地代理
    proxies = {
        'http': 'http://' + proxy,
        'https': 'https://' + proxy
    }
    response = requests.get(url, headers=head)
    # response = requests.get(url, headers=head, proxies={"http": "http://118.89.234.236:8787"})    # 代理IP模式
    code = response.status_code
    if code != 200:
        log.warning("页面:" + url + "返回:" + str(code))  #

    # 页面数据解析 放到 p_list 中
    html = response.content.decode('GBK', 'ignore')
    content_soup = BeautifulSoup(html, 'lxml')
    p_list = content_soup.select(' h3 > a')     # List 存放需要的项
    # 解析结果与预期不符，一般就是IP被反爬了，要验证码，就直接gg出去
    if len(p_list) == 0:
        log.warning("页面反爬验证 or 页面错误")
        return -1
    # p_list = content_soup.select(' .tal ')
    log.info("解析获得单页：" + str(len(p_list)) + "项")

    # 单页地址
    # 入库
    singlepagetable = mydb["SinglePage"]
    # singlepagetable.delete_many({})

    # 每个解析截取出来的进行再验证，然后再操作
    for i in p_list:
        # 首先检查属性有没有 "href" 链接，没有的说明不是预期项
        if i.text and i["href"]:
            # 从父项的父项上搞到文字标题 name，
            if i.parent.parent['class'][0] == 'tal':
                # print("test=265")
                if (not re.search('[↑]\d', i.parent.parent.text)) and (not re.search('[notice]', i.parent.parent.text)):
                    fstr = i.parent.parent.getText('\n', '&nbsp').replace('\n', ' ').replace(u'\xa0', ' ').replace(
                        u'\u200b', '')
                    try:
                        typestr = fstr.split('[')[1].split(']')[0]
                    except:
                        typestr = "其他"
                    singurl = i['href']
                    # print(fstr + i["href"])
                    # itext = i.parent.parent.get_text().replace(u'\xa0', ' ')  # 将源码中的空格转码
                    # itext = itext.replace(u'\u200b', '')
                    datadict = {"name": fstr, "type": typestr, "url": i['href'], "isdid": 0, "max": 0, "status": 0}
                    if not IsHaveHashData(mydb, "SinglePage", datadict, {"_id": 0}):
                        log.info("入库:" + str(datadict))
                        singlepagetable.insert_one(datadict)  # 数据库中没有的则插入
                        pass
                    # logstr = "单页:" + fstr + "\t" + i['href'] + "\n"
                    # log.info(logstr)
    time.sleep(random.uniform(0.5, 1))
    print("完成:" + url)
    return 0
    # 分主题爬取 ps:[写真]、[动漫]

    # 进入具体页进行操作，这里最好要做通道先进先出，放一个地址进去，拿一个地址出来。
    # 用多线程，线程池 pool

    #


#
def GetOnePage(host_url, table, wantdowntype):
    '''
    从表table中查询未下载的进行下载
    :param host_url:    hots地址
    :param table:   表名
    :param wantdowntype:    想要下载的类型
    :return:
    '''
    # print(str(table))
    for each in table.find({"status": 0, "type": wantdowntype}).sort("_id"):
        # print(str(each))
        imgid = each["_id"]
        imgname = each["name"]
        imgdowntype = each["type"]
        imgurl = each["url"]
        imgdidcount = int(each["isdid"])
        imgstatus = int(each["status"])
        if imgstatus == 0 and imgdowntype == "寫真":
            log.info("进入/" + imgurl + "/预备下载……")
            GetALLPic(host_url, table, imgid, imgname, imgurl, imgdidcount)


# 进入单页，操作，下载
# 修改图片数据库状态
def GetALLPic(host_url, ptable, pid, pfname, purlpath, pdidcount):
    '''

    :param host_url:    Host
    :param ptable:      表名
    :param pid:         id
    :param pfname:      图名
    :param purlpath:    单页url路径
    :param pdidcount:   已下载计数
    :return:
    '''
    url = "https://" + host_url + "/" + purlpath
    # print(url)
    head = {
        "user-Agent": "Mozilla/4.0 (compatible; MSIE 6.13; Windows NT 5.1;SV1)",
        "Host": host_url,
        "Content-Length": "0",
    }
    response = requests.get(url, headers=head)
    html = response.content.decode('GBK')
    content_soup = BeautifulSoup(html, 'lxml')
    # print(str(response.status_code) + "321==" + str(content_soup).replace(u'\xbb', ' ').replace(u'\xa0', ' ').replace(u'\u200b', ''))
    p_list = content_soup.select('div.tpc_content.do_not_catch > img ')
    pmax = len(p_list)
    ptable.update_one({"_id": pid}, {"$set": {"max": pmax}})
    log.info("pmax---" + str(pmax))
    for i in range(pdidcount, pmax):
        src = p_list[i]["data-src"]
        log.info('src::' + str(src))
        downimg(src, pfname, i, pmax)        ####
        ptable.update_one({"_id": pid}, {"$set": {"isdid": i + 1}})
    ptable.update_one({"_id": pid},  {"$set": {"status": 1, "isdid": pmax, "max": pmax}})
    print("下载完成:" + "[" + str(pid) + "](" + str(pmax) + ")")
    log.info("下载完成:" + "[" + pfname + "](" + str(pmax) + ")")

    return i

def downimg(src, fstr, didcount, pmax):
    # url = "https://" + host_url + "/" + url_1
    url = src
    b = False
    r = requests.get(url)
    imgname = src.split('/')[-1]
    my_file = Path("p1024/"+fstr)
    # print(my_file)
    if r.status_code != 200:
        r = requests.get(url)
    if not my_file.is_dir():
        os.makedirs(my_file)

    with open("p1024/" + fstr + "/" + imgname, 'wb') as f:
        f.write(r.content)
        print(imgname + " 下载成功(" + str(didcount) + "/" + str(pmax) + ")")


def CheckMainUrl():
    result = ''
    m_urls = []
    maintable = mydb["MainUrl"]
    for x in maintable.find({"status": 1}).sort("_id", -1):
        if len(x) == 0:
            break
        log.info(x)
        m_urls.append(x)

    for x in m_urls:
        mainhtml = main_page(x["url"])
        if len(mainhtml) > 0:
            m_urls.append(x["url"])
            result = x["url"]
            break
        else:
            m_urls.remove(x)
            maintable.update({"_id": x["_id"]}, {"status": 0})

    log.info("主页地址列表:" + str(m_urls))

    return result


if __name__ == '__main__':
    log = get_logger()
    log.info("Start,启动--------------------")
    switch = 0
    all_urls = []
    mhost = CheckMainUrl()
    if mhost != '':
        switch == 1
        pass
    else:
        # 获取主页地址
        all_urls = GetMainUrl(m_url)
        log.info("主页地址列表:" + str(all_urls))

        mainhtml = main_page(all_urls[0]["url"])
        GetAreaurUrl(mainhtml)

    stable = mydb["SinglePage"]   # 图片区

    GetOnePage(mhost, stable, "寫真")

    # all_task = GetPageUrlFromDb(all_urls[0]["url"], "AreaUrl")
    # for each in all_task:
    #     print("all_task"+str(each))
    # wait(all_task, return_when=ALL_COMPLETED)
    # done, unfinished = wait(all_task, timeout=0, return_when=ALL_COMPLETED)
    # for d in done:
    #     log.info('执行中:%s, 已完成:%s' % (d.running(), d.done()))
        # print(d.result())
    # for future in as_completed(all_task):
    #     data = future.result()
    #     print("in main: get page {}s success".format(data))
    # AreaurPage(m_urls[0]["url"], 12)
    # # print(d)

    # singlepagetable = mydb["SinglePage"]
    # for x in singlepagetable.find():
    #     log.info(x)
    # print("执行数:%s" % (singlepagetable.count_documents({})))
    # for each in all_task:
    #     print("all_task"+str(each))
    print("Exit")
    log.info("Exit,退出--------------------\n\n")
