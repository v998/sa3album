#!/usr/bin/env python
# coding:utf-8

"""
Created by ben on 2010/10/27 .
Copyright (c) 2010 http://sa3.org All rights reserved. 
"""
import datetime
import settings
import logging
import webapp2
from google.appengine.ext.webapp import template

register = template.create_template_register()

def default_album_img(value):
    '''
    if album.cover_url is None,return '/static/1.jpg'
    '''
    return '/static/1.jpg' if value is None else value

register.filter(default_album_img)

def datetz(value,arg):
    t = datetime.timedelta(seconds=3600*8) #8hour
    return template.django.template.defaultfilters.date(value+t, arg)

register.filter(datetz)

def humdate(value):
    tmp = datetime.datetime.now() -value
    if tmp.days > 0:
        return datetz(value,"m-d H:i")
    if tmp.seconds < 60:
        return u"%s 秒前" % tmp.seconds
    if tmp.seconds <3600:
        return u"約%s分鐘前" % (tmp.seconds/60)
    return u"約%s小時前" % (tmp.seconds/3600)

register.filter(humdate)

def humimg_width(value,max_width):
    return 'style="width:%spx"' % max_width if value > max_width else ''

def hum_width(value,max_width):
    return max_width if value > max_width else  value

register.filter(hum_width)

def human_count(value,max_count):
    return value if value < max_count else value[0:max_count]+'...'

register.filter(human_count)

register.filter(humimg_width)
    