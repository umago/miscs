#!/usr/bin/python
# coding: utf-8
# Copyright (C) 2011 Lucas Alvares Gomes <lucasagomes@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

# NOTE[1]: This script was made to help my friend download mangas from www.mangareader.net
#it wont work for any other website :) so don't lose ur time trying ;)~

# NOTE[2]: It was made in 06/04/11, and can stop working at any time!!!!

# NOTE[3]: Go mayzi!! download it by urself now :)~

# TODO: Make it much more faster with multi-processing

import urllib
import Tkinter
import tkFileDialog
import os
import re
import threading
import sys

REGEX = "(?i)<\/?\w+((\s+\w+(\s*=\s*(?:\".*?\"|'.*?'|[^'\">\s]+))?)+\s*|\s*)\/?>"
BASE_URL = "http://www.mangareader.net"

class NalineeMangaDownloader(Tkinter.Tk):

    def __init__(self,parent):
        Tkinter.Tk.__init__(self,parent)
        self.parent = parent
        self.active = False
        self.initialize()

    def initialize(self):
        self.grid()
        self.dirname = None

        self.bind("<Destroy>", self._destroy)

        self.entry_url = Tkinter.Entry(self)
        self.entry_url.grid(column=0, row=0,sticky='WENS',
                            columnspan=2, rowspan=2, padx=5, pady=5)

        self.button = Tkinter.Button(self,text=u"Choose the folder",
                                command=self.open_directory)
        self.button.grid(column=0, row=3, rowspan=2)

        self.buttondl = Tkinter.Button(self,text=u"Download",
                                command=self.download_clicked)
        self.buttondl.grid(column=0, row=6)

        self.grid_columnconfigure(0, weight=1)
        self.grid_propagate(0)
        self.config(width=300, height=100)
        self.resizable(True, False)

    def _destroy(self, event):
        self.active = False
        print "destroy"

    def check_url(self, url):
        try:
            web_file = urllib.urlopen(url)
        except IOError:
            return False
        data = web_file.read()
        chapter = self.get_chapter(data)
        if chapter:
            return True
        return False

    def download_clicked(self):
        url = self.entry_url.get()

        if not url or not self.dirname:
            return
        
        try:
            if not self.check_url(url):
                print "Invalid url"
                return
        except:
            print "Invalid url"
            return

        self.buttondl.config(state=Tkinter.DISABLED)
        self.button.config(state=Tkinter.DISABLED)
        threading.Thread(target=self.download, args=(url, self.dirname,)).start()

    def open_directory(self):
        tmp = tkFileDialog.askdirectory(parent=self, title="Choose the folder")
        if tmp:
            self.dirname = tmp
            print "Selected Folder: ", self.dirname

    def get_img_path(self, lines):
        for match in re.finditer(REGEX, lines):
            data  = repr(match.group())
            if data.find("<img") != -1:
                p = re.compile('src="([^"]*)"')
                path = p.search(data).group(1)
                return path
        return None

    def get_next_path(self, lines):
        next = False
        for match in re.finditer(REGEX, lines):
            data  = repr(match.group())
            if next:
                p = re.compile('href="([^"]*)"')
                path = p.search(data).group(1)
                return path
            if data.find('<span class="next"') != -1:
                next = True
        return None

    def get_chapter(self, lines):
        lines = lines.split()
        for e, i in enumerate(lines):
            if i.startswith("document['chapterno']"):
                chapter = lines[e+2]
                chapter = chapter.replace(';', '')
                return chapter
        return None
        
    def download(self, url, basedir):
        if not basedir[-1] == os.sep:
            basedir += os.sep

        self.active = True
        while self.active:
            try:
                web_file = urllib.urlopen(url)
            except IOError:
                continue
            data = web_file.read()
            chapter = self.get_chapter(data)
            if chapter is None: break
            if not os.path.exists(basedir + chapter):
                try:
                    os.mkdir(basedir + chapter)
                except OSError:
                    pass
            os.chdir(basedir + chapter)
            image = self.get_img_path(data)
            print "Downloading: %s" % image
            image_data = urllib.urlopen(image)
            image_data = image_data.read()
            local_file = open(image.split('/')[-1], 'wb')
            local_file.write(image_data)
            os.chdir(basedir)
            url = self.get_next_path(data)
            if url is None: break
            url = BASE_URL + url
        
        self.active = False
        print "Manga Downloaded"
        self.buttondl.config(state=Tkinter.NORMAL)
        self.button.config(state=Tkinter.NORMAL)


if __name__ == '__main__':
    app = NalineeMangaDownloader(None)
    app.title('Nalinee Manga Downloader')
    app.mainloop()

