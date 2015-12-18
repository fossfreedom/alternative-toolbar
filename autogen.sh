#!/bin/sh
# Run this to generate all the initial makefiles, etc.

srcdir=`dirname $0`
test -n "$srcdir" || srcdir=`dirname "$0"`
test -n "$srcdir" || srcdir=.

PKG_NAME="alternative-toolbar"
prevdir="$PWD"
cd "$srcdir"


intltoolize --force
AUTORECONF=`which autoreconf`
if test -z $AUTORECONF;
then
  echo "*** No autoreconf found, please install it ***"
  exit 1
else
  autoreconf --force --install || exit $?
fi

cd "$prevdir"
test -n "$NOCONFIGURE" || "$srcdir/configure" "$@"
