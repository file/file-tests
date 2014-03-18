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
from pyfile.progressbar import ProgressBar
from pyfile.threadpool import *

global_error = False

def update_all_files(file_name = 'file', magdir = 'Magdir'):

	print_file_info()

	split_patterns(magdir, file_name)
	compile_patterns(file_name)
	compiled = is_compilation_supported(file_name)

	entries = get_stored_files("db")
	if len(entries) == 0:
		raise ValueError('no files in db {0}'.format( os.path.join(os.getcwd(), 'db') ))
	prog = ProgressBar(0, len(entries), 50, mode='fixed', char='#')

	def store_mimedata(data):
		metadata = get_full_metadata(data[0], file_name, compiled)
		error = metadata['output'] == None
		if not error:
			set_stored_metadata(data[0], metadata)
		return (data[1], error)
	
	def data_stored(data):
		hide, error = data
		if error:
			global global_error
			global_error = True
			return
		prog.increment_amount()
		if not hide:
			print prog, "Updating database", '\r',
			sys.stdout.flush()

	pool = ThreadPool(4)   # create this here, so program exits if error occurs earlier
	for i,entry in enumerate(entries):
		# Insert tasks into the queue and let them run
		pool.queueTask(store_mimedata, (entry, i % 2), data_stored)
		if global_error:
			print "Error when executing File binary"
			break

	# When all tasks are finished, allow the threads to terminate
	pool.joinAll()
	print ''
	return global_error

file_name = 'file'
magdir = "Magdir"

if len(sys.argv) == 3:
	magdir = sys.argv[2]
	file_name = sys.argv[1]
elif (len(sys.argv) == 2 and sys.argv[1] == "-h") or len(sys.argv) == 1:
	print "Updates database."
	print sys.argv[0] + " <version_name> [path_to_magdir_directory]"
	print "  Default path_to_magdir_directory='Magdir'"
	print "  Default version_name='file'"
	print "Examples:"
	print "  " + sys.argv[0] + " file-5.07;"
	print "  " + sys.argv[0] + " file-5.04-my-version file-5.04/magic/Magdir;"
	sys.exit(1)

file_name = sys.argv[1]
sys.exit(update_all_files(file_name, magdir))
