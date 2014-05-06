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
from pyfile.progressbar import ProgressBar
from pyfile.threadpool import *

global_error = False

def update_all_files(file_name = 'file', magdir = 'Magdir', file_binary = 'file'):

	print_file_info(file_binary)

	split_patterns(magdir, file_name)
	compile_patterns(file_name, file_binary)
	compiled = is_compilation_supported(file_name, file_binary)

	entries = get_stored_files("db")
	if len(entries) == 0:
		raise ValueError('no files in db {0}'.format( os.path.join(os.getcwd(), 'db') ))
	prog = ProgressBar(0, len(entries), 50, mode='fixed', char='#')

	def store_mimedata(data):
		metadata = get_full_metadata(data[0], file_name, compiled, file_binary)
		error = metadata['output'] == None
		if not error:
			set_stored_metadata(data[0], metadata)
			return (data[0], data[1], False)
		else:
			return (data[0], data[1], metadata['err'])   # err=(cmd, output)
	
	def data_stored(data):
		entry, hide, error = data
		if error:
			global global_error
			global_error = True
			print 'ERROR for', entry
			print 'ERROR running command', error[0]
			print 'ERROR produced output', error[1]
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

def usage(ecode):
	print "Updates database."
	print sys.argv[0] + " [-v <version_name>] [-m <magdir>] [-b <file-binary>]"
	print "  Default path_to_magdir_directory='Magdir'"
	print "  Default version_name='file'"
	print "Examples:"
	print "  " + sys.argv[0] + " -v file-5.07;"
	print "  " + sys.argv[0] + " -v file-5.04-my-version -m file-5.04/magic/Magdir;"
	sys.exit(ecode)

# run this only if started as script from command line
if __name__ == '__main__':
	file_name = 'file'
	file_binary = "file"
	magdir = "Magdir"
	args = sys.argv[1:]

	optlist, args = getopt.getopt(args, 'b:hm:v:')

	for o, a in optlist:
		if o == '-b':
			file_binary = a
		elif o == '-m':
			magdir = a
		elif o == '-h':
			usage(0)
		elif o == '-v':
			file_name = a
		else:
			usage(1)

	sys.exit(update_all_files(file_name, magdir, file_binary))
