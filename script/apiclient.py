#!/usr/bin/env python
# coding:utf-8

"""
Created by ben on 2010/11/10 .
Copyright (c) 2010 http://sa3.org All rights reserved. 
"""
import httplib
import os

def upload(name):
    connection = httplib.HTTPConnection('localhost:8095')
    connection.request('PUT','/api/album/2/%s' % name,open(name,'rb'),{'key':'horzMQsyJFgtWBNG'})
    result = connection.getresponse().read()
    print result


if __name__=='__main__':
    upload("1.jpg")