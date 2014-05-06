#!/usr/bin/env python
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
import getopt
from pyfile import *
from pyfile.threadpool import *
import mutex

ret = 0

def test_all_files(exact = False, binary = "file"):

	global ret
	ret = 0

	print_file_info(binary)

	m = mutex.mutex()

	entries = sorted(get_stored_files("db"))

	def store_mimedata(filename):
		metadata = get_simple_metadata(filename, binary)
		try:
			stored_metadata = get_stored_metadata(filename)
		except IOError:
			# file not found or corrupt
			text = "FAIL " + filename + "\n" + "FAIL   could not find stored metadata!\n\
			This can mean that the File failed to generate any output for this file."
		else:
			text = "PASS " + filename
			if is_regression(stored_metadata, metadata, exact):
				text = "FAIL " + filename + "\n" + get_diff(stored_metadata, metadata, exact)
		return text

	def data_print(data):
		print data
		if data[0] == "F":
			global ret
			ret = 1
		m.unlock()

	def data_stored(data):
		m.lock(data_print, data)

	pool = ThreadPool(4)  # create here so program exits if error occurs earlier

	for entry in entries:
		# Insert tasks into the queue and let them run
		pool.queueTask(store_mimedata, entry, data_stored)

	# When all tasks are finished, allow the threads to terminate
	pool.joinAll()
	print ''
	return ret

def usage(ecode):
	print "Runs regressions."
	print sys.argv[0] + " [-e] [-b <file-binary>]"
	print "  Default file_binary='file'"
	print "Examples:"
	print "  " + sys.argv[0] + " -e -b '../file -m ../../magic/magic.mgc'"
	print "  " + sys.argv[0] + " -e"
	sys.exit(ecode)

# run this only if started as script from command line
if __name__ == '__main__':
	exact = False
	file_binary = "file"
	args = sys.argv[1:]

	optlist, args = getopt.getopt(args, 'b:e')

	for o, a in optlist:
		if o == '-b':
			file_binary = a
		elif o == '-e':
			exact = True
		else:
			usage(1)

	sys.exit(test_all_files(exact, file_binary))
