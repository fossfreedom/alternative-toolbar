#!/bin/sh
echo "creating po files"

for i in /usr/share/locale/*; do
	loc=`basename $i .`
	echo "creating $loc"
    msginit --no-translator -l $loc
done
