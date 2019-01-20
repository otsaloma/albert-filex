# -*- coding: utf-8-unix -*-

DESTDIR =
PREFIX  = /usr/local
MODDIR  = $(DESTDIR)$(PREFIX)/share/albert/org.albert.extension.python/modules

check:
	flake8 .

clean:
	rm -rf __pycache__

install:
	mkdir -p $(MODDIR)
	cp -f filex.py $(MODDIR)

.PHONY: check clean install
