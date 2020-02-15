# 1024社区图片爬虫
"""
执行时间做一下     暂时不用了，因为变成单线程在做
下载图片功能做一下   完成，但要细化分页文件夹和命名
反爬虫 ip 被封怎么搞    可能是代理ip解决的，可能是包头里加了coockie和accept解决的？
多线程池问题暂时解决不是很好，待实现优化
实现下载完，数据库修改状态

cookie，变化，处理    要自动get道cookie然后保存、更新
"""

# -*- coding: utf-8 -*-
import logging
import os
import random
# import threading
# from concurrent.futures import ThreadPoolExecutor, as_completed, wait, ALL_COMPLETED
import traceback
from logging import handlers
from pathlib import Path

import configparser
import pymongo
import requests
# import json
import time
import re
from bs4 import BeautifulSoup

CONFIGFILE = "config.ini"  # 配置文件名 ,这个一定ok才行
HTTPS = "https://"
HTTP = "http://"
# 全局配置
GLOBAL = "Global"  # 配置文件-全局配置key值
DEFAULT_HOST = "get.xunfs.com"  # 默认获取主页地址的网址url
DEFAULT_URL_PATH = "app/listapp.php"
# 日志配置
LOG = "Log"  # 配置文件-日志配置key值
LOG_PATH = "log/p1024.log"
WHEN = "midnight"
INTERVAL = 1
BACKUP_COUNT = 5
# 数据库配置
DATABASE = "Database"  # 配置文件-数据库配置key值
DB_HOST = "mongodb://localhost:27017/"
DATABASE_NAME = "p1024"
MAIN_URL_TABLE = "MainUrl"
Areaur_Url_TABLE = "AreaurUrl"
Picture_Url_TABLE = "PictureUrl"
# 下载配置
Download = "Download"
Download_Path = "Download/"
# 指令配置
INSTRUCTION = "Instruction"
SWITCH = 0


def InitConf():
    """
    初始化配置文件
    :param config:
    :return:
    """
    conf = configparser.ConfigParser()

    if not Path(CONFIGFILE).is_file():
        fd = open(CONFIGFILE, mode="w", encoding="utf-8")  # 创建空文件
        fd.close()

    conf[GLOBAL] = {'DefaultHost': DEFAULT_HOST,
                    "DefaultUrlPath": DEFAULT_URL_PATH
                    }

    conf[LOG] = {'LogPath': LOG_PATH,
                 "When": WHEN,
                 "Interval": INTERVAL,
                 "BackupCount": BACKUP_COUNT
                 }

    conf[DATABASE] = {"DBHost": DB_HOST,
                      'Database': DATABASE_NAME,
                      'MainURLTABLE': MAIN_URL_TABLE,
                      'AreaurUrlTABLE': Areaur_Url_TABLE,
                      "PictureUrlTABLE": Picture_Url_TABLE
                      }

    conf[Download] = {"DownloadPath": Download_Path}

    conf[INSTRUCTION] = {"Switch": SWITCH}

    with open(CONFIGFILE, 'w') as configfile:
        conf.write(configfile)

    return conf


def ReadConfig():
    conf = configparser.ConfigParser()
    # 检查配置文件
    if not Path(CONFIGFILE).is_file():
        log.info("缺少配置文件\"" + CONFIGFILE + "\"，需要初始化！！！")
        return None
    elif conf is None:
        log.error("有配置文件，读取空值，检查配置文件\"" + CONFIGFILE + "\"内容，或删除配置文件进行重启进行初始化")
        exit(-1)

    conf.read(CONFIGFILE)

    return conf


def get_logger(when="midnight", interval=1, backupCount=5):
    """
    日志模块配置
    :return:
    """
    logPath = "log/p1024.log"  # logini["LogPath"]
    when = when  # "midnight"           # logini["When"]
    interval = interval  # 1                # logini["Interval"]
    backupCount = backupCount  # 5           # logini["BackupCount"]

    logger_obj = logging.getLogger(__name__)
    if not Path("log").is_dir():
        os.makedirs(Path("log"))
    logger_obj.setLevel(logging.INFO)
    # fh = logging.FileHandler(log_file)
    fh = handlers.TimedRotatingFileHandler(logPath, when=when, interval=interval,
                                           backupCount=backupCount, encoding='utf-8')  # filename定义将信息输入到指定的文件，
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


#
def GetMainUrl(hosturl, urlpath):
    """
    获取主页
    :param urlpath:
    :param hosturl:
    :return:
    """
    url = HTTPS + hosturl + "/" + urlpath
    head = {
        "accept": "*/*",
        "connection": "Keep-Alive",
        "user-agent": "Mozilla/4.0 (compatible; MSIE 6.13; Windows NT 5.1;SV1)",
        "Host": hosturl,
        "Accept-Encoding": "gzip",
        "Content-Type": "application/x-www-form-urlencoded",
        "Content-Length": "30"
    }
    data = "a=get18&system=android&v=2.2.4"
    response = requests.post(url, data=data, headers=head)
    data = response.json()
    code = response.status_code
    log.info(url + "return code(" + str(code) + ")")

    # 将data的json放到list中
    datalist = [
        {"name": "url1", "url": data["url1"], "status": 1},
        {"name": "url2", "url": data["url2"], "status": 1},
        {"name": "url3", "url": data["url3"], "status": 1},
    ]
    mainurltable = mydb[MAIN_URL_TABLE]
    # mainurltable.delete_many({})
    for d in datalist:
        if not IsHaveHashData(MAIN_URL_TABLE, d, {"_id": 0}):
            log.info("Need Insert:" + str(d))
            mainurltable.insert_one(d)  # 数据库中没有的则插入
            pass
    return datalist
    # print(data["url1"])


# 查询db中table有没有dat这条数据 hash比对
def IsHaveHashData(table, dat, datshowdict):
    result = False
    dat = dat
    # mycol = mydb[table]
    for x in table.find({}, datshowdict):
        # print("xhash=" + str(hash(str(x))) + "\n" + "dhash=" + str(hash(str(dat))) + "\n")
        if hash(str(dat)) == hash(str(x)):
            result = True
            log.debug("数据库:" + str(mydb.name) + "\t表:" + str(table.name) + "\t已有数据:" + str(dat) + "数据hash值:" + str(
                hash(str(dat))) + "\tResult:" + str(result))
    # print(result)
    return result
    pass


def file_write(fstr, fname):
    f = open(fname, "w+", encoding="utf-8")
    f.write(fstr)
    f.close()


def file_read_data(fname):
    f = open(fname, "r", encoding="utf-8")
    line = f.readline()
    result = ""
    while line:
        result += line
        line = f.readline()
    f.close()
    return result


def GetCookie():
    if not Path("p1024_cookie.txt").is_file():
        fd = open("p1024_cookie.txt", mode="w", encoding="utf-8")  # 创建空文件
        fd.close()
    result = file_read_data("p1024_cookie.txt")

    return result


# 根据主页url开始进入，操作处理
def GetMainPagaInfo(host_url):
    url = HTTPS + host_url + "//index.php"
    # cookie = "__cfduid=dba705234c4d97a2955a497ea5c9827461581446271; UM_distinctid=170358b8538127-0ff0112ab3a28c-5373e62-144000-170358b8539331; PHPSESSID=o2ojaksdf5rl8praij15nrd1o1; serverInfo=cl.fc55.ga%7C114.216.127.160; 227c9_lastvisit=0%091581578981%09%2Fnotice.php%3F; CNZZDATA950900=cnzz_eid%3D941630872-1581441339-https%253A%252F%252Fcl.fc55.ga%252F%26ntime%3D1581576339"
    head = {
        "user-Agent": "Mozilla/4.0 (compatible; MSIE 6.13; Windows NT 5.1;SV1)",
        "Host": host_url,
        "Content-Type": "text/html;charset=utf-8",
        "Content-Length": "0",
        # "Cookie": cookie,
    }
    cookie = GetCookie()
    if len(cookie) > 1:
        head["Cookie"] = cookie
    # data = ""
    log.info("主页地址:" + url)
    print("主页地址:" + url)
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
    # 获取cookie
    for key, value in response.cookies.items():
        cookie += key + '=' + value + ';'
    file_write(cookie, "p1024_cookie.txt")

    return p_list


def GetAreaurUrl(arealist):
    """
    解析 获取 分区url地址
    :param arealist:
    :return:
    """
    areaurls = []
    fstr = ""
    for i in arealist:
        # fstr = fstr + i.text + "-" + i['href'] + "\n"
        areaurldict = {"name": i.text, "url": i['href']}  # , "isdid": 0}
        areaurls.append(areaurldict)

    # 入库
    areaurltable = mydb[Areaur_Url_TABLE]
    # areaurltable.delete_many({})
    d_i = 0
    for d in areaurls:
        if not IsHaveHashData(Areaur_Url_TABLE, d, {"_id": 0, "isdid": 0}):
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


def GetPageUrlFromDb(hosturl, table, areanum, pagetable):
    """
    版块分区 页面处理
    :param pagetable:
    :param areanum:
    :param hosturl:
    :param table:
    :return:
    """
    areaurltable = mydb[table]
    allpages = []
    myquery = {"_id": areanum, "isdid": 0}  # 根据id来设置处理的分区，这里以12【图片】分区先做
    for each in areaurltable.find(myquery, {"url": 1}):
        # print("194" + str(each))
        result = each["url"]
    for i in range(1, 2):
        eachurl = result + "&search=&page=" + str(i)
        allpages.append(eachurl)
        AreaurPage(hosturl, eachurl, pagetable)
        # task = executor.submit(AreaurPage, hosturl, eachurl)
        # print(hosturl + "/" + eachurl)

    # with ThreadPoolExecutor(3) as executor:
    # for eachurl in allpages:
        # future = executor.submit(AreaurPage, hosturl, eachurl)
        # AreaurPage(hosturl, eachurl, pagetable)
        # alltask.append(future)
    # executor.submit()



def AreaurPage(host_url, eachurl, table):
    """
    -从板块页（xx区）获取具体每一项页面    这里目前只有'图片'区，以后可以改成传入参数，或每个区不同函数
    :param host_url: -Host地址
    :param eachurl: -urlpath路径
    :return:    没啥用
    """
    url = "https://" + host_url + "/" + eachurl  # GetPageUrlFromDb("AreaUrl")
    # url = "https://cl.fc55.ga/thread0806.php?fid=8&search=&page=1"
    head = {
        # "user-Agent": "Mozilla/4.0 (compatible; MSIE 6.13; Windows NT 5.1;SV1)",
        "user-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/76.0.3809.132 Safari/537.36",
        "Host": host_url,
        "Content-Length": "0",
        "Accept": "accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,"
                  "application/signed-exchange;v=b3",
        # "Cookie": cookie,
    }
    cookie = GetCookie()
    if len(cookie) > 1:
        head["Cookie"] = cookie

    print("抓取地址板块地址:" + url + "\n")
    log.info("抓取地址板块地址:" + url + "\n")

    proxy = '119.23.79.199:3128'  # 本地代理
    # proxies = {
    #     'http': 'http://' + proxy,
    #     'https': 'https://' + proxy
    # }
    response = requests.get(url, headers=head)
    # response = requests.get(url, headers=head, proxies={"http": "http://118.89.234.236:8787"})    # 代理IP模式
    code = response.status_code
    if code != 200:
        log.warning("页面:" + url + "返回:" + str(code))  #

    # 页面数据解析 放到 p_list 中
    html = response.content.decode('GBK', 'ignore')
    content_soup = BeautifulSoup(html, 'lxml')
    p_list = content_soup.select(' h3 > a')  # List 存放需要的项
    # 解析结果与预期不符，一般就是IP被反爬了，要验证码，就直接gg出去
    if len(p_list) == 0:
        log.warning("页面反爬验证 or 页面错误")
        return -1
    # p_list = content_soup.select(' .tal ')
    log.info("解析获得单页：" + str(len(p_list)) + "项")

    # 单页地址
    # 入库
    singlepagetable = mydb[table]
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
                    if not IsHaveHashData(singlepagetable, datadict, {"_id": 0}):
                        log.info("入库:" + mydb.name + "/" + singlepagetable.name + str(datadict))
                        singlepagetable.insert_one(datadict)  # 数据库中没有的则插入
                        pass
                    # logstr = "单页:" + fstr + "\t" + i['href'] + "\n"
                    # log.info(logstr)
    time.sleep(random.uniform(0.5, 1))
    print("完成抓取解析入库:" + url)
    return 0
    # 分主题爬取 ps:[写真]、[动漫]

    # 进入具体页进行操作，这里最好要做通道先进先出，放一个地址进去，拿一个地址出来。
    # 用多线程，线程池 pool

    #


#
def GetOnePage(host_url, table, wantdowntype):
    """
    从表table中查询未下载的进行下载
    :param host_url:    hots地址
    :param table:   表名
    :param wantdowntype:    想要下载的类型
    :return:
    """
    # print(str(table))
    for each in table.find({"status": 0, "type": wantdowntype}).sort("_id", 1):
        # print(str(each))
        imgid = each["_id"]
        imgname = each["name"]
        imgdowntype = each["type"]
        imgurl = each["url"]
        imgdidcount = int(each["isdid"])
        imgstatus = int(each["status"])
        if imgstatus == 0 and imgdowntype == "寫真":
            log.info("进入[" + imgurl + "]预备下载：" + imgname)
            GetALLPic(host_url, table, imgid, imgname, imgurl, imgdidcount)


def GetALLPic(host_url, ptable, pid, pfname, purlpath, pdidcount):
    """
    进入单页，操作，下载；修改图片数据库状态
    :param host_url:    Host
    :param ptable:      表名
    :param pid:         id
    :param pfname:      图名
    :param purlpath:    单页url路径
    :param pdidcount:   已下载计数
    :return:
    """
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

    p_list = content_soup.select('div.tpc_content.do_not_catch > img ')
    pmax = len(p_list)
    ptable.update_one({"_id": pid}, {"$set": {"max": pmax}})
    # log.info("pmax---" + str(pmax))
    for i in range(pdidcount, pmax):
        src = p_list[i]["data-src"]
        # log.info('src::' + str(src))
        downimg(src, pfname, i, pmax)  #
        ptable.update_one({"_id": pid}, {"$set": {"isdid": i + 1}})
    ptable.update_one({"_id": pid}, {"$set": {"status": 1, "isdid": pmax, "max": pmax}})
    print("下载完成:" + "[" + str(pid) + "](" + str(pmax) + ")")
    log.info("下载完成:" + "[" + pfname + "](" + str(pmax) + ")")


def downimg(src, fstr, didcount, pmax):
    """
    下载图片
    :param src:
    :param fstr:
    :param didcount:
    :param pmax:
    :return:
    """
    # url = "https://" + host_url + "/" + url_1
    url = src
    b = False
    try:
        r = requests.get(url)
    except Exception as e:
        print(e.__str__())
    # log.info(str(r))
    imgindexname = src.split('/')[-1]
    # my_file = Path(Download_Path + fstr)
    # print(Download_Path + " " + fstr)
    if r.status_code != 200:
        r = requests.get(url)
    # if not Path(Download_Path).is_dir():    # download目录
    #     os.makedirs(Download_Path)
    if not Path(Download_Path + "/" + fstr).is_dir():        # 单项目录
        os.makedirs(Download_Path + "/" + fstr)

    with open(Download_Path + "/" + fstr + "/" + imgindexname, 'wb') as f:
        f.write(r.content)
        # log.info(imgindexname + " 下载成功(" + str(fstr) + "/" + str(pmax) + ")")
        os.system("")  # 变色玄学必须
        print(Download_Path + "\033[0;37;47m" + fstr + "\033[0m" + imgindexname + " 下载成功(" + str(didcount) + "/" + str(pmax) + ")")


def CheckMainUrl():
    """
    检查主页状态
    :return:
    """
    result = ''
    m_can_use_urls = []  # 存放库中状态可用的url地址列表
    maintable = mydb[MAIN_URL_TABLE]
    for x in maintable.find({"status": 1}).sort("_id", -1):
        if len(x) == 0:
            break
        m_can_use_urls.append(x)

    for x in m_can_use_urls:
        m_re_htmls = GetMainPagaInfo(x["url"])
        if len(m_re_htmls) > 0:
            m_can_use_urls.append(x)
            result = m_can_use_urls
            break
        else:
            m_can_use_urls.remove(x)
            maintable.update_one({"_id": x["_id"]}, {"$set": {"status": 0}})

    log.info("主页地址列表:" + str(m_can_use_urls))

    return m_can_use_urls


if __name__ == '__main__':
    try:

        log = get_logger()
        log.info("Start,启动--------------------")
        config = ReadConfig()
        if config is None:
            config = InitConf()  # 缺少配置文件就初始化
            log.info("初始化配置文件完成！！！Exit,退出--------------------\n\n")
            print("初始化配置文件完成！！！Exit,退出--------------------\n\n")
            exit(120)
        log.info("配置文件加载完成>>>>>" + str(config))

        # 全局配置
        DEFAULT_HOST = config[GLOBAL]["DefaultHost"]  # 默认获取主页地址的网址url
        DEFAULT_URL_PATH = config[GLOBAL]["DefaultUrlPath"]
        # 日志配置
        LOG_PATH = config[LOG]["logpath"]
        WHEN = config[LOG]["When"]
        INTERVAL = config[LOG].getint("Interval")
        BACKUP_COUNT = config[LOG].getint("BackupCount")
        # 数据库配置
        DB_HOST = config[DATABASE]["DBHost"]
        DATABASE_NAME = config[DATABASE]['Database']
        MAIN_URL_TABLE = config[DATABASE]['MainURLTABLE']
        Areaur_Url_TABLE = config[DATABASE]['AreaurUrlTABLE']
        Picture_Url_TABLE = config[DATABASE]["PictureUrlTABLE"]
        # 下载配置
        Download_Path = config[Download]["DownloadPath"]
        # 指令配置
        SWITCH = config[INSTRUCTION].getint("Switch")

        # log = get_logger(config[LOG]["When"], config[LOG].getint("Interval"), config[LOG].getint("backupCount"))

        myclient = pymongo.MongoClient(DB_HOST)
        mydb = myclient[DATABASE_NAME]

        if SWITCH == 0:     # 初始化，不做爬虫
            pass

        elif SWITCH == 1:   # 显示可用网址
            mhost = CheckMainUrl()
            if mhost == '':
                # 获取主页地址
                all_urls = GetMainUrl(DEFAULT_HOST, DEFAULT_URL_PATH)
                log.info("主页地址列表:" + str(all_urls))
                print("可用地址：" + str(all_urls))
            else:
                log.info("主页地址列表:" + str(mhost))
                print("可用地址：" + str(mhost))

        elif SWITCH == 2:       # 抓分区地址
            mhost = CheckMainUrl()
            if mhost == '':
                # 获取主页地址
                mhost = GetMainUrl(DEFAULT_HOST, DEFAULT_URL_PATH)
                log.info("主页地址列表:" + str(mhost))
                print("可用地址：" + str(mhost))
            else:
                log.info("主页地址列表:" + str(mhost))
                print("可用地址：" + str(mhost))
            # 解析主页 获取分区地址  GetMainPagaInfo() 改成返回本次获取的地址，解析的单独函数做
            mainhtml = GetMainPagaInfo(mhost[0]["url"])
            GetAreaurUrl(mainhtml)

        elif SWITCH == 3:       # 下载
            mhost = CheckMainUrl()
            if mhost == '':
                # 获取主页地址
                mhost = GetMainUrl(DEFAULT_HOST)
                log.info("主页地址列表:" + str(mhost))
                print("可用地址：" + str(mhost))
            else:
                log.info("主页地址列表:" + str(mhost))
                print("可用地址：" + str(mhost))
            GetPageUrlFromDb(mhost[0]["url"], Areaur_Url_TABLE, 12, Picture_Url_TABLE)    # 12是图片区的 _id
            pictable = mydb[Picture_Url_TABLE]

            GetOnePage(mhost[0]["url"], pictable, "寫真")

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
        # print("Exit")

    except Exception as e:
        # print('traceback.format_exc():\n%s' % traceback.format_exc())
        log.error('traceback.format_exc():\n' + traceback.format_exc())
    input("Press Any Key Exit!!!")
    log.info("Exit,退出--------------------\n\n")
