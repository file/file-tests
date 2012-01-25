import os
import sys
from pyfile import *
from pyfile.progressbar import ProgressBar
from pyfile.threadpool import *

def update_all_files(file_name = 'file', magdir = 'Magdir'):
	pool = ThreadPool(4)

	split_patterns(magdir, file_name)
	compile_patterns(file_name)
	compiled = is_compilation_supported(file_name)

	entries = get_stored_files("db")
	prog = ProgressBar(0, len(entries), 50, mode='fixed', char='#')

	def store_mimedata(data):
		metadata = get_full_metadata(data[0], file_name, compiled)
		set_stored_metadata(data[0], metadata)
		return data[1]
	
	def data_stored(hide):
		prog.increment_amount()
		if not hide:
			print prog, "Updating database", '\r',
			sys.stdout.flush()

	for i,entry in enumerate(entries):
		# Insert tasks into the queue and let them run
		pool.queueTask(store_mimedata, (entry, i % 2), data_stored)

	# When all tasks are finished, allow the threads to terminate
	pool.joinAll()
	print ''

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
	print "  " + sys.argv[0] + "file-5.04-my-version file-5.04/magic/Magdir;"
	sys.exit(0)

file_name = sys.argv[1]
update_all_files(file_name, magdir)
