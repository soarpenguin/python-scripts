#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Import system libs
import re

class WWW():
    def __init__(self):
        pass

    def get_domain(self, site):
        if site.startswith('https://'):
            site = site[8:-1]
        elif site.startswith('http://'):
            site = site[7:-1]
        return site.split('/')[0]

    def is_url_format(self, url):
        regex = """
               ^ #必须是串开始
               (?:http(?:s)?://)? #protocol
               (?:[\w]+(?::[\w]+)?@)? #user@password
               ([-\w]+\.)+[\w-]+(?:.)? #domain
               (?::\d{2,5})? #port
               (/?[-:\w;\./?%&=#]*)? #params
               $
               """
        result = re.search(regex, url, re.X|re.I)
        if result:
            return True
        else:
            return False

