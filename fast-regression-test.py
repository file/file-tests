import os
import sys
from pyfile import *
from pyfile.threadpool import *
import mutex

ret = 0

def test_all_files():
	pool = ThreadPool(4)
	m = mutex.mutex()

	entries = get_stored_files("db")

	def store_mimedata(filename):
		metadata = get_simple_metadata(filename)
		stored_metadata = get_stored_metadata(filename)
		text = "PASS " + filename
		if is_regression(stored_metadata, metadata):
			text = "FAIL " + filename + "\n" + get_diff(stored_metadata, metadata)
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
		pool.queueTask(store_mimedata, entry, data_stored)

	# When all tasks are finished, allow the threads to terminate
	pool.joinAll()
	print ''
	return ret

sys.exit(test_all_files())
