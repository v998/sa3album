#!/usr/bin/env python
# coding:utf-8

"""
Created by ben on 2010/10/26 .
Copyright (c) 2010 http://sa3.org All rights reserved. 
"""

class Base36():
    def __init__(self,num):
        self.s ="0123456789abcdefghijklmnopqrstuvwxyz"
        if not set(num) <= set(self.s):
            raise ValueError('number must be in "[0-9a-z]"')
        self.num = num
    
    def base10(self):
        '''
        return base 10 number
        '''
        return int(self.num,36)
    
    def __len__(self):
        return len(self.num)
    
    def base36(self,num):
        if not isinstance(num,(int,long)):
            raise TypeError('num must be an integer')
        if num < 0:
            raise ValueError('num must be positive')
        if num < 36:
            return self.s[num]
        b=''
        while num !=0:
            num,i = divmod(num,36)
            b = self.s[i]+b
        return b
    
    def __add__(self,num):
        if isinstance(num,(int,long)):
            return self.base36(int(self.num,36)+num)
        return self.base36(int(self.num,36)+int(num,36))


if __name__=='__main__':
    pass