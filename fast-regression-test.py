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
from pyfile import *
from pyfile.threadpool import *
import mutex

ret = 0

def test_all_files(exact = False):

	print_file_info()

	m = mutex.mutex()

	entries = get_stored_files("db")

	def store_mimedata(filename):
		metadata = get_simple_metadata(filename)
		try:
			stored_metadata = get_stored_metadata(filename)
		except IOError:
			# file not found or corrupt
			text = "FAIL " + filename + "\n" + "FAIL   could not find stored metadata!"
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

	for i,entry in enumerate(entries):
		# Insert tasks into the queue and let them run
		pool.queueTask(store_mimedata, entry, data_stored)

	# When all tasks are finished, allow the threads to terminate
	pool.joinAll()
	print ''
	return ret

exact = False
if len(sys.argv) == 2 and sys.argv[1] == "exact":
	exact = True

sys.exit(test_all_files(exact))
