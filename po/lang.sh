#!/bin/sh
echo "installing languages to $1"
lang=`echo $LANG | cut -d'.' -f 1`

if [ ! -f $lang.po ]; then
   lang=`echo $lang | cut -d'_' -f 1`
fi

if [ ! -f $lang.po ]; then
   lang="en_US"
fi

echo "installing $lang"
install -d $1$lang/LC_MESSAGES
msgfmt -c $lang.po -o $1$lang/LC_MESSAGES/alternative-toolbar.mo
