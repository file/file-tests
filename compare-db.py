import os
import sys
from pyfile import *
from pyfile.progressbar import ProgressBar
from pyfile.threadpool import *
import mutex


def compare_all_files(file_binary = 'file', magdir = 'Magdir'):
	pool = ThreadPool(4)
	m = mutex.mutex()

	split_patterns(magdir, file_binary)
	compile_patterns(file_binary)
	compiled = is_compilation_supported(file_binary)

	entries = get_stored_files("db")
	prog = ProgressBar(0, len(entries), 50, mode='fixed', char='#')

	def store_mimedata(data):
		metadata = get_full_metadata(data[0], file_binary, compiled)
		stored_metadata = get_stored_metadata(data[0])
		text = "PASS " + data[0]
		if is_regression(stored_metadata, metadata):
			text = "FAIL " + data[0] + "\n" + get_diff(stored_metadata, metadata)
		return text

	def data_print(data):
		print data
		if data[0] == "F":
			global ret
			ret = 1
		m.unlock()

	def data_stored(data):
		m.lock(data_print, data)

	for i,entry in enumerate(entries):
		# Insert tasks into the queue and let them run
		pool.queueTask(store_mimedata, (entry, i % 2), data_stored)

	# When all tasks are finished, allow the threads to terminate
	pool.joinAll()
	print ''

file_binary = 'file'
magdir = "Magdir"

if len(sys.argv) == 3:
	file_binary = sys.argv[2]
	magdir = sys.argv[1]
elif len(sys.argv) == 2 and sys.argv[1] == "-h":
	print "Compares files in database with output of particular file binary."
	print sys.argv[0] + " [path_to_magdir_directory] [file_binary]"
	print "  Default path_to_magdir_directory='Magdir'"
	print "  Default file_binary='file'"
	print "Examples:"
	print "  " + sys.argv[0] + ";"
	print "  " + sys.argv[0] + " file-5.04/magic/Magdir file-5.04/src/file;"
	sys.exit(0)
compare_all_files(file_binary, magdir)
