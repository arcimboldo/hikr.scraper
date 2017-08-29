#!/usr/bin/env python
# -*- coding: utf-8 -*-#
#
#
# Copyright (C) 2017, Centralway AG. All rights reserved.

__docformat__ = 'reStructuredText'
__author__ = 'Antonio Messina <antonio.messina@centralway.com>'

import pandas as pd
import re

df = pd.read_csv('ch.csv', names=['title', 't', 'm', 'c', 'date', 'updown', 'link'])

df['t'] = df.t.fillna('T1')
df['hard'] = df.t.apply(lambda x: int(x[1]) > 3)

upre = re.compile('.*↑([0-9]+)[^0-9]')
downre = re.compile('.*↓([0-9]+)[^0-9]')
    
df['up'] = df.updown.apply(lambda x: int(upre.search(x).group(1)) if upre.match(str(x)) else 0)
df['down'] = df.updown.apply(lambda x: int(downre.search(x).group(1)) if downre.match(str(x)) else 0)
df['climbing'] = df.c.apply(lambda x: True if re.match('(^([V4-9]|IV)|.*X)', str(x)) else False)

hardhikes = df[(df.hard == True) & (df.climbing == False)]

hardhikes.to_csv('ch_hard.csv', index=False)
