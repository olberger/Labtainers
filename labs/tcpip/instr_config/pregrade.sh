#!/bin/bash
: <<'END'
This software was created by United States Government employees at 
The Center for Cybersecurity and Cyber Operations (C3O) 
at the Naval Postgraduate School NPS.  Please note that within the 
United States, copyright protection is not available for any works 
created  by United States Government employees, pursuant to Title 17 
United States Code Section 105.   This software is in the public 
domain and is not subject to copyright. 
END
#
# Script to run prior to grading a student's lab.  It is intended
# for two potential purposes:
# 1) Create solution artifacts to campare against student artifacts;
# 2) Process student artifacts into a different form, e.g., extracting
#    browser sqlite data as in the default instance of this file below.
# 
# 
#
homedir=$1
# destdir includes the container 
destdir=$2
dbg=/tmp/pregrade.log
cd $homedir/$destdir
is_sqlite=`which sqlite3`
echo $is_sqlite
if [[ ! -z $is_sqlite ]]; then
    for fname in .mozilla/firefox/*default/places.sqlite; do
        outpath=.local/result
        outfile=$outpath/moz_places.txt
        mkdir -p "$outpath"
        sqlite3 "$fname" "SELECT moz_places.* FROM moz_places;" >"$outfile"
    done
fi
#
#  Add other processing below.
#
