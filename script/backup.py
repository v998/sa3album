#!/usr/bin/env python
# coding:utf-8

"""
Created by ben on 2010/11/15 .
Copyright (c) 2010 http://sa3.org All rights reserved. 
"""
import os
from api import Album,Image,Sa3Album
import urllib

def backup(appid,key,path):
    if not os.path.exists(path):
        os.mkdir(path)
    url = "http://%s.appspot.com" % appid
    #url = "http://localhost:8095"
    sa3 = Sa3Album(url,key)
    albums = sa3.get_albums()
    for album in albums:
        album_path = os.path.join(path,album.name)
        if not os.path.exists(album_path):
            os.mkdir(album_path)
        imgs = sa3.get_img_by_album(album.slug)
        for img in imgs:
            urllib.urlretrieve(img.url_f,os.path.join(album_path,img.name))
            print "%s done" % img.name
    
if __name__=='__main__':
    appid = raw_input("Please Input Your APP ID:").strip()
    key = raw_input("Please Input Your KEY:").strip()
    if len(key) <> 16:
        print "Pleace check your key"
        exit()
    path = raw_input("Please Input backup path(such as F:/sa3album):")
    backup(appid,key,path)
   