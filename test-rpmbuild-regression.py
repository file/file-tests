# Copyright (C) 2012 Red Hat, Inc.
# Authors: Jan Kaluza <jkaluza@redhat.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#

import os
import sys
import errno
from subprocess import Popen, PIPE
import mimetypes
import difflib
from pyfile import *
import re

mimetypes.init()

detected = []
undetected = []

def test_attr(attr):
	global detected
	global undetected
	regex = None
	path = None
	f = open(attr)
	for line in f.readlines():
		if len(line.split()) != 0 and line.split()[0].endswith("_magic"):
			regex = line[line.find("_magic") + 6:].strip()
			regex = regex.replace("(", "\\(")
			regex = regex.replace(")", "\\)")
			regex = regex.replace("|", "\\|")
			regex = regex.replace("?", "\\?")

			l = line.split()[0]
			if l.find("perl") != -1:
				path = "./db/pl"
			elif l.find("python") != -1:
				path = "./db/py"
			elif l.find("elf") != -1:
				path = "./db/elf"
			elif l.find("mono") != -1:
				path = "./db/mono"
			break
	f.close()

	if regex and path:
		for f in os.listdir(path):
			if f.endswith("json"):
				continue
			full_path = os.path.join(path, f)
			output = get_simple_metadata(full_path)['output']
			#print regex, [output]
			p1 = Popen(["echo", "-n", output[:-1]], stdout=PIPE)
			p2 = Popen(["grep", regex], stdin=p1.stdout, stdout=PIPE)
			p1.stdout.close()
			output = p2.communicate()[0]
			if len(output) == 0 and not full_path in detected:
				if not full_path in undetected:
					undetected.append(full_path)
			elif not full_path in detected:
				if full_path in undetected:
					undetected.remove(full_path)
				detected.append(full_path)

# run this only if started as script from command line
if __name__ == '__main__':
	for attr in os.listdir("./rpm-fileattrs"):
		test_attr(os.path.join("./rpm-fileattrs", attr))

	print "Undetected:", undetected

	#metadata = get_simple_metadata(sys.argv[1])

	#print metadata
