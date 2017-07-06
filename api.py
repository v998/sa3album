#!/usr/bin/env python
# coding:utf-8

"""
Created by ben on 2010/11/10 .
Copyright (c) 2010 http://sa3.org All rights reserved. 
"""

import settings
import mimetypes
import logging
import urllib
from functools import wraps
from util.handler import ApiHandler
import webapp2
from google.appengine.ext.webapp import util
from models import Album,Image,Setting as S

#api key check decorator
def key_requires(method):
    @wraps(method)
    def wrapper(self,*args,**kwargs):
        key = self.request.headers.get("key",None)
        s = S.get_s()
        if key and key in  s.api_keys:
            return method(self,*args,**kwargs)
        return self.error(403)
    return wrapper
        
def get_mime(name):
    return mimetypes.guess_type(name)[0] or 'application/octet-stream'

class ApiIndexHandler(ApiHandler):
    def get(self):
        self.response.out.write("api")
        
class AlbumApiHandler(ApiHandler):

    @key_requires
    def get(self):
        '''
        List all album
        '''
        self.template_value['albums']=[(album.name,album.slug,album.count,album.cover_url) for album in Album.all()]
        return self.render()
    
class ImageByAlbumApiHander(ApiHandler):
    @key_requires
    def get(self,slug):
        album = Album.get_by_key_name(slug)
        if album is None:
            return self.error(404)
        self.template_value['album'] = (album.name,album.slug,album.count,album.url)
        self.template_value['imgs']=[(img.name,img.size,img.f,img.s) for img in Image.all().filter('album =',album)]
        return self.render()
    
class UploadImageApiHandler(ApiHandler):
    @key_requires
    def put(self,slug,name):
        '''Put a image file
        '''
        album = Album.get_by_key_name(slug)
        if album is None:
            return self.error(404)
        name = urllib.unquote(name).decode('utf-8')
        mime = get_mime(name)
        bf = self.request.body
        if len(bf) > 1000*1000:
            return self.error(411)
        try:
            img = Image.add(album,name,mime,bf)
            self.template_value['key'] = img.key().name()
            self.template_value['f'] = img.f
            self.template_value['s'] = img.s
            return self.render()
        except:
            return self.error(500)
        
app = webapp2.WSGIApplication ([
                                        ('/api/', ApiIndexHandler),
                                        ('/api/album/',AlbumApiHandler),
                                        ('/api/album/(?P<slug>[0-9a-z]+)/',ImageByAlbumApiHander),
                                        ('/api/album/(?P<slug>[0-9a-z]+)/(?P<name>.+)',UploadImageApiHandler),
                                ], debug=settings.DEBUG)