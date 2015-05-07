#!/bin/sh
echo "updating po files"
for i in *.po; do
	lang=`basename $i .po`
	echo "updating $lang"
    intltool-update --dist $lang -g alternative-toolbar
done

echo "update plugin file"

intltool-merge -d . ../alternative-toolbar.plugin.in ../alternative-toolbar.plugin
