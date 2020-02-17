# -*- coding: UTF-8 -*-
#
import sqlite3

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
    p_list = content_soup.select('div.tpc_content.do_not_catch > p > img ')
    pmax = len(p_list)
    print("pmax=" + str(pmax))
    print("plist=\n" + str(p_list).replace('\n', ' ').replace(u'\xa0', ' ').replace(
                        u'\u200b', ''))


GetALLPic("cl.tu2s.tk", "ptable", "pid", "pfname", "htm_data/2002/8/3815594.html", 0)