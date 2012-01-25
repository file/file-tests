import os
import sys
from pyfile import *
from pyfile.progressbar import ProgressBar
from pyfile.threadpool import *

def update_all_files(file_binary = 'file', magdir = 'Magdir'):
	pool = ThreadPool(4)

	split_patterns(magdir, file_binary)
	compile_patterns(file_binary)
	compiled = is_compilation_supported(file_binary)

	entries = get_stored_files("db")
	prog = ProgressBar(0, len(entries), 50, mode='fixed', char='#')

	def store_mimedata(data):
		metadata = get_full_metadata(data[0], file_binary, compiled)
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

file_binary = 'file'
magdir = "Magdir"

if len(sys.argv) == 3:
	magdir = sys.argv[1]
	file_binary = sys.argv[2]
elif len(sys.argv) == 2 and sys.argv[1] == "-h":
	print "Updates database."
	print sys.argv[0] + " [path_to_magdir_directory] [file_binary]"
	print "  Default path_to_magdir_directory='Magdir'"
	print "  Default file_binary='file'"
	print "Examples:"
	print "  " + sys.argv[0] + ";"
	print "  " + sys.argv[0] + " file-5.04/magic/Magdir file-5.04/src/file;"
	sys.exit(0)
update_all_files(file_binary, magdir)
