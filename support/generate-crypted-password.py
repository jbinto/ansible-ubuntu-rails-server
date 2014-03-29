#!/usr/bin/python -tt
# skvidal@fedoraproject.org - (c) Red Hat, inc 2013
# gpl v2+ 
# utterly trivial so I'm not worried one way or the other

# This source code adapted from http://skvidal.fedorapeople.org/misc/shapass
# Enhancements (c) Jesse Buchanan 2014 - GPL v2+

# Purpose: Generates a secure, crypted password for use in /etc/shadow.
# Usage: Execute without arguments.

import string
import getpass
import sys

try:
    from passlib.hosts import linux_context
except ImportError, e:
    print "Couldn't import passlib. Try: pip install passlib"
    sys.exit(1)

match = False
while not match:
    input = getpass.getpass()
    input2 = getpass.getpass(prompt="Re-enter Password: ")
    if input == input2:
        match = True
    else:
        print 'Passwords do not match, try again!'

print linux_context.encrypt(input)
