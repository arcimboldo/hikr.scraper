#!/usr/bin/env python
# -*- coding: utf-8 -*-#
#
#
# Copyright (C) 2017, Centralway AG. All rights reserved.

__docformat__ = 'reStructuredText'
__author__ = 'Antonio Messina <antonio.messina@centralway.com>'

import requests
from bs4 import BeautifulSoup
import re
import argparse
import logging
import sys
import csv
import asyncio
import aiohttp


log = logging.getLogger()
log.addHandler(logging.StreamHandler(stream=sys.stderr))
log.setLevel(logging.INFO)

BASEURL='http://www.hikr.org/'
DEFAULT_REGION='Schweiz'


def get_regions():
    regions = {}
    region_regex = re.compile('\s*([^(]+)\s*(\(.*)?')

    resp = requests.get(BASEURL + 'region1.html')
    soup = BeautifulSoup(resp.content, 'html.parser')
    for line in soup.find(id='contentmain_l').find_all('a'):
        link = line.get('href')
        region = line.getText()
        region = region_regex.search(region).group(1).strip()

        regions[region] = link
    return regions


def list_hikes_in_page(data):
    # TITLE, TN, PD/AD, II, DATE
    soup = BeautifulSoup(data, 'html.parser')
    hikes = []
    for hike in soup.select('div[class="content-center"] div[class=content-list] div[class=content-list-intern]'):        
        title = hike.select('div strong a')[0].getText().strip()
        link = hike.select('div strong a')[0].attrs.get('href')
        row = hike.select('table[class="content-list-intern_table"] tr')[0]
        updown, difficulty, date = row.select('td')
        date = date.getText().strip()
        updown = updown.getText().strip()

        t, m, c = '', '', ''
        for td in difficulty.select('span'):
            tdtitle = td.attrs.get('title')
            if tdtitle == 'Wandern Schwierigkeit':
                t = td.getText().strip()
            elif tdtitle == 'Hochtouren Schwierigkeit':
                m = td.getText().strip()
            elif tdtitle == 'Klettern Schwierigkeit':
                c = td.getText().strip()
        hikes.append([title, t, m, c, date, updown, link])

    return hikes


def list_hikes(region, dump, skip=0):
    regions = get_regions()
    if region not in regions:
        raise Exception("Region '%s' not found", region)

    resp = requests.get(regions[region])
    soup = BeautifulSoup(resp.content, 'html.parser')

    # Find the number of pages
    lastpage = 1
    if soup.select('div[class="navigator"]'):
        end = soup.select('div[class="navigator"] a[class="end"]')
        if end:
            lastpage = int(end[0].getText())
        else:
            links = soup.select('div[class="navigator"] a')
            if len(links) > 2:
                last = links[-2]
                lastpage = int(last.getText())
    log.info("Lastpage: %d" % lastpage)

    hikes = []
    # for each extra page, open the page and append to hikes
    # loop = asyncio.get_event_loop()

    # async def getpage(session, page):
    #     async with session.get('%s?skip=%d' % (regions[region], (page-1)*10)) as resp:
    #         body = await resp.text()
    #     h = list_hikes_in_page(body)
    #     dump.writerows(h)
    #     return h

    # async def get_all_pages(session, lastpage, skip):
    #     hikes = []
    #     start = skip//10 +1
    #     results = await asyncio.wait([loop.create_task(getpage(session, page)) for page in range(start, lastpage+1)])
    #     for h in results:
    #         hikes.extend(h)
    #     return hikes

    # conn = aiohttp.TCPConnector(limit=30)
    # with aiohttp.ClientSession(loop=loop, connector=conn) as session:
    #     hikes = loop.run_until_complete(get_all_pages(session, lastpage, skip))
    start = skip
    for page in range(start, lastpage+1):
        # remove .html
        url = regions[region][:-5]
        url = '%s/tour/?skip=%d&' % (url, page*10)

        resp = requests.get(url)

        h = list_hikes_in_page(resp.content)
        log.info("Page %d parsed: %d hikes" % (page, len(h)))
        dump.writerows(h)
        hikes.extend(h)
    return hikes


def setup():
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--region', default=DEFAULT_REGION, help='Region to use. Default: %(default)s.', choices=get_regions())
    parser.add_argument('-o', '--output', default='')
    parser.add_argument('--skip', default=0, type=int)
    opts = parser.parse_args()
    return opts


class Dumper:
    def writerows(self, rows):
        for row in rows:
            print(str.join(' ', row))

if __name__ == "__main__":
    opts = setup()
    dump = Dumper()
    if opts.output:
        fd = open(opts.output, 'w+')
        dump = csv.writer(fd)
    data = list_hikes(opts.region, dump, skip=opts.skip)
        
