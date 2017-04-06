#!/usr/bin/env python

"""Simple HTTP Server With Upload.

This module builds on BaseHTTPServer by implementing the standard GET
and HEAD requests in a fairly straightforward manner.

"""


__version__ = "0.1"
__all__ = ["SimpleHTTPRequestHandler"]

import os
import posixpath
import BaseHTTPServer
import urllib
import cgi
import shutil
import mimetypes
import re
import subprocess
import glob
from os.path import basename

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


class SimpleHTTPRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    """Simple HTTP request handler with GET/HEAD/POST commands.

    This serves files from the current directory and any of its
    subdirectories.  The MIME type for files is determined by
    calling the .guess_type() method. And can reveive file uploaded
    by client.

    The GET/HEAD/POST requests are identical except that the HEAD
    request omits the actual contents of the file.

    """

    server_version = "SimpleHTTPWithUpload/" + __version__

    def do_GET(self):
        """Serve a GET request."""
        f = self.send_head()
        if f:
            self.copyfile(f, self.wfile)
            f.close()

    def do_HEAD(self):
        """Serve a HEAD request."""
        f = self.send_head()
        if f:
            f.close()

    def do_POST(self):
        """Serve a POST request."""
        r, info = self.deal_post_data()
        print r, info, "by: ", self.client_address
        f = StringIO()
        f.write('<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">')
        f.write("<html>\n<title>Upload Result Page</title>\n")
        f.write("<body>\n<h2>Upload Result Page</h2>\n")
        f.write("<hr>\n")
        if r:
            f.write("<strong>Success:</strong>")
            self.encode()
            self.m3u8()
        else:
            f.write("<strong>Failed:</strong>")
        f.write(info)
        f.write("<br><a href=\"%s\">back</a>" % self.headers['referer'])
        f.write("<hr><small>Powerd By: MosQuito")
        f.write("</a>.</small></body>\n</html>\n")
        length = f.tell()
        f.seek(0)
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", str(length))
        self.end_headers()
        if f:
            self.copyfile(f, self.wfile)
            f.close()
        
    def deal_post_data(self):
        boundary = self.headers.plisttext.split("=")[1]
        remainbytes = int(self.headers['content-length'])
        line = self.rfile.readline()
        remainbytes -= len(line)
        if not boundary in line:
            return (False, "Content NOT begin with boundary")
        line = self.rfile.readline()
        remainbytes -= len(line)
        fn = re.findall(r'Content-Disposition.*name="file"; filename="(.*)"', line)
        if not fn:
            return (False, "Can't find out file name...")
        path = self.translate_path(self.path)
        fn = os.path.join(path, fn[0])
        line = self.rfile.readline()
        remainbytes -= len(line)
        line = self.rfile.readline()
        remainbytes -= len(line)
        try:
            out = open(fn, 'wb')
        except IOError:
            return (False, "Can't create file to write, do you have permission to write?")
                
        preline = self.rfile.readline()
        remainbytes -= len(preline)
        while remainbytes > 0:
            line = self.rfile.readline()
            remainbytes -= len(line)
            if boundary in line:
                preline = preline[0:-1]
                if preline.endswith('\r'):
                    preline = preline[0:-1]
                out.write(preline)
                out.close()
                return (True, "%s" % fn)
                #return (True, "File '%s' upload success!" % fn)
            else:
                out.write(preline)
                preline = line
        return (False, "Unexpect Ends of data.")

    def send_head(self):
        """Common code for GET and HEAD commands.

        This sends the response code and MIME headers.

        Return value is either a file object (which has to be copied
        to the outputfile by the caller unless the command was HEAD,
        and must be closed by the caller under all circumstances), or
        None, in which case the caller has nothing further to do.

        """
        path = self.translate_path(self.path)
        f = None
        if os.path.isdir(path):
            if not self.path.endswith('/'):
                # redirect browser - doing basically what apache does
                self.send_response(301)
                self.send_header("Location", self.path + "/")
                self.end_headers()
                return None
            for index in "index.html", "index.htm":
                index = os.path.join(path, index)
                if os.path.exists(index):
                    path = index
                    break
            else:
                return self.list_directory(path)
        ctype = self.guess_type(path)
        try:
            # Always read in binary mode. Opening files in text mode may cause
            # newline translations, making the actual size of the content
            # transmitted *less* than the content-length!
            f = open(path, 'rb')
        except IOError:
            self.send_error(404, "File not found")
            return None
        self.send_response(200)
        self.send_header("Content-type", ctype)
        fs = os.fstat(f.fileno())
        self.send_header("Content-Length", str(fs[6]))
        self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
        self.end_headers()
        return f

    def list_directory(self, path):
        """Helper to produce a directory listing (absent index.html).

        Return value is either a file object, or None (indicating an
        error).  In either case, the headers are sent, making the
        interface the same as for send_head().

        """
        try:
            list = os.listdir(path)
        except os.error:
            self.send_error(404, "No permission to list directory")
            return None
        list.sort(key=lambda a: a.lower())
        f = StringIO()
        displaypath = cgi.escape(urllib.unquote(self.path))
        f.write('<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">')
        f.write("<html>\n<title>Directory listing for %s</title>\n" % displaypath)
        f.write("<body>\n<h2>Directory listing for %s</h2>\n" % displaypath)
        f.write("<hr>\n")
        f.write("<form ENCTYPE=\"multipart/form-data\" method=\"post\">")
        f.write("<input name=\"file\" type=\"file\"/>")
        f.write("<input type=\"submit\" value=\"upload\"/></form>\n")
        f.write("<hr>\n<ul>\n")
        for name in list:
            fullname = os.path.join(path, name)
            displayname = linkname = name
            # Append / for directories or @ for symbolic links
            if os.path.isdir(fullname):
                displayname = name + "/"
                linkname = name + "/"
            if os.path.islink(fullname):
                displayname = name + "@"
                # Note: a link to a directory displays with @ and links with /
            f.write('<li><a href="%s">%s</a>\n'
                    % (urllib.quote(linkname), cgi.escape(displayname)))
        f.write("</ul>\n<hr>\n</body>\n</html>\n")
        length = f.tell()
        f.seek(0)
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", str(length))
        self.end_headers()
        return f

    def translate_path(self, path):
        """Translate a /-separated PATH to the local filename syntax.

        Components that mean special things to the local file system
        (e.g. drive or directory names) are ignored.  (XXX They should
        probably be diagnosed.)

        """
        # abandon query parameters
        path = path.split('?',1)[0]
        path = path.split('#',1)[0]
        path = posixpath.normpath(urllib.unquote(path))
        words = path.split('/')
        words = filter(None, words)
        path = os.getcwd()
        for word in words:
            drive, word = os.path.splitdrive(word)
            head, word = os.path.split(word)
            if word in (os.curdir, os.pardir): continue
            path = os.path.join(path, word)
        return path

    def copyfile(self, source, outputfile):
        """Copy all data between two file objects.

        The SOURCE argument is a file object open for reading
        (or anything with a read() method) and the DESTINATION
        argument is a file object open for writing (or
        anything with a write() method).

        The only reason for overriding this would be to change
        the block size or perhaps to replace newlines by CRLF
        -- note however that this the default server uses this
        to copy binary data as well.

        """
        shutil.copyfileobj(source, outputfile)

    def guess_type(self, path):
        """Guess the type of a file.

        Argument is a PATH (a filename).

        Return value is a string of the form type/subtype,
        usable for a MIME Content-type header.

        The default implementation looks the file's extension
        up in the table self.extensions_map, using application/octet-stream
        as a default; however it would be permissible (if
        slow) to look inside the data to make a better guess.

        """

        base, ext = posixpath.splitext(path)
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        ext = ext.lower()
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        else:
            return self.extensions_map['']

    if not mimetypes.inited:
        mimetypes.init() # try to read system mime.types
    extensions_map = mimetypes.types_map.copy()
    extensions_map.update({
        '': 'application/octet-stream', # Default
        '.py': 'text/plain',
        '.c': 'text/plain',
        '.h': 'text/plain',
        })

    def encode(self):
        video = glob.glob(os.path.join('*.mp4'))
        print video[0]
        #ffmpeg -i $filename -vf scale=320:240,setsar=4:3 "320_240_"$filename
        #ffmpeg -i "320_240_"$filename -vcodec copy -map 0 -segment_time 8 -f segment "320_240_"%03d"_"$filename
        #ffmpeg -i $filename -vf scale=160:120,setsar=4:3 "160_120_"$filename
        #ffmpeg -i "160_120_"$filename -vcodec copy -map 0 -segment_time 8 -f segment "160_120_"%03d"_"$filename
        #ffmpeg -i $filename -vf scale=80:60,setsar=4:3 "80_60_"$filename
        #ffmpeg -i "80_60_"$filename -vcodec copy -map 0 -segment_time 8 -f segment "80_60_"%03d"_"$filename
        #subprocess.call(['ffmpeg', '-i', base[0], 'overwatch.mkv'])
        #subprocess.call('ffmpeg -i "%s" overwatch.mkv' % video[0], shell=True)       
        subprocess.call('rm 320_240_*.mp4 160_120_*.mp4 80_60_*.mp4', shell=True)
        subprocess.call('ffmpeg -i "%s" -vf scale=320:240 320_240.mp4' % video[0], shell=True)
        subprocess.call('ffmpeg -i "%s" -vf scale=160:120 160_120.mp4' % video[0], shell=True)
        subprocess.call('ffmpeg -i "%s" -vf scale=80:60 80_60.mp4' % video[0], shell=True)
        #subprocess.call('ffmpeg -i 320_240.mp4 -vcodec copy -map 0 -segment_time 10 -f segment "320_240_"%03d.mp4', shell=True)
        #subprocess.call('ffmpeg -i 160_120.mp4 -vcodec copy -map 0 -segment_time 10 -f segment "160_120_"%03d.mp4', shell=True)
        #subprocess.call('ffmpeg -i 80_60.mp4 -vcodec copy -map 0 -segment_time 10 -f segment "80_60_"%03d.mp4', shell=True)
        #for i in range(0,6):
        #    time = i * 10 
        #    subprocess.call('ffmpeg -ss 00:00:"%s" -i 320_240.mp4 -t 00:00:10 -vcodec copy -acodec copy 320_240_"%03d".mp4' % (time, i), shell=True)
        #    subprocess.call('ffmpeg -ss 00:00:"%s" -i 160_120.mp4 -t 00:00:10 -vcodec copy -acodec copy 160_120_"%03d".mp4' % (time, i), shell=True)
        #    subprocess.call('ffmpeg -ss 00:00:"%s" -i 80_60.mp4 -t 00:00:10 -vcodec copy -acodec copy 80_60_"%03d".mp4' % (time, i), shell=True)
        subprocess.call('ffmpeg -i 320_240.mp4 -c:v libx264 -c:a copy -f hls -hls_time 10 -hls_list_size 10 high.m3u8', shell=True)
        subprocess.call('ffmpeg -i 160_120.mp4 -c:v libx264 -c:a copy -f hls -hls_time 10 -hls_list_size 10 medium.m3u8', shell=True)
        subprocess.call('ffmpeg -i 80_60.mp4 -c:v libx264 -c:a copy -f hls -hls_time 10 -hls_list_size 10 low.m3u8', shell=True)
        return

    def m3u8(self):
        subprocess.call('echo "#EXTM3U" >> playlist.m3u8', shell=True)
        subprocess.call('echo "#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=1280000" >> playlist.m3u8', shell=True)
        subprocess.call('echo "low.m3u8" >> playlist.m3u8', shell=True)
        subprocess.call('echo "#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=2560000" >> playlist.m3u8', shell=True)
        subprocess.call('echo "medium.m3u8" >> playlist.m3u8', shell=True)
        subprocess.call('echo "#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=5120000" >> playlist.m3u8', shell=True)
        subprocess.call('echo "high.m3u8" >> playlist.m3u8', shell=True)
        return


def test(HandlerClass = SimpleHTTPRequestHandler,
         ServerClass = BaseHTTPServer.HTTPServer):
    BaseHTTPServer.test(HandlerClass, ServerClass)

if __name__ == '__main__':
    test()