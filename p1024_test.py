# -*- coding: UTF-8 -*-
#
import os
import sqlite3
from contextlib import closing
from pathlib import Path

import requests
from bs4 import BeautifulSoup

dbpath = "log"
dbfile = "p1024test.db"

conn = sqlite3.connect(dbpath + "/" + dbfile)
c = conn.cursor()


def out(outStr, *args):
    if(True):
        for var in args:
            if(var):
                outStr = outStr + ", " + str(var)
        print("db. " + outStr)
    return


def tselect(table, *args):
    sql = "SELECT "
    for i in range(0, len(args)):
        sql = sql + args[i]
        if i < len(args) - 1:
            sql += ", "

    sql = sql + " FROM " + table + ";"

    print("sql: " + sql)
    c.execute(sql)


def CheckMainUrl(table):
    """
    检查主页状态
    :return:
    """
    m_re_htmls = []
    m_can_use_urls = []  # 存放库中状态可用的url地址列表
    # maintable = mydb[MAIN_URL_TABLE]
    sql = "select id, url from " + table + " where status = ? order by id"
    args = (1,)
    reslist = c.execute(sql, args).fetchall()
    print(reslist)
    # 查询主页地址表中所有状态可用(1)的数据
    if len(reslist) > 0:
        for each in reslist:
            m_can_use_urls.append(each)

        for each in m_can_use_urls:
            # m_re_htmls = GetMainPagaInfo(each[1])
            if len(m_re_htmls) == 0:
                m_can_use_urls.remove(each)
                # maintable.update_one({"_id": x["_id"]}, {"$set": {"status": 0}})
                sql = "UPDATE " + table + " SET  STATUS = 0  WHERE ID = ?;"
                sqldata = (each[0],)
                print(c.execute(sql, sqldata).fetchall())
                conn.commit()

def tselect(table, *args):
    sql = "SELECT "
    for i in range(0, len(args)):
        sql = sql + args[i]
        if i < len(args) - 1:
            sql += ", "

    sql = sql + " FROM " + table + ";"

    print("sql: " + sql)
    c.execute(sql)

# out("insert into student values('id1" + str(1) + "', 'name1" + str(1) + "', 'birth1" + str(1) + "')")
# tselect("table", "ID", "NAME", "BIRTHDAY", "SEX", "CNBIRTHDAY", "ZI", "DIE", "DIEDAY", "SPOUSEID", "CHILDRENNUM", "CHILDREN"

# CheckMainUrl("MAINURL")

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
    imgindexname = src.split('/')[-1]
    file_path = "Download" + "/" + fstr + "/" + imgindexname
    print("sdhfalfghj")
    # print("\r Download" + "\\\033[0;37;47m" + fstr + "\033[0m\\" + imgindexname + " 下载成功(" + str(didcount + 1) + "/" + str(pmax) + ")", end=" ")
    try:
        r = requests.get(url, stream=True)
        imgsize = int(r.headers["Content-Length"])
        print("pic leng=" + str(imgsize))
    except Exception as e:
        print(e.__str__())
    # log.info(str(r))
    if not Path("Download" + "/" + fstr).is_dir():    # download目录
        os.makedirs("Download" + "/" + fstr)
    # print("Download" + "\\\033[0;37;47m" + fstr + "\033[0m\\" + imgindexname + " 下载成功(" + str(didcount + 1) + "/" + str(pmax) + ")")

    chunk_size = 1024  # 单次请求最大值
    content_size = int(r.headers['content-length'])  # 内容体总大小
    data_count = 0
    with open(file_path, 'wb') as file:
        for data in r.iter_content(chunk_size=chunk_size):
            file.write(data)
            data_count = data_count + len(data)
            now_jd = (data_count / content_size) * 100
            done = int(50 * data_count / content_size)

            print("\r %s\\\033[0;37;47m%s\033[0m\\%s 下载进度 - [%s%s] - (%d/%d) %d%%  - (%d/%d) " % ("Download", fstr, imgindexname, "█" * done, " " * int(50 - done), data_count, content_size, now_jd, didcount, pmax), end=" ")

    # with open("Download" + "/" + fstr + "/" + imgindexname, 'wb') as f:
    #     f.write(r.content)
    #     # log.info(imgindexname + " 下载成功(" + str(fstr) + "/" + str(pmax) + ")")
    #     os.system("")  # 变色玄学必须
    #     print("Download"  + "\\\033[0;37;47m" + fstr + "\033[0m\\" + imgindexname + " 下载成功(" + str(didcount + 1) + "/" + str(
    #         pmax) + ")")
        # log.info(Download_Path + "\\\033[0;37;47m" + fstr + "\033[0m\\" + imgindexname + " 下载成功(" + str(
        #     didcount + 1) + "/" + str(
        #     pmax) + ")")


url = "https://www.skeimg.com/u/20200211/22304229.jpg"
downimg(url, "pfname", 0, 0)