#!/usr/bin/env python
# coding:utf-8

"""
Created by ben on 2010/10/26 .
Copyright (c) 2010 http://sa3.org All rights reserved. 
"""
import re
import logging
import random
import string
import os
import hashlib

from google.appengine.ext import db
from util.b36 import Base36
from util.base import filter_url
from util.thumb import resize
from google.appengine.api import images
from google.appengine.api import memcache

def get_md5(bf):
    return hashlib.md5(bf).hexdigest()

class Album(db.Model):
    '''
    sa3album Album Model
    '''
    slug = db.StringProperty()
    name = db.StringProperty()
    description = db.StringProperty()
    created = db.DateTimeProperty(auto_now_add=True)
    last_updated = db.DateTimeProperty(auto_now=True)
    cover_url = db.StringProperty()

    def put(self):
        self.slug = self.key().name()
        super(Album,self).put()
    
    @property
    def url(self):
        return "/b/%s/" % (self.slug)
    
    @property
    def m_url(self):
        return "/a/album/manage/%s/" % (self.slug)
    
    @property
    def count(self):
        return Image.all().filter('album =',self).count()
    
    @classmethod
    def add(cls,name):
        album = Album(name = name,key_name = Counter.get_max('album'))
        album.put()
        return album
    
class Image(db.Model):
    '''
    sa3album Photo Model
    '''
    album = db.ReferenceProperty(Album)
    name = db.StringProperty()
    mime = db.StringProperty()
    size = db.IntegerProperty()
    created = db.DateTimeProperty(auto_now_add=True)
    description = db.StringProperty()
    width = db.IntegerProperty()
    height =db.IntegerProperty()
    bf = db.BlobProperty()
    md5 = db.StringProperty(indexed=True)
    
    view_count = db.IntegerProperty(default=0) #view count
    
    def put(self):
        if self.is_saved():
            memcache.delete("f::%s" % self.key().name())
        super(Image,self).put()
    
    def delete(self):
        memcache.delete("s::%s" % self.key().name())
        memcache.delete("f::%s" % self.key().name())
        super(Image,self).delete()
    
    @property
    def url(self):
        return "/d/%s/" %(self.key().name())
    
    @property
    def s(self):
        ''' small image url '''
        return "/s/%s/" %(self.key().name())
    
    @property
    def download_url(self):
        '''downlaod url'''
        return "/e/%s/" % (self.key().name())
    
    @property
    def f(self):
        return "/f/%s/" %(self.key().name())
    
    @property
    def copyurl(self):
        return "http://%s/f/%s/" %(os.environ['HTTP_HOST'],self.key().name())
    
    @property
    def next(self):
        '''return next image'''
        return Image.all().filter('album =',self.album).order('created').filter('created >', self.created).get()
    
    @property
    def prev(self):
        '''return  prev image'''
        return Image.all().filter('album =',self.album).order('-created').filter('created <', self.created).get()
    
    @property
    def body(self):
        if self.bf:
            return self.bf
        bfs = ImageBF.all().filter('image =',self)
        bf = bfs.order('vid').fetch(10)
        if not bf:
            bf = self.bfs
        return ''.join([f.bf for f in bf])
    
    @property
    def des(self):
        '''
        Return image description,default :imgage name
        '''
        return self.description if  self.description else self.name
    
    def get_resize_img(self,w,h):
        key = "r::%s::%s::%s" % (self.key().name(),w,h)
        data = memcache.get(key)
        if data is None:
            logging.info("generate thumb image key:%s" % key)
            data = resize(self.body,(w,h))
            #make true data size < 1000000
            if len(data) < 1000000:
                memcache.set(key,data,3600*24)
        return data
        
    @classmethod
    def add(cls,album,name,mime,bf,**kwargs):
        #先檢查md5看圖片是否已經上傳過.
        md5 = get_md5(bf)
        img = Image.all().filter('md5 =',md5).get()
        if img and Setting.get_s().is_check_md5:
            logging.info("%s exist" % md5)
            return img
        
        key_name = Counter.get_max('image')
        size = len(bf)
        start =0
        splitelen=1000*1000 # 1M limit  
        if size <= splitelen:
            img = Image(album=album,name=name,mime=mime,bf=bf,key_name = key_name,size=size,**kwargs)
        else:
            img = Image(album=album,name=name,mime=mime,key_name = key_name,size=size,**kwargs)
            while start<img.size:
                ibf = ImageBF(bf=bf[start:start+splitelen],image = img,vid = start)
                ibf.put()
                start+=splitelen
            
        t = images.Image(image_data=bf)
        img.width = t.width
        img.height = t.height
        img.md5 = get_md5(bf)
        img.put()
        return img
    
    @classmethod
    def get_by_key_name_with_cache(cls,key_name):
        key = "f::%s" % key_name
        data = memcache.get(key)
        if data is None:
            data =Image.get_by_key_name(key_name)
            memcache.set(key,data,3600*24)
        return data
            
class ImageBF(db.Model):
    '''Image binary file'''
    bf = db.BlobProperty()
    image = db.ReferenceProperty(Image,collection_name='bfs')
    vid = db.IntegerProperty(default=0)
    
class Counter(db.Model):
    '''
    sa3album Counter Model
    '''
    name = db.StringProperty(required=False)
    value = db.StringProperty(default ='0') #use base36
    created = db.DateTimeProperty(auto_now_add =True)
    last_updated = db.DateTimeProperty(auto_now = True)
    
    def put(self):
        self.name = self.key().name()
        super(Counter,self).put()
        
    @classmethod
    def get_count(cls,key_name):
        obj = Counter.get_by_key_name(key_name)
        if obj is None:
            obj = Counter(key_name = key_name)
            obj.value = '0'
            obj.put()
        return obj
    
    @classmethod
    def get_max(cls,key_name):
        '''
        return max value +1
        '''
        obj = Counter.get_count(key_name)
        obj.value = Base36(obj.value)+1
        obj.put()
        return obj.value
    
class Setting(db.Model):
    name = db.StringProperty()
    theme = db.StringProperty()
    skey = db.StringProperty()
    is_anti_leech = db.BooleanProperty(default=False)
    allow_list = db.StringListProperty()
    anti_leech_img = db.StringProperty()
    copy_txt = db.StringProperty()
    api_keys = db.StringListProperty()
    
    #twitter settings
    user_key = db.StringProperty()
    user_secret = db.StringProperty()
    twitter_user = db.StringProperty()
    twitter_auto = db.BooleanProperty(default=False)

    is_check_md5 = db.BooleanProperty(default=False)
    
    version = '0.2.6'
    path = "http://%s" % os.environ['HTTP_HOST']
    
    @classmethod
    def get_s(cls):
        s = Setting.get_by_key_name('s')
        if s is None:
            skey = ''.join(random.sample(string.ascii_letters,16))
            s = Setting(key_name = 's',name ='sa3album',theme='gallery',skey=skey)
            s.put()
            #add default album
            Album.add('default')
        return s
    

if __name__=='__main__':
    pass