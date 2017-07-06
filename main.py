#!/usr/bin/env python
# coding:utf-8

"""
Created by ben on 2010/10/26 .
Copyright (c) 2010 http://sa3.org All rights reserved. 
"""

import settings
import logging
import re
import urllib
import fnmatch
import datetime
from google.appengine.api import users
import webapp2
from google.appengine.ext.webapp import util
import json as simplejson
from util.handler import PublicHandler,get_or_404,FeedHandler
from util.getimageinfo import getImageInfo
from util.paging import PagedQuery
from util.thumb import resize
from models import Album,Image

PAGESIZE = 24 
def format_date(dt):
    return dt.strftime('%a, %d %b %Y %H:%M:%S GMT')

def check_referer(request,referer):
    referer = referer.lower()
    for rule in request.settings.allow_list:
        if fnmatch.fnmatch(referer,rule):
            return True
    logging.info("%s forbidden" % referer)
    return False

class IndexHandler(PublicHandler):
    def get(self):
        
        self.template_value['albums']=Album.all()
        self.render('index.html')
        
class AlbumListHandler(PublicHandler):
    def get(self,key_name):
        p = int(self.request.get('p','1'))
        album = get_or_404(Album.get_by_key_name,key_name)
        self.template_value['album']=album
        PAGESIZE = 500 if self.settings.theme <> 'default' else 24
        imgs = PagedQuery(Image.all().filter('album = ',album),PAGESIZE)
        temp = imgs.fetch_page(p)
        self.template_value['prev']=p-1 if p>1 else None
        self.template_value['next'] = p +1 if len(temp) == PAGESIZE else None
        self.template_value['imgs']  = temp
        self.template_value['ps'] = range(1,imgs.page_count()+1)
        self.template_value['current_p'] = p
        self.render('album.html')
    
class ImageViewHandler(PublicHandler):
    '''Handler show Image'''
    def get(self,size,key_name):
        referer = self.request.headers.get("Referer")
        if  self.settings.is_anti_leech and referer is not None and (not check_referer(self,referer)):
            #將圖片替換為禁止盜鏈的圖片
            key_name = self.settings.anti_leech_img
        #handler If-None-Match
        if size =='s':
            w,h = 120,120
        else:
            w = int(self.request.get("w","0"))
            h = int(self.request.get("h","0"))
        
        key="%s:%s:%s" % (w,h,key_name)
        if_none_match = self.request.headers.get("If-None-Match")
        if if_none_match and if_none_match ==key:
            return self.error(304)
        img = get_or_404(Image.get_by_key_name_with_cache,key_name)
        img.view_count+=1
        img.put()
        mime = str(img.mime) if w ==0 and h==0 else "image/jpeg"
        bf = img.get_resize_img(w,h)
        logging.info(len(bf))
        self.response.headers['Content-Type'] = mime
        self.response.headers['ETag']=key
        self.response.headers['Cache-Control']="max-age=315360000"
        self.response.headers['Last-Modified']=format_date(img.created)
        self.response.out.write(bf)
        
class ImageResizeTestHandler(PublicHandler):
    def get(self,key_name):
        img = get_or_404(Image.get_by_key_name_with_cache,key_name)
        w = int(self.request.get("w","0"))
        h = int(self.request.get("h","0"))
        mime = 'image/jpeg' 
        self.response.headers['Content-Type'] = mime
        self.response.out.write(resize(img.body,(w,h)))
        
class ImagePageHandler(PublicHandler):
    def get(self,key_name):
        self.template_value['img']=get_or_404(Image.get_by_key_name,key_name)
        self.render('img.html')
        
class ImageUploadHandler(PublicHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'application/json'       
        self.response.out.write(simplejson.dumps({'result':False}))           
         
    def post(self):
        skey = self.request.get("skey")
        logging.info(skey)
        if skey != self.settings.skey:
            self.response.out.write("")
        try:
            album = self.request.get("album")
            bf = self.request.get("Filedata")
            name = unicode(self.request.body_file.vars["Filedata"].filename,'utf-8')
            mime = getImageInfo(bf)[0]
            album = Album.get_by_key_name(album)
            img =Image.add(album,name,mime,bf)
            self.response.out.write(img.copyurl)
        except:
            self.response.out.write("")
                                    
class ImageDownloadHandler(PublicHandler):
    def get(self,key_name):
        img = get_or_404(Image.get_by_key_name_with_cache,key_name)
        self.response.headers['Content-Type'] = "application/octet-stream; CHARSET=utf8"
        self.response.headers['Content-Disposition']='attachment; filename=%s' % img.name.encode('utf-8')
        self.response.out.write(img.body)
        
class LogoutHandler(PublicHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            return self.redirect(users.create_logout_url("/"))
        
class LoginHandler(PublicHandler):
    def get(self):
        user = users.get_current_user()
        if user and users.is_current_user_admin() :
            return self.redirect("/a/upload/")
        return self.redirect(users.create_login_url("/a/upload/"))
    
class FeedIndexHandler(FeedHandler):
    def get(self):
        imgs = Image.all().order('-created').fetch(10)
        self.template_value['imgs']=imgs
        self.template_value['lastupdated'] = imgs[0].created if len(imgs) >0 else datetime.datetime.now()
        self.response.headers['Content-Type'] = "application/atom+xml"
        self.response.out.write(self.get_render("rss.xml"))
    
class FeedAlbumHandler(FeedHandler):
    def get(self,key_name):
        album = get_or_404(Album.get_by_key_name,key_name)
        imgs = Image.all().filter('album =',album).order('-created').fetch(10)
        self.template_value['imgs']=imgs
        self.template_value['lastupdated'] = imgs[0].created if len(imgs) >0 else datetime.datetime.now()
        self.response.headers['Content-Type'] = "application/atom+xml"
        self.response.out.write(self.get_render("rss.xml"))
        
class IEHandler(FeedHandler):
    def get(self):
        self.response.out.write(self.get_render("ie.html"))
        
       
app = webapp2.WSGIApplication ([
                                        ('/', IndexHandler),
                                       ('/b/(?P<key_name>[a-z0-9]+)/?',AlbumListHandler), 
                                       ('/(?P<size>[f|s])/(?P<key_name>[a-z0-9]+)/?',ImageViewHandler),
                                       ('/d/(?P<key_name>[a-z0-9]+)/?',ImagePageHandler),
                                       #('/t/(?P<key_name>[a-z0-9]+)/?',ImageResizeTestHandler),
                                       ('/e/(?P<key_name>[a-z0-9]+)/?',ImageDownloadHandler),
                                       ('/u/',ImageUploadHandler),
                                       ('/logout/',LogoutHandler),
                                       ('/login/',LoginHandler),
                                       ('/ie/',IEHandler),
                                       
                                       #Feed
                                       (r'/feed/?',FeedIndexHandler),
                                       (r'/feed/(?P<key_name>[a-z0-9]+)/?',FeedAlbumHandler),
                                ], debug=settings.DEBUG)