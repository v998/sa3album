#!/usr/bin/env python
# coding:utf-8

"""
Created by ben on 2010/11/29 .
Copyright (c) 2010 http://sa3.org All rights reserved. 
"""
from google.appengine.api import images
import logging

def get_offset(value):
    return int(max(0,min(value*0.5/1,value)))

def toint(number):
    """
    Helper to return rounded int for a float or just the int it self.
    """
    if isinstance(number, float):
        number = round(number, 0)
    return int(number)

def resize(data,size):
    '''
    Resize Image
    @params img - images.Image Data
    @size -tuple such as (75,75)
    @return images.Image object
    '''
    r_x,r_y = size
    r_x = max(0,r_x)
    r_y = max(0,r_y)
    
    if r_x == 0 and r_y==0:
        return data
    img = images.Image(image_data = data)
    x,y = img.width,img.height
    r_x = min(r_x,x)
    r_y = min(r_y,y)
    if r_x ==0:
        img.resize(height=r_y)
    elif r_y ==0:
        img.resize (width = r_x)
    else:
        
        factor = max(r_x*1.0/x,r_y*1.0/y)
        if factor <1:
            #need resize
            x = toint(x * factor)
            y = toint(y * factor)
            img.resize(width= x,height = y)
            
        offset_x = get_offset(x - r_x)
        offset_y = get_offset(y - r_y)
        logging.info("%s:%s" % ((offset_x+r_x)*1.0/x,(offset_y+r_y)*1.0/y))
        img.crop(
            offset_x*1.0/x,
            offset_y*1.0/y,
            (offset_x+r_x)*1.0/x,
            (offset_y+r_y)*1.0/y,
            )
    return img.execute_transforms(output_encoding=images.JPEG)

if __name__=='__main__':
    pass