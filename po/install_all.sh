#!/bin/sh
echo "installing languages to $1"
for i in *.po; do
	lang=`basename $i .po`
	echo "installing $lang"
	install -d $1$lang/LC_MESSAGES
	msgfmt -c $lang.po -o $1$lang/LC_MESSAGES/alternative-toolbar.mo
done
