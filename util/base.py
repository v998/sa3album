#!/usr/bin/env python
# coding:utf-8

"""
Created by ben on 2010/10/27 .
Copyright (c) 2010 http://sa3.org All rights reserved. 
"""
import re
import unicodedata

def filter_url(s):
    '''
    url contains [a-z0-9-]
    can not startswith or endswith '-'
    '''
    if not isinstance(s,str):
        s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore')
    return  re.sub(r'[^a-z0-9]+','-',s.lower()).strip('-')


if __name__=='__main__':
    pass