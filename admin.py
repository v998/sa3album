#!/usr/bin/env python
# coding:utf-8

"""
Created by ben on 2010/10/26 .
Copyright (c) 2010 http://sa3.org All rights reserved. 
"""
import settings
import logging
import string
import re
import random
import urllib
import os
from google.appengine.api import urlfetch,memcache
import webapp2
from google.appengine.ext.webapp import util
from util.handler import AdminHandler,get_or_404
from util.paging import PagedQuery
from util.base import filter_url
from util.getimageinfo import getImageInfo
from util import oauth
import json as simplejson
from models import Album,Image,Setting as S

PAGESIZE = 15
APPLICATIOIN_KEY = '0aOKVWcEj31dmDo6p1Wg'
APPLICATION_SECRET='UOoAPmcet0fLOOEQtV3axTUEbq1DZGGvIdjo7Yxyz4'

def get_themes():
    path = os.path.join(os.path.dirname(__file__),'themes')
    themes = os.listdir(path)
    themes.remove('admin')
    for theme in themes:
        if not os.path.isdir(os.path.join(path,theme)):
            themes.remove(theme)
    return themes

class MainHandler(AdminHandler):
    def get(self):
        self.render('index.html')
        
class AlbumIndexHandler(AdminHandler):
    def get(self):
        self.template_value['albums']=Album.all()
        self.render('album.html')
        
class AlbumAddHandler(AdminHandler):
    def get(self):
        self.render('album_add.html')
    
    def post(self):
        name = self.request.get("name")
        #check name 
        name = name.strip()
        if len(name)==0:
            self.template_value['error'] = True
            self.template_value['name']=name
            return self.render('album_add.html')
        album = Album.add(name)
        self.redirect("/a/album/")
        
class AlbumEditHandler(AdminHandler):
    
    def get(self):
        key = self.request.get("key")
        self.template_value['key']=key
        self.template_value['album']=get_or_404(Album.get,key)
        self.render('album_edit.html')
        
    def post(self):
        key = self.request.get("key")
        name = self.request.get("name")
        name = name.strip()
        if len(name)==0:
            self.template_value['error'] = True
            self.template_value['name']=name
            return self.render('album_add.html')
        
        album = get_or_404(Album.get,key)
        album.name = name
        album.put()
        self.redirect("/a/album/")
        
class AlbumDelHandler(AdminHandler):
    def get(self):
        key = self.request.get('key')
        album = get_or_404(Album.get,key)
        imgs = Image.all().filter('album =',album)
        for img in imgs:
            img.delete()
        album.delete()
        self.redirect("/a/album/")
        
class AlbumSetCoverHandler(AdminHandler):
    def get(self):
        album = get_or_404(Album.get_by_key_name,self.request.get("album"))
        img = get_or_404(Image.get_by_key_name,self.request.get("img"))
        album.cover_url = img.s
        album.put()
        self.redirect("/a/album/")
        
    def post(self):
        album = get_or_404(Album.get_by_key_name,self.request.get("album"))
        img = get_or_404(Image.get_by_key_name,self.request.get("img"))
        album.cover_url = img.s
        album.put()
        self.response.out.write(img.name)
        
class CommonImageUploadHandler(AdminHandler):
    def get(self):
        self.template_value['albums']=Album.all()
        self.render("upload_common.html")

    def post(self):
        bf = self.request.get("file")
        if not bf :
            return self.redirect("/a/upload/common/")
        name = unicode(self.request.body_file.vars['file'].filename,'utf-8')
        mime = self.request.body_file.vars['file'].headers['content-type']
        #handle file > 1M
        if  mime.find('image')==-1:
            self.redirect("/a/upload/common/")
        album = Album.get_by_key_name(self.request.get("album"))
        Image.add(album,name,mime,bf)
        self.redirect(album.url)
        
class ImageManageHandler(AdminHandler):
    def get(self,key_name):
        album = get_or_404(Album.get_by_key_name,key_name)
        p = int(self.request.get("p","1"))
        imgs = PagedQuery(Image.all().filter("album =",album).order('-created'),PAGESIZE)
        temp = imgs.fetch_page(p)
        self.template_value['album']=album
        self.template_value['prev']=p-1 if p>1 else None
        self.template_value['next'] = p +1 if len(temp) == PAGESIZE else None
        self.template_value['imgs']=temp
        self.template_value['ps'] = range(1,imgs.page_count()+1)
        self.template_value['current_p'] = p
        self.render('album_manage.html')
        
class ImageUploadHandler(AdminHandler):
    def get(self):
        self.template_value['albums']=Album.all()
        self.template_value['album_select'] = self.request.get("album","")
        self.render('upload.html')
        
class ImageHtml5UploadHandler(AdminHandler):
    def get(self):
        self.template_value['albums']=Album.all()
        self.template_value['album_select'] = self.request.get("album","")
        self.render('upload-html5.html')
        
    def post(self):
        album = self.request.get("album")
        name = urllib.unquote(self.request.get("qqfile"))
        bf = self.request.body
        mime = getImageInfo(bf)[0]
        album = Album.get_by_key_name(album)
        if mime.find('image') > -1 and album:
            img =Image.add(album,name,mime,bf)
            return self.response.out.write("{success:true}")
        return self.response.out.write("{success:false}")
    
class ImageWebUploadHandler(AdminHandler):
    def get(self):
        u = self.request.get("u") 
        if u  :
            self.template_value['albums'] = Album.all()
            self.template_value['u']=u
            self.template_value['name']= u.split("/")[-1] or "aaaa"+ mime.split("/")[-1]
            return self.render("upload-web2.html")
        self.render("upload-web.html")
        
    def post(self):
        album = self.request.get("album")
        u = self.request.get("u")
        des = self.request.get("des")
        name = self.request.get("name")
        retries = 3
        result = None
        try:
            result = urlfetch.fetch(u,deadline=10)
        except:
            retries -=1
            if retries > 0:
                result = urlfetch.fetch(u,deadline=10)
            
        if result and result.status_code == 200:
            album = Album.get_by_key_name(album)
            bf = result.content
            mime = getImageInfo(bf)[0]
            if mime.find("image") <0:
                raise Exception(u"不是正確的圖片")
            img = Image.add(album,name,mime,bf,**{"description":des})
            self.redirect(album.m_url)
        else:
            self.response.out.write(u"此地址抓取錯誤")
        
class ImageDelHandler(AdminHandler):
    def get(self):
        key_name = self.request.get("key")
        img = get_or_404(Image.get_by_key_name,key_name)
        img.delete()
        self.redirect(img.album.m_url)
    
    def post(self):
        img = get_or_404(Image.get_by_key_name,self.request.get("key"))
        img.delete()
        self.response.out.write("ok")
        
class ImageUpdateDesHandler(AdminHandler):
    def get(self):
        self.response.out.write("image update des handler")
    
    def post(self):
        des = self.request.get("des")
        key = self.request.get("key")
        img = Image.get_by_key_name(key)
        img.description = des
        img.put()
        logging.info("%s update description" % key)
        self.response.out.write("ok")
        
class SystemSettingsHandler(AdminHandler):
    def get(self):
        self.template_value['themes'] = get_themes()
        logging.info(self.template_value)
        self.render('settings.html')
        
    def post(self):
        name = self.request.get("name").strip()
        theme = self.request.get("theme-name").strip()
        s=  S.get_s()
        s.name = name
        s.theme = theme
        s.is_check_md5 = True if self.request.get("is_check_md5") else False
        s.put()
        self.redirect("/a/settings/")
        
class AntiLeechSettingsHandler(AdminHandler):
    def get(self):
        self.template_value['allow_list'] = '\n'.join(self.settings.allow_list)
        self.render('antileech.html')
        
    def post(self):
        is_anti_leech = self.request.get("is_anti_leech")
        allow_list = self.request.get("allow_list")
        anti_leech_img = self.request.get("anti_leech_img")
        
        s = S.get_s()
        s.is_anti_leech =  True if is_anti_leech else False
        s.allow_list = [rule.replace("\r","") for rule in allow_list.split("\n")]
        s.anti_leech_img = anti_leech_img
        s.put()
        self.redirect("/a/antileech/")
    
class CopySettingHandler(AdminHandler):
    def get(self):
        self.template_value['copy_txt'] = self.settings.copy_txt
        self.render('copy.html')
    
    def post(self):
        copy_txt = self.request.get("copy_txt")
        s = S.get_s()
        s.copy_txt = copy_txt
        s.put()
        self.redirect("/a/copy/")
        
class ApiSettingHandler(AdminHandler):
    def get(self):
        s = S.get_s()
        self.template_value['keys'] = s.api_keys
        self.render('api.html')
        
    def post(self):
        s = S.get_s()
        s.api_keys.append(''.join(random.sample(string.ascii_letters,16)))
        s.put()
        self.redirect("/a/api/")
    
class ApiSettingRemoveHandler(AdminHandler):
    def get(self):
        key = self.request.get("key")
        s = S.get_s()
        s.api_keys.remove(key)
        s.put()
        self.redirect("/a/api/")
        
callback_url = "http://%s/a/twitter/verify/" %  os.environ['HTTP_HOST']
client = oauth.TwitterClient(APPLICATIOIN_KEY, APPLICATION_SECRET,callback_url)   
class TwitterMainHandler(AdminHandler):
    def get(self):
        self.response.out.write("hi")
        
    def post(self):
        self.redirect(client.get_authorization_url())
    
class TwitterVerifyHandler(AdminHandler):
    def get(self):
        auth_token = self.request.get("oauth_token")
        auth_verifier = self.request.get("oauth_verifier")
        user_info = client.get_user_info(auth_token, auth_verifier=auth_verifier)
        s = S.get_s()
        s.user_key = user_info.get("token")
        s.user_secret = user_info.get("secret")
        s.twitter_user= user_info.get("username")
        s.put()
        self.redirect("/a/settings/")
        
class TwitterUpdateHandler(AdminHandler):
    def post(self):
        key = self.request.get("key")
        img = Image.get_by_key_name(key)
        if img is None:
            return self.response.out.write("error")
        status = "%s %s" % (img.des,img.copyurl)
        url = "http://twitter.com/statuses/update.json"
        result = client.make_request(url=url,
                                                    token=self.settings.user_key,
                                                    secret=self.settings.user_secret,
                                                    additional_params={'status':status},
                                                    method=urlfetch.POST,
                                                    )
        self.response.out.write(result.content)

class FlushMemcacheHandler(AdminHandler):
    def post(self):
        memcache.flush_all()
        self.redirect("/a/settings/")
        
app = webapp2.WSGIApplication ([
                                        ('/a/', MainHandler),
                                        ('/a/album/',AlbumIndexHandler),
                                        ('/a/album/add/',AlbumAddHandler),
                                        ('/a/album/edit/',AlbumEditHandler),
                                        ('/a/album/del/',AlbumDelHandler), 
                                        ('/a/album/manage/(?P<key_name>[a-z0-9]+)/',ImageManageHandler),
                                        
                                        ('/a/album/set/',AlbumSetCoverHandler),
                                        
                                        ('/a/upload/common/',CommonImageUploadHandler),
                                        ('/a/upload/',ImageUploadHandler),
                                        ('/a/upload5/',ImageHtml5UploadHandler),
                                        ('/a/g/',ImageWebUploadHandler),
                                        ('/a/img/del/',ImageDelHandler),
                                        ('/a/img/updatedes/',ImageUpdateDesHandler),
                                        ('/a/settings/',SystemSettingsHandler),
                                        ('/a/antileech/',AntiLeechSettingsHandler),
                                        ('/a/copy/', CopySettingHandler),
                                        ('/a/api/',ApiSettingHandler),
                                        ('/a/api/remove/',ApiSettingRemoveHandler),
                                        
                                        ('/a/twitter/',TwitterMainHandler),
                                        ('/a/twitter/verify/',TwitterVerifyHandler),
                                        ('/a/twitter/update/',TwitterUpdateHandler),
                                        
                                        ('/a/flush/',FlushMemcacheHandler),
                                ], debug=settings.DEBUG)