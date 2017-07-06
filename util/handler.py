#!/usr/bin/env python
# coding:utf-8

"""
Created by ben on 2010/10/26 .
Copyright (c) 2010 http://sa3.org All rights reserved. 
"""

import os
import logging
import traceback
import sys
import cgi
import re

import webapp2
from google.appengine.ext.webapp import template
from models import Setting
import json as simplejson

template.register_template_library('util.filter')

class NotFound(Exception):
    pass

class Forbidden(Exception):
    pass

def get_or_404(func,*args,**kwargs):
    obj = func(*args,**kwargs)
    if obj is None:
        raise NotFound()
    return obj

class PublicHandler(webapp2.RequestHandler):
    def initialize(self,request,response):
        webapp2.RequestHandler.initialize(self,request,response)
        self.settings =Setting.get_s()
        self.template_value = {'settings':self.settings}
        
    def render(self,template_file):
        self.response.out.write(self.get_render(template_file))
    
    def get_render(self,template_file):
        template_file = "themes/%s/%s" % (self.settings.theme,template_file)
        path = os.path.join(os.path.dirname(__file__), r'../',template_file)
        return template.render(path, self.template_value)        

    def error(self,code):
        self.response.clear()
        self.response.set_status(code)
        if code ==404:
            self.render("404.html")
        elif code ==403:
            self.render("403.html")
        elif code == 500:
            self.render("500.html")
            
    def handle_exception(self, exception, debug_mode):
        if isinstance(exception,NotFound):
            return self.error(404)
        elif isinstance(exception,Forbidden):
            return self.error(403)
        else:
            if debug_mode:
                lines = ''.join(traceback.format_exception(*sys.exc_info()))
                self.response.clear()
                self.response.out.write('<pre>%s</pre>' % (cgi.escape(lines, quote=True)))
            else:
                self.error(500)
                logging.exception(exception)
                
class FeedHandler(PublicHandler):
    def get_render(self,template_file):
        template_file = "themes/%s" % (template_file)
        path = os.path.join(os.path.dirname(__file__), r'../',template_file)
        return template.render(path, self.template_value)        
    

class ApiHandler(webapp2.RequestHandler):
    def initialize(self,request,response):
        webapp2.RequestHandler.initialize(self,request,response)
        self.settings =Setting.get_s()
        self.template_value = {}
        
    def render(self):
#        self.response.headers['Content-Type'] = 'application/json' 
        return self.response.out.write(simplejson.dumps(self.template_value))
        

class AdminHandler(PublicHandler):
    def get_render(self,template_file):
        template_file = "themes/admin/%s" % (template_file)
        path = os.path.join(os.path.dirname(__file__), r'../',template_file)
        return template.render(path, self.template_value)        
    
if __name__=='__main__':
    pass