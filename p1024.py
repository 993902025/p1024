# 1024社区图片爬虫
"""
执行时间做一下     暂时不用了，因为变成单线程在做
反爬虫 ip 被封怎么搞    是包头里加了coockie解决的
多线程池问题暂时解决不是很好，待实现优化
exe程序莫名卡住，要日志排查，    貌似是图片文件过大，半天下不下来
"""

# -*- coding: utf-8 -*-
import logging
import os
import random
# import threading
# from concurrent.futures import ThreadPoolExecutor, as_completed, wait, ALL_COMPLETED
import sqlite3
import traceback
from contextlib import closing
from logging import handlers
from pathlib import Path
import configparser
import pymongo
import requests
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
DB_PATH = "Data"
DATABASE_NAME = "p1024.db"
MAIN_URL_TABLE = "mainurl"
Area_Url_TABLE = "areaurl"
Picture_Url_TABLE = "pictureurl"
# 下载配置
Download = "Download"
Download_Path = "Download"
# 指令配置
INSTRUCTION = "Instruction"
SWITCH = 1
GetPageNum = 1


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

    conf[DATABASE] = {"DBPath": DB_PATH,
                      'Database': DATABASE_NAME,
                      'MainURLTABLE': MAIN_URL_TABLE,
                      'AreaurUrlTABLE': Area_Url_TABLE,
                      "PictureUrlTABLE": Picture_Url_TABLE
                      }

    conf[Download] = {"DownloadPath": Download_Path}

    conf[INSTRUCTION] = {"Switch": SWITCH,
                         "GetPageNum": 1}

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
    logger_obj.setLevel(logging.DEBUG)      # 最低日志显示等级
    # fh = logging.FileHandler(log_file)
    fh = handlers.TimedRotatingFileHandler(logPath, when=when, interval=interval,
                                           backupCount=backupCount, encoding='utf-8')  # filename定义将信息输入到指定的文件，
    # when指定单位是s(秒),interval是时间间隔的频率,单位是when所指定的哟（所以，你可以理解频率是5s）；backupCount表示备份的文件个数，我这里是指定的3个文件。
    fh.setLevel(logging.DEBUG)      # 最低文件日志显示等级

    ch = logging.StreamHandler()
    ch.setLevel(logging.WARNING)    # 最低屏显日志显示等级

    formater = logging.Formatter("%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s")
    fh.setFormatter(formater)
    ch.setFormatter(formater)

    logger_obj.addHandler(fh)
    logger_obj.addHandler(ch)

    return logger_obj


# 检查一下有没有这个库、表
def CheckSqlLib(cur, table):
    # conn = sqlite3.connect(database)
    # print("!Connect database successfully")
    # c = conn.cursor()
    sql = "select name from sqlite_master where type='table' order by name"
    try:
        reslist = cur.execute(sql).fetchall()
        log.info(sql)
        log.info(reslist)
        for row in reslist:
            if row[0] == table:
                return True

    except sqlite3.Error as e:
        log.error(e.args)
    return False


def InitDatabase(con, dbpath, database):
    """
    初始化数据（sqllite）
    :param conn:
    :param dbpath:
    :param database:
    :return:
    """
    if not Path("Data").is_dir():
        os.makedirs("Data")

    if con is None:
        con = sqlite3.connect("Data" + "/" + database)
    c = con.cursor()

    # sql = 'INSERT INTO PERSONS(ID, NAME, BIRTHDAY, SEX, CNBIRTHDAY, ZI, DIE, DIEDAY, SPOUSEID, CHILDRENNUM,
    # CHILDREN) VALUES( ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
    if not CheckSqlLib(c, "USER"):
        # 创建用户表 用于测试数据库的
        sql = "CREATE TABLE USER (ID INTEGER PRIMARY KEY autoincrement NOT NULL, username VARCHAR (255) NOT NULL, password VARCHAR (255) NOT NULL, STATUS CHAR NOT NULL DEFAULT (1), BACKUP1 VARCHAR(255));"
        log.info("创建表" + "USER" + ":" + sql)
        cursor = c.execute(sql)
    if not CheckSqlLib(c, "MAINURL"):
        sql = "CREATE TABLE MAINURL (ID INTEGER PRIMARY KEY autoincrement NOT NULL, URL VARCHAR (255) NOT NULL, STATUS CHAR NOT NULL DEFAULT (1), BACKUP1 VARCHAR(255));"
        log.info("创建表" + "MAINURL" + ":" + sql)
        cursor = c.execute(sql)
    if not CheckSqlLib(c, "AREAURL"):
        sql = "CREATE TABLE AREAURL (ID INTEGER PRIMARY KEY NOT NULL, NAME VARCHAR (255) NOT NULL UNIQUE, URL VARCHAR (255) NOT NULL, STATUS CHAR NOT NULL DEFAULT (1),TABLE_NAME VARCHAR(255), BACKUP1 VARCHAR(255));"
        log.info("创建表" + "AREAURL" + ":" + sql)
        cursor = c.execute(sql)
    if not CheckSqlLib(c, "PICTUREURL"):
        sql = "CREATE TABLE PICTUREURL (ID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, NAME VARCHAR(255) NOT NULL, URL VARCHAR(255) NOT NULL, STATUS CHAR NOT NULL DEFAULT(1), TYPE VARCHAR(255) NOT NULL, ISDID INTEGER DEFAULT(0), MAX INTEGER DEFAULT(0), BACKUP1 VARCHAR(255));"
        log.info("创建表" + "PICTUREURL" + ":" + sql)
        cursor = c.execute(sql)

    # sqldata = (str(id), name, birthday, sex, cnbirthday, zi, die, dieday, spouseid, childrennum, children)
    # cursor = c.execute(sql, sqldata)
    con.commit()

    return con


def SqlSelect():
    pass


#
def GetMainUrl(hosturl, urlpath):
    log.debug("Do GetMainUrl")
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
    datalist = []
    for i in range(0, 3):
        log.debug("data:" + str(len(data) - 1) + ":" + str(data))
        datalist.append(data["url" + str(i + 1)])

    # 数据入库
    c = conn.cursor()
    for each in datalist:
        if not IsHaveHashData(MAIN_URL_TABLE, ("url", each)):
            sql = "INSERT INTO MAINURL ( URL ) VALUES ( ? );"
            sqldata = (each,)
            reslist = c.execute(sql, sqldata).fetchall()
            log.info("新数据入库:" + sql + str(each) + "|" + str(reslist))
    conn.commit()
    return datalist


def IsHaveHashData(table, *args):
    """
    查询db中table有没有dat这条数据
    :param table:
    :param args:
    :return:
    """
    c = conn.cursor()
    sql = "select id from " + table + " where "  # status = ? order by id"
    for i in range(0, len(args)):
        if i == len(args) - 1:
            sql = sql + str(args[i][0]) + " = ? " + ";"
        else:
            sql = sql + "\'" + str(args[i][0]) + "\'" + " = ?" + " and "
    sqldata = ()
    for i in range(0, len(args)):
        sqldata += (args[i][1],)

    # log.debug(sql + str(sqldata))
    reslist = c.execute(sql, sqldata).fetchall()

    if len(reslist) > 0:
        # print("表:" + table + "\t已有数据:" + str(args))
        log.info("表:" + table + "\t已有数据:" + str(args))
        return True
    else:
        return False


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
    # print("主页地址:" + url)
    response = requests.get(url, headers=head)
    # data = response.content
    # response.encoding = response.apparent_encoding
    html = response.content.decode('GBK')
    # log.debug(html)

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


def GetAreaurUrl(arealist, table):
    """
    解析 获取 分区url地址
    :param arealist:
    :param table:
    :return:
    """
    areaurls = []
    fstr = ""
    for each in arealist:
        areaurls.append({"name": each.text, "url": each['href'], "status": 1, "TABLE_NAME": table})
    log.debug("areaurls:" + str(areaurls))
    c = conn.cursor()
    for each in areaurls:
        log.debug("areaurls:" + str(each) + "|" + each["url"])
        if not IsHaveHashData(Area_Url_TABLE, ("url", each["url"])):  # (Area_Url_TABLE, d, {"_id": 0, "isdid": 0}):
            sql = "INSERT INTO " + Area_Url_TABLE.upper() + " ( NAME, URL, STATUS, TABLE_NAME ) VALUES ( ?, ?, ?, ? );"
            sqldata = (each["name"], each["url"], each["status"], each["TABLE_NAME"],)
            reslist = c.execute(sql, sqldata).fetchall()
            log.info("新数据入库:" + sql + str(each) + "|" + str(reslist))

    conn.commit()

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


def GetPageUrlFromDb(hosturl, table, areanum, getpagenum):
    """
    版块分区 页面处理
    :param getpagenum:
    :param pagetable:
    :param areanum:
    :param hosturl:
    :param table:
    :return:
    """
    # areaurltable = mydb[table]
    c = conn.cursor()
    allpages = []
    myquery = {"_id": areanum, "isdid": 0}  # 根据id来设置处理的分区，这里以12【图片】分区先做
    sql = "SELECT ID, NAME, URL, STATUS, TABLE_NAME FROM " + table.upper() + " WHERE ID = ?;"
    sqldata = (12, )
    log.debug(sql + str(sqldata))
    reslist = c.execute(sql, sqldata).fetchall()

    for each in reslist:    # 不限制 id = 12 的话，就是所有分区的地址都出来了，这里目前只做图片区（12），所以其实只有长度1
        allpages.append({"id": each[0], "name": each[1], "url": each[2], "table": each[4]})
    for each in allpages:
        for i in range(0, getpagenum):
            eachurl = each["url"] + "&search=&page=" + str(i + 1)
            # allpages.append(eachurl)
            AreaurPage(hosturl, eachurl, each["table"])
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
    :param table:
    :return:    没啥用
    """
    url = "https://" + host_url + "/" + eachurl  # GetPageUrlFromDb("AreaUrl")
    # url = "https://cl.fc55.ga/thread0806.php?fid=8&search=&page=1"
    head = {
        "user-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/76.0.3809.132 Safari/537.36",
        "Host": host_url,
        "Content-Length": "0",
        "Accept": "accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,"
                  "application/signed-exchange;v=b3",
    }
    cookie = GetCookie()
    if len(cookie) > 1:
        head["Cookie"] = cookie

    print("抓取地址板块地址:" + url + "\n")
    log.info("抓取地址板块地址:" + url + "\n")

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
    c = conn.cursor()
    datalist = []
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
                        typestr = fstr[0: int(len(fstr)/2)].split('[')[1].split(']')[0]
                    except Exception as e:
                        log.warning(e.__str__() + "|" + fstr)
                        typestr = "其他"
                    datalist.append({"name": fstr, "url": i['href'], "status": 1, "type": typestr, "isdid": 0, "max": 0})
                    # log.debug(str({"name": fstr, "url": i['href'], "status": 0, "type": typestr, "isdid": 0, "max": 0}))
    i = 0
    for each in datalist:
        if not IsHaveHashData(table, ("url", each["url"])):  # (Area_Url_TABLE, d, {"_id": 0, "isdid": 0}):
            sql = "INSERT INTO " + table.upper() + " ( NAME, URL, STATUS, TYPE, ISDID, MAX ) VALUES ( ?, ?, ?, ?, ?, ? );"
            sqldata = (each["name"], each['url'], each['status'], each['type'], each['isdid'], each['max'])
            reslist = c.execute(sql, sqldata).fetchall()
            log.info("新数据入库:" + str(sqldata) + sql + "|" + str(reslist))
            i += 1

    conn.commit()
    time.sleep(random.uniform(0.1, 0.3))
    print("完成抓取解析入库:" + url + " | 新增数据:(" + str(i) + ")")
    return 0
    # 分主题爬取 ps:[写真]、[动漫]
    # 进入具体页进行操作，这里最好要做通道先进先出，放一个地址进去，拿一个地址出来。
    # 用多线程，线程池 pool


def GetOnePage(host_url, table, wantdowntype):
    """
    从表table中查询未下载的进行下载
    :param host_url:    hots地址
    :param table:   表名
    :param wantdowntype:    想要下载的类型
    :return:
    """
    c = conn.cursor()
    allpages = []
    # myquery = {"_id": areanum, "isdid": 0}  # 根据id来设置处理的分区，这里以12【图片】分区先做
    sql = "SELECT ID, NAME, URL, STATUS, TYPE, ISDID, MAX FROM " + table + " WHERE TYPE = ? AND STATUS = ?;"
    sqldata = (wantdowntype, 1)
    reslist = c.execute(sql, sqldata).fetchall()
    log.debug(sql + str(sqldata))
    for each in reslist:
        # log.debug(str(reslist))
        # print(str(each[1]) + str(int(each[3]) == 1) + str(each[4] == "寫真"))
        if int(each[3]) == 1 and each[4] == "寫真":
            # log.info("进入[" + each[2] + "]预备下载：" + each[1])
            GetALLPic(host_url, table, each[0], each[1], each[2], each[5])


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
    log.info("进入[" + url + "]预备下载：" + pfname)
    response = requests.get(url, headers=head)
    log.info("" + purlpath + "响应码：" + str(response.status_code))
    if response.status_code != 200:
        log.warning(url + " 页面可能进不去了")
        return
    html = response.content.decode('GBK')
    content_soup = BeautifulSoup(html, 'lxml')
    p_list = content_soup.select('div.tpc_content.do_not_catch > img ')
    pmax = len(p_list)
    if pmax == 0:
        p_list = content_soup.select('div.tpc_content.do_not_catch > p > img ')
        pmax = len(p_list)
    if pmax == 0:
        log.warning("提取不到数据，可能方式不一样【" + str(url) + "】")
        return
    c = conn.cursor()
    sql = "UPDATE " + ptable.upper() + " SET  MAX = ?  WHERE ID = ?;"
    sqldata = (pmax, pid,)
    reslist = c.execute(sql, sqldata).fetchall()
    conn.commit()

    # log.info("pmax---" + str(pmax))
    start = time.time()
    for i in range(pdidcount, pmax):
        src = p_list[i]["data-src"]
        # log.info('src::' + str(src))
        downimg(src, pfname, i, pmax)  #
        sql = "UPDATE " + ptable.upper() + " SET  ISDID = ?  WHERE ID = ?;"
        sqldata = (i + 1, pid,)
        reslist = c.execute(sql, sqldata).fetchall()
        conn.commit()
    end = time.time()
    print(' %s\033[0;37;47m%s\033[0m 完成下载 %d!用时 %.2f 秒' % (Download_Path, pfname, pmax, (end-start)))
    sql = "UPDATE " + ptable.upper() + " SET STATUS = ?, ISDID = ?  WHERE ID = ?;"
    sqldata = (0, pmax, pid,)
    reslist = c.execute(sql, sqldata).fetchall()
    conn.commit()
    # print("下载完成:" + "[" + str(pid) + "](" + str(pmax) + ")")
    # log.info("下载完成:" + "[" + pfname + "](" + str(pmax) + ")")
    log.info(" 下载完成: [%s](%d) 用时 %.2f 秒 " % (pfname, pmax, (end-start)))


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
    start = time.time()
    try:
        r = requests.get(url, stream=True)
    except Exception as e:
        print(e.__str__())
    # log.info(str(r))
    # log.info("图片大小:" + r.headers["Content-Length"] + "byte")
    imgindexname = src.split('/')[-1]
    file_path = "Download" + "/" + fstr + "/" + imgindexname
    # my_file = Path(Download_Path + fstr)
    # print(Download_Path + " " + fstr)
    if r.status_code != 200:
        log.warning(src + "响应：" + r.status_code)
    # if not Path(Download_Path).is_dir():    # download目录
    #     os.makedirs(Download_Path)
    if not Path(Download_Path + "/" + fstr).is_dir():  # 单项目录
        os.makedirs(Download_Path + "/" + fstr)
    # 流模式，一块一块进行下载
    chunk_size = 1024  # 单次请求最大值
    content_size = int(r.headers['content-length'])  # 内容体总大小
    data_count = 0
    with open(Download_Path + "/" + fstr + "/" + imgindexname, 'wb') as file:
        for data in r.iter_content(chunk_size=chunk_size):
            file.write(data)
            data_count = data_count + len(data)
            now_jd = (data_count / content_size) * 100
            done = int(50 * data_count / content_size)
            print("\r %s\\\033[0;37;47m%s\033[0m\\%s 下载进度 - [%s%s] - (%d/%d) %d%% - (%d/%d) " % (Download_Path, fstr, imgindexname, "█" * done, " " * int(50 - done), data_count, content_size, now_jd, didcount+1, pmax), end=" ")
        log.info(Download_Path + "\\\033[0;37;47m" + fstr + "\033[0m\\" + imgindexname + " 下载成功(" + str(didcount + 1) + "/" + str(pmax) + ")")
    print()


def CheckMainUrl(table):
    """
    检查主页状态
    :return:
    """
    result = ''
    c = conn.cursor()
    m_can_use_urls = []  # 存放库中状态可用的url地址列表
    # maintable = mydb[MAIN_URL_TABLE]
    sql = "select id, url from " + str(table).upper() + " where status = ? order by id"
    args = (1,)
    reslist = c.execute(sql, args).fetchall()
    # 查询主页地址表中所有状态可用(1)的数据
    if len(reslist) > 0:
        for each in reslist:
            m_can_use_urls.append(each)

        for each in m_can_use_urls:
            m_re_htmls = GetMainPagaInfo(each[1])
            if len(m_re_htmls) == 0:
                m_can_use_urls.remove(each)
                # maintable.update_one({"_id": x["_id"]}, {"$set": {"status": 0}})
                sql = "UPDATE MAINURL SET  STATUS = 1  WHERE ID = ?;"
                sqldata = (each[0],)
                c.execute(sql, sqldata)
                conn.commit()
            else:
                return m_can_use_urls

    log.info("主页地址列表:" + str(m_can_use_urls))
    print("主页地址列表:" + str(m_can_use_urls))
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
            # sys.exit()
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
        DB_PATH = config[DATABASE]["DBPath"]
        DATABASE_NAME = config[DATABASE]['Database']
        MAIN_URL_TABLE = config[DATABASE]['MainURLTABLE']
        Area_Url_TABLE = config[DATABASE]['AreaurUrlTABLE']
        Picture_Url_TABLE = config[DATABASE]["PictureUrlTABLE"]
        # 下载配置
        Download_Path = config[Download]["DownloadPath"]
        # 指令配置
        SWITCH = config[INSTRUCTION].getint("Switch")
        GetPageNum = config[INSTRUCTION].getint("GetPageNum")

        # log = get_logger(config[LOG]["When"], config[LOG].getint("Interval"), config[LOG].getint("backupCount"))

        conn = None  # sqlite3.connect(DATABASE_NAME)
        # c = conn.cursor()
        conn = InitDatabase(conn, DB_PATH, DATABASE_NAME)

        myclient = pymongo.MongoClient(DB_PATH)
        # mydb = myclient[DATABASE_NAME]

        if SWITCH == 0:  # 初始化，不做爬虫
            pass

        elif SWITCH == 1:  # 显示可用网址
            mhost = CheckMainUrl(MAIN_URL_TABLE)
            if len(mhost) == 0:
                # 获取主页地址
                all_urls = GetMainUrl(DEFAULT_HOST, DEFAULT_URL_PATH)
                log.info("主页地址列表:" + str(all_urls))
                print("可用地址：" + str(all_urls))
            else:
                log.info("主页地址列表:" + str(mhost))
                print("可用地址：" + str(mhost))

        elif SWITCH == 2:  # 抓分区地址
            mhost = CheckMainUrl(MAIN_URL_TABLE)
            if len(mhost) == 0:
                # 获取主页地址
                mhost = GetMainUrl(DEFAULT_HOST, DEFAULT_URL_PATH)
                log.info("主页地址列表:" + str(mhost))
                print("可用地址：" + str(mhost))
            # else:
            #     log.info("主页地址列表:" + str(mhost))
            #     print("可用地址：" + str(mhost))
            # 解析主页 获取分区地址  GetMainPagaInfo() 改成返回本次获取的地址，解析的单独函数做
            mainhtml = GetMainPagaInfo(mhost[0][1])
            GetAreaurUrl(mainhtml, Picture_Url_TABLE)
            GetPageUrlFromDb(mhost[0][1], Area_Url_TABLE, 12, GetPageNum)  # 12是图片区的 _id
            # pictable = mydb[Picture_Url_TABLE]
            GetOnePage(mhost[0][1], Picture_Url_TABLE, "寫真")

        elif SWITCH == 3:  # 下载
            mhost = CheckMainUrl(MAIN_URL_TABLE)
            if len(mhost) == 0:
                # 获取主页地址
                mhost = GetMainUrl(DEFAULT_HOST, DEFAULT_URL_PATH)
                log.info("主页地址列表:" + str(mhost))
                print("可用地址：" + str(mhost))
            else:
                log.info("主页地址列表:" + str(mhost))
                print("可用地址：" + str(mhost))
            GetPageUrlFromDb(mhost[0][1], Area_Url_TABLE, 12, GetPageNum)  # 12是图片区的 _id
            # pictable = mydb[Picture_Url_TABLE]
            GetOnePage(mhost[0][1], Picture_Url_TABLE, "寫真")

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
        log.error('traceback.format_exc():\n%s' % traceback.format_exc())
    input("Press Any Key Exit!!!")
    log.info("Exit,退出--------------------\n\n")
