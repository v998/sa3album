#!/usr/bin/env python
# coding:utf-8

"""
Created by ben on 2010/10/29 .
Copyright (c) 2010 http://sa3.org All rights reserved. 
"""

import getpass
import os
import sys

REMOTE_API_PATH = '/remote_api'

for x in ['C','D','E','F','G','H','I']:
    path = r'%s:\Program Files\Google\google_appengine' % x
    if os.path.exists(path):
        sys.path.append(path)
        sys.path.append(os.path.join(path,'lib','antlr3'))
        sys.path.append(os.path.join(path,'lib','fancy_urllib'))
        sys.path.append(os.path.join(path,'lib','yaml','lib'))
        break

from google.appengine.ext.remote_api import remote_api_stub

def attach(appid):
    def auth_func():
        return (raw_input('Email:'), getpass.getpass('Password:'))
    remote_api_stub.ConfigureRemoteApi(appid, REMOTE_API_PATH, auth_func, "%s.appspot.com" % appid)
    remote_api_stub.MaybeInvokeAuthentication()
    os.environ['SERVER_SOFTWARE'] = 'Development (remote_api)/1.0'
	
if __name__ == "__main__":
    attach('sa3album')