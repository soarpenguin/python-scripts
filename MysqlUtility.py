#!/usr/bin/env python
#-*-coding:utf-8-*-

import MySQLdb
import sys
import ConfigParser


G_GROUP = 'mysql'
G_CONFIG = './config.ini'

def getConfig(file, group, configName):
    config = ConfigParser.ConfigParser()
    config.readfp(open(file, "rw"))
    configValue = config.get(group, configName.strip(' ').strip('\'').strip("\""))

    return configValue

host = getConfig(G_CONFIG,G_GROUP,'host')
port = getConfig(G_CONFIG,G_GROUP,'port')
user = getConfig(G_CONFIG,G_GROUP,'user')
passwd = getConfig(G_CONFIG,G_GROUP,'passwd')
dbname = getConfig(G_CONFIG,G_GROUP,'dbname')

def mysqlExec(sql, param):
    conn = MySQLdb.connect(host=host,user=user,passwd=passwd,port=int(port),connect_timeout=5,charset='utf8')
    conn.select_db(dbname)
    cursor = conn.cursor()
    if param <> '':
        cursor.execute(sql,param)
    else:
        cursor.execute(sql)
    conn.commit()
    cursor.close()
    conn.close()

def mysqlQuery(sql):
    conn = MySQLdb.connect(host=host,user=user,passwd=passwd,port=int(port),connect_timeout=5,charset='utf8')
    conn.select_db(dbname)
    cursor = conn.cursor()
    count = cursor.execute(sql)
    if count == 0 :
        result = 0
    else:
        result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result

def getOption(key):
    conn = MySQLdb.connect(host=host,user=user,passwd=passwd,port=int(port),connect_timeout=5,charset='utf8')
    conn.select_db(dbname)
    cursor = conn.cursor()
    sql="select value from options where name=+'"+key+"'"
    count = cursor.execute(sql)
    if count == 0 :
        result=0
    else:
        result=cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0]

