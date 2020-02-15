# -*- coding: UTF-8 -*-
#
import sqlite3

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


def IsHaveHashData(table, *args):
    """
    查询db中table有没有dat这条数据
    :param table:
    :param args:
    :return:
    """
    sql = "select id from " + table + " where " # status = ? order by id"
    for i in range(0, len(args)):
        if i == len(args) - 1:
            sql = sql + str(args[i][0]) + " = ? " + ";"
        else:
            sql = sql + "\'" + str(args[i][0]) + "\'" + " = ?" + " and "
    sqldata = ()
    for i in range(0, len(args)):
        sqldata += (args[i][1],)

    print(sql, sqldata)
    reslist = c.execute(sql, sqldata).fetchall()

    if len(reslist) > 0:
        print("表:" + table + "\t已有数据:" + str(args))
        return True
    else:
        return False

print(IsHaveHashData("MAINURL", ("url", "cl.fc55.ga")))