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
import pickle
from progressbar import ProgressBar
import hashlib

COMPILED_SUFFIX = ".mgc"

def mkdir_p(path):
	try:
		os.makedirs(path)
	except OSError as exc: # Python >2.5
		if exc.errno == errno.EEXIST:
			pass
		else: raise

def get_file_output(filename, file_binary = "file"):
	pipe = Popen("file -b " + filename, shell=True, bufsize=4096, stdout=PIPE).stdout
	output = pipe.read()
	return output

def get_file_mime(filename, file_binary = "file"):
	pipe = Popen("file -ib " + filename, shell=True, bufsize=4096, stdout=PIPE).stdout
	output = pipe.read()
	return output

def get_simple_metadata(filename, file_binary = "file"):
	metadata = {}
	metadata['output'] = get_file_output(filename, file_binary)
	metadata['mime'] =  get_file_mime(filename, file_binary)
	return metadata

def split_patterns(magdir = "Magdir", file_name = "file"):
	FILE_BINARY_HASH = hashlib.sha224(file_name).hexdigest()
	outputdir = ".mgc_temp/" + FILE_BINARY_HASH + "/output"
	mkdir_p(outputdir)
	pattern_id = 0

	files = os.listdir(magdir)
	files.sort()
	prog = ProgressBar(0, len(files), 50, mode='fixed', char='#')
	for f in files:
		fd = open(os.path.join(magdir, f), "r")
		buff = ""
		in_pattern = False
		prog.increment_amount()
		print prog, "Splitting patterns", '\r',
		sys.stdout.flush()
		lines = fd.readlines()
		for i,line in enumerate(lines):
			if line.strip().startswith("#") or len(line.strip()) == 0:
				continue
			#print line.strip()
			if line.strip()[0].isdigit():
				if in_pattern:
					fd_out = open(os.path.join(outputdir, str(pattern_id)), "w")
					fd_out.write(buff)
					fd_out.close()
				buff = ""
				in_pattern = True
				pattern_id += 1
				buff += "# Automatically generated from:\n"
				buff += "#" + f + ":" + str(i) + "\n"
				buff += line
			elif line.strip().startswith(">") or line.strip().startswith("!"):
				if in_pattern:
					buff += line
				else:
					print "broken pattern in file '" + f + "':" + str(i)
		if in_pattern:
			fd_out = open(os.path.join(outputdir, str(pattern_id)), "w")
			fd_out.write(buff)
			fd_out.close()
		fd.close()
	print ''

def compile_patterns(file_name = "file"):
	FILE_BINARY_HASH = hashlib.sha224(file_name).hexdigest()
	magdir = ".mgc_temp/" + FILE_BINARY_HASH + "/output"
	files = os.listdir(magdir)
	files.sort()
	mkdir_p(".mgc_temp")
	mkdir_p(".mgc_temp/" + FILE_BINARY_HASH)
	prog = ProgressBar(0, len(files), 50, mode='fixed', char='#')
	for i,f in enumerate(files):
		if not os.path.exists(".mgc_temp/" + FILE_BINARY_HASH + "/.find-magic.tmp." + str(i) + ".mgc"):
			fd = open(os.path.join(magdir, f), "r")
			buf = fd.read()
			fd.close()
			tmp = open(".mgc_temp/" + FILE_BINARY_HASH + "/.find-magic.tmp", "a")
			tmp.write(buf)
			tmp.flush()
			tmp.close()
			#os.chdir(".mgc_temp")
			#print "cp .mgc_temp/.find-magic.tmp .mgc_temp/.find-magic.tmp." + str(i) + ";" + FILE_BINARY + " -C -m .mgc_temp/.find-magic.tmp." + str(i) + ";"
			#mv .find-magic.tmp." + str(i) + ".mgc .mgc_temp/;
			os.system("cp .mgc_temp/" + FILE_BINARY_HASH + "/.find-magic.tmp .mgc_temp/" + FILE_BINARY_HASH + "/.find-magic.tmp." + str(i) + ";file -C -m .mgc_temp/" + FILE_BINARY_HASH + "/.find-magic.tmp." + str(i) + ";")
			if os.path.exists(".find-magic.tmp." + str(i) + ".mgc"):
				os.system("mv .find-magic.tmp." + str(i) + ".mgc .mgc_temp/" + FILE_BINARY_HASH)
			#os.chdir("..")
		prog.increment_amount()
		print prog, "Compiling patterns", '\r',
		sys.stdout.flush()
	print ""

def get_full_metadata(infile, file_name = "file", compiled = True):
	COMPILED_SUFFIX = ".mgc"
	if not compiled:
		COMPILED_SUFFIX = ""
	FILE_BINARY_HASH = hashlib.sha224(file_name).hexdigest()
	magdir = ".mgc_temp/" + FILE_BINARY_HASH + "/output"
	FILE_BINARY = "file";
	files = os.listdir(magdir)
	files.sort()
	history = []
	tlist = []
	mkdir_p(".mgc_temp")
	a = 0
	b = len(files) - 1
	i = b

	a_out = ""
	b_out = None

	while True:
		f = files[i]
		#print FILE_BINARY + " " + infile + " -m .mgc_temp/" + FILE_BINARY_HASH + "/.find-magic.tmp." + str(i) + COMPILED_SUFFIX
		pipe = Popen(FILE_BINARY + " -b " + infile + " -m .mgc_temp/" + FILE_BINARY_HASH + "/.find-magic.tmp." + str(i) + COMPILED_SUFFIX, shell=True, bufsize=4096, stdout=PIPE).stdout
		last = pipe.read()
		if b_out == None:
			b_out = last
		# a---------i---------b
		# a_out ==  last   \solution here
		if last != b_out:
			a = i
			a_out = last
		# a-------------------i-------------------b
		#   solution here/    last       ==       b_out
		else:
			b = i
			b_out = last
		
		if i == a + (b - a) / 2:
			if b_out != last:
				i += 1
				last = b_out
			f = files[i]
			#if f in PATTERNS:
				#PATTERNS.remove(f);
			#print i, f
			fd = open(os.path.join(magdir, f), "r")
			buf = fd.read()
			fd.close()
			if os.path.exists(os.path.dirname(FILE_BINARY) + "/../magic/magic.mime.mgc"):
				pipe = Popen(FILE_BINARY + " -bi " + infile + " -m " + os.path.dirname(FILE_BINARY) + "/../magic/magic", shell=True, bufsize=4096, stdout=PIPE).stdout
			else:
				pipe = Popen(FILE_BINARY + " -bi " + infile + " -m .mgc_temp/" + FILE_BINARY_HASH + "/.find-magic.tmp." + str(i) + COMPILED_SUFFIX, shell=True, bufsize=4096, stdout=PIPE).stdout
			mime = pipe.read()
			tlist.append(last)
			index = infile.find('.')
			if index == -1:
				suffix = ""
			else:
				suffix = infile[index:]
			if last == "data\n" and i == 0:
				buf = ""
			return {'output':last, 'mime':mime, 'pattern':buf, "suffix":suffix}
		else:
			i = a + (b - a) / 2

def is_compilation_supported(file_binary = "file"):
	FILE_BINARY_HASH = hashlib.sha224(file_binary).hexdigest()
	if os.system("file /bin/sh -m .mgc_temp/" + FILE_BINARY_HASH + "/.find-magic.tmp.0.mgc > /dev/null") != 0:
		print ''
		print "This file version doesn't support compiled patterns => they won't be used"
		return False
	else:
		print 'Compiled patterns will be used'
		print ''
		return True


