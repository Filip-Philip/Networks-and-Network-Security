#! /bin/bash
perl -e 'print "lab5.py\n" x 10' | xargs -P 10 -I {} python3 {}
