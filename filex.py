# -*- coding: utf-8 -*-

# Copyright (C) 2019 Osmo Salomaa
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Index, find and open files and folders."""

import glob
import json
import os
import threading
import time
import urllib.parse

from gi.repository import Gio

try:
    import albertv0 as albert
except ImportError:
    # The albert module is only available when running via Albert.
    # Use a mock object to allow testing outside Albert.
    class albert:
        def configLocation():
            return os.path.expanduser("~/.config/albert")
        def iconLookup(name):
            return None
        def info(text):
            print(text)

__iid__ = "PythonInterface/v0.2"
__prettyname__ = "Filex"
__version__ = "0.1"
__trigger__ = "filex "
__author__ = "Osmo Salomaa"
__dependencies__ = []


class IndexItem:

    def __init__(self, path_or_uri):
        if os.path.exists(path_or_uri):
            path_or_uri = urllib.parse.quote(path_or_uri)
            path_or_uri = "file://{}".format(path_or_uri)
        file = Gio.File.new_for_uri(path_or_uri)
        info = file.query_info("*", Gio.FileQueryInfoFlags.NONE, None)
        self.title = info.get_display_name()
        self.path = file.get_path()
        self.uri = file.get_uri()
        self.icon = self.get_icon(info.get_icon().get_names())

    def __repr__(self):
        return "IndexItem(title={!r}, uri={!r})".format(self.title, self.uri)

    def get_icon(self, names):
        for name in names:
            icon = albert.iconLookup(name)
            if icon: return icon
        if not self.path: return ""
        name = "folder" if os.path.isdir(self.path) else "text-plain"
        return albert.iconLookup(name)

    def to_albert_item(self):
        return albert.Item(
            id=self.uri,
            icon=self.icon,
            text=self.title,
            subtext=self.path or self.uri,
            completion=self.title,
            urgency=albert.ItemBase.Normal,
            actions=[albert.UrlAction("Open", self.uri)],
        )


class Extension:

    def __init__(self):
        self.conf = self.read_conf()
        self.index = []

    def find_results(self, query):
        q = query.string.strip().lower()
        for item in self.index:
            if not query.isValid: break
            pos = item.title.lower().find(q)
            if pos < 0: continue
            result = item.to_albert_item()
            yield (pos, result)

    def handle_query(self, query):
        q = query.string.strip().lower()
        if len(q) < self.conf["min_length"]: return []
        results = list(self.find_results(query))
        results.sort(key=lambda x: x[0])
        return [x[1] for x in results]

    def read_conf(self):
        directory = albert.configLocation()
        fname = os.path.join(directory, "filex.json")
        conf = self.read_json(fname, {}) or {}
        orig = conf.copy()
        conf.setdefault("min_length", 1)
        conf.setdefault("paths", [os.path.expanduser("~/*")])
        conf.setdefault("scan_interval", 900)
        if conf != orig:
            self.write_json(conf, fname)
        return conf

    def read_json(self, fname, default=None):
        if not os.path.isfile(fname):
            if default is not None:
                return default
        albert.info("Reading {}...".format(fname))
        with open(fname, "r") as f:
            return json.load(f)

    def scan(self):
        for pattern in self.conf["paths"]:
            pattern = os.path.expanduser(pattern)
            for path in glob.iglob(pattern, recursive=True):
                albert.info("... {}".format(path))
                yield IndexItem(path)

    def update_index(self):
        albert.info("Updating index...")
        index = list(self.scan())
        index.append(IndexItem("computer:///"))
        index.append(IndexItem("recent:///"))
        index.append(IndexItem("trash:///"))
        self.index = index
        albert.info("{:d} items in index.".format(len(index)))

    def write_json(self, data, fname):
        directory = os.path.dirname(fname)
        os.makedirs(directory, exist_ok=True)
        albert.info("Writing {}...".format(fname))
        with open(fname, "w") as f:
            f.write("{}\n".format(
                json.dumps(data,
                           ensure_ascii=False,
                           indent=2,
                           sort_keys=True)))


def worker():
    while True:
        extension.update_index()
        time.sleep(extension.conf["scan_interval"])

extension = Extension()
thread = threading.Thread(target=worker, daemon=True)

def initialize():
    thread.start()

def finalize():
    thread.join(timeout=0.1)

def handleQuery(query):
    return extension.handle_query(query)
