#!/usr/bin/env python
# coding:utf-8

"""
Created by ben on 2010/11/10 .
Copyright (c) 2010 http://sa3.org All rights reserved. 
"""

import urllib2
import json as simplejson

class Album():
    def __init__(self,url,name,slug,count,cover_url):
        self.url = url
        self.name = name
        self.slug = slug
        self.count = count
        self.cover_url = cover_url
        
class Image():
    def __init__(self,url,img):
        self.url = url
        self.name = img[0]
        self.size = img[1]
        self.f = img[2]
        self.s = img[3]
        
    @property
    def url_f(self):
        return self.url+self.f
    
    @property
    def url_s(self):
        return self.url+self.s

class Sa3Album():
    def __init__(self,url,key):
        self.url = url
        self.key = key
        
    def req(self,url):
        req = urllib2.Request(url,headers={"key":self.key})
        result = urllib2.urlopen(req).read()
        return simplejson.loads(result)
            
    
    def get_albums(self):
        ret = self.req(self.url+'/api/album/')
        albums = [Album(self.url,album[0],album[1],album[2],album[3]) for album in ret['albums']]
        return albums
    
    def get_img_by_album(self,slug):
        ret = self.req(self.url +'/api/album/%s/' % slug)
        imgs = [Image(self.url,img) for img in ret['imgs']]
        return imgs
    
if __name__=='__main__':
    sa3 = Sa3Album('http://localhost:8095','horzMQsyJFgtWBNx')
    albums = sa3.get_albums()
    print albums