#-*- coding: utf-8 -*-

###########################################################################
##                                                                       ##
## Copyrights Frederic Rodrigo 2012                                      ##
##                                                                       ##
## This program is free software: you can redistribute it and/or modify  ##
## it under the terms of the GNU General Public License as published by  ##
## the Free Software Foundation, either version 3 of the License, or     ##
## (at your option) any later version.                                   ##
##                                                                       ##
## This program is distributed in the hope that it will be useful,       ##
## but WITHOUT ANY WARRANTY; without even the implied warranty of        ##
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         ##
## GNU General Public License for more details.                          ##
##                                                                       ##
## You should have received a copy of the GNU General Public License     ##
## along with this program.  If not, see <http://www.gnu.org/licenses/>. ##
##                                                                       ##
###########################################################################

import codecs
import hashlib
import os
import time
try:
    # For Python 3.0 and later
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import urlopen, Request
    from urllib2 import HTTPError

from datetime import datetime
from . import config

HTTP_DATE_FMT = "%a, %d %b %Y %H:%M:%S GMT"


def update_cache(url, delay, bz2_decompress=False):
    file_name = hashlib.sha1(url.encode('utf-8')).hexdigest()
    cache = os.path.join(config.dir_cache, file_name)
    tmp_file = cache + ".tmp"

    cur_time = time.time()
    request = Request(url.encode('utf-8'))

    if os.path.exists(cache):
        statbuf = os.stat(cache)
        if (cur_time - delay*24*60*60) < statbuf.st_mtime:
            # force cache by local delay
            return cache
        date_string = datetime.strftime(datetime.fromtimestamp(statbuf.st_mtime), HTTP_DATE_FMT)
        request.add_header("If-Modified-Since", date_string)

    request.add_header("User-Agent", "Wget/1.9.1 - http://osmose.openstreetmap.fr") # Add "Wget" for Dropbox user-agent checker

    try:
        answer = urlopen(request)
    except HTTPError as exc:
        if exc.getcode() == 304:
            # not newer
            os.utime(cache, (cur_time,cur_time))
        if os.path.exists(cache):
            return cache
        else:
            raise

    # write the file
    try:
        outfile = None
        if bz2_decompress:
            import bz2
            decompressor = bz2.BZ2Decompressor()
        outfile = open(tmp_file, "wb")
        while True:
            data = answer.read(100 * 1024)
            if len(data) == 0:
                break
            if bz2_decompress:
                data = decompressor.decompress(data)
            outfile.write(data)
    except:
        raise
    finally:
        outfile and outfile.close()

    outfile = codecs.open(cache+".url", "w", "utf-8")
    outfile.write(url)
    outfile.close()
    os.rename(tmp_file, cache)

    # set timestamp
    os.utime(cache, (cur_time, cur_time))

    return cache

def urlmtime(url, delay):
    return os.stat(update_cache(url, delay)).st_mtime

def path(url, delay):
    return update_cache(url, delay)

def urlopen(url, delay):
    return open(path(url, delay), 'r')

def urlread(url, delay):
    return codecs.open(path(url, delay), 'r', "utf-8").read()

if __name__ == "__main__":
    import sys
    url   = sys.argv[1]
    print(urlread(url, 1)[1:10])
