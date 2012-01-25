import os
import sys
import errno
from subprocess import Popen, PIPE
import pickle
import difflib
import mimetypes
from cStringIO import StringIO
import re
mimetypes.init()

def get_stored_metadata(filename):
	f = open (filename + ".pickle", 'r')
	p = pickle.load(f)
	f.close()
	return p

def set_stored_metadata(filename, metadata):
	f = open (filename + ".pickle", 'w')
	pickle.dump(metadata, f)
	f.close()

def is_regression(m1, m2, ratio = 0.7):
	if m1['output'] != m2['output']:
		# previous file didn't detect it, so we hope new output is ok
		if not m1['output'].endswith("data\n"):
			r = difflib.SequenceMatcher(None, m1['output'], m2['output']).ratio()
			if (r < ratio):
				#print >> sys.stderr, "Expected:%sGot     :%s" % (m2['output'], m1['output'])
				return True

	mime = m2['mime'].split(":")[-1].split(";")[0].strip()
	old_mime = m1['mime'].split(":")[-1].split(";")[0].strip()

	# if old_mime is empty, then previous version of File didn't know that filetype.
	# we will hope that new mime is right.
	if old_mime != mime and len(old_mime) != 0:
		ext = os.path.splitext(mime)[-1]
		# it's not error if new mimetype is correct type for that extension.
		if ext in mimetypes.types_map.keys():
			expected = mimetypes.types_map[ext]
			if expected == mime:
				return True
			#else:
				#print >> sys.stderr, "Expected:%s" % (expected)
		#print >> sys.stderr, "Expected:%s\nGot     :%s" % (old_mime, mime)
		return True
	return False;

def get_diff(m1, m2, ratio = 0.7):
	text = ""
	if m1['output'] != m2['output']:
		# previous file didn't detect it, so we hope new output is ok
		if not m1['output'].endswith("data\n"):
			r = difflib.SequenceMatcher(None, m1['output'], m2['output']).ratio()
			if (r < ratio):
				text = "Expected :%sGot      :%s" % (m1['output'], m2['output'])

	mime = m2['mime'].split(":")[-1].split(";")[0].strip()
	old_mime = m1['mime'].split(":")[-1].split(";")[0].strip()

	want_mime_diff = False

	# if old_mime is empty, then previous version of File didn't know that filetype.
	# we will hope that new mime is right.
	if old_mime != mime and len(old_mime) != 0:
		ext = os.path.splitext(mime)[-1]
		# it's not error if new mimetype is correct type for that extension.
		if ext in mimetypes.types_map.keys():
			expected = mimetypes.types_map[ext]
			if expected != mime:
				want_mime_diff = True
		want_mime_diff = True
	if want_mime_diff:
		text = "Expected :%sGot      :%s" % (m1['mime'], m2['mime'])

	if text != "":
		if m1.has_key('pattern') and m2.has_key('pattern') and m1['pattern'] != "" and m2['pattern'] != "":
			for line in difflib.unified_diff(StringIO(m1['pattern']).readlines(), StringIO(m2['pattern']).readlines()):
				text += line
	return text

def get_stored_files(dir_name, subdir = True, *args):
	'''Return a list of file names found in directory 'dir_name'
	If 'subdir' is True, recursively access subdirectories under 'dir_name'.
	Additional arguments, if any, are file extensions to match filenames. Matched
		file names are added to the list.
	If there are no additional arguments, all files found in the directory are
		added to the list.
	Example usage: fileList = dirEntries(r'H:\TEMP', False, 'txt', 'py')
		Only files with 'txt' and 'py' extensions will be added to the list.
	Example usage: fileList = dirEntries(r'H:\TEMP', True)
		All files and all the files in subdirectories under H:\TEMP will be added
		to the list.
	'''
	fileList = []
	for file in os.listdir(dir_name):
		dirfile = os.path.join(dir_name, file)
		if os.path.isfile(dirfile):
			if not args:
				if not dirfile.endswith("pickle"):
					fileList.append(dirfile)
			else:
				if os.path.splitext(dirfile)[1][1:] in args:
					fileList.append(dirfile)
		# recursively access file names in subdirectories
		elif os.path.isdir(dirfile) and subdir:
			#print "Accessing directory:", dirfile
			fileList.extend(get_stored_files(dirfile, subdir, *args))
	return fileList
