#!/bin/sh
# Run this to generate all the initial makefiles, etc.

srcdir=`dirname $0`
test -n "$srcdir" || srcdir=`dirname "$0"`
test -n "$srcdir" || srcdir=.

PKG_NAME="alternative-toolbar"
prevdir="$PWD"
cd "$srcdir"

INTLTOOLIZE=`which intltoolize`
if test -z $INTLTOOLIZE; then
  echo "*** No intltoolize found, please install the intltool package ***"
  exit 1
fi

AUTORECONF=`which autoreconf`
if test -z $AUTORECONF; then
  echo "*** No autoreconf found, please install it ***"
  exit 1
fi

intltoolize --force
autoreconf --force --install || exit $?

cd "$prevdir"
test -n "$NOCONFIGURE" || "$srcdir/configure" "$@"
