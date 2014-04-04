# Copyright (C) 2014 Red Hat, Inc.
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

def review_patches(patches):
	ret = 0
	for patch in patches:
		out = ""
		f = open(patch)

		added_files = []
		files_without_source = []

		for line in f.readlines():
			filename = ""
			if line.startswith("+++"):
				filename = line[4:-1]
			elif line.startswith("diff --git"):
				filename = line[line.rfind(" ") + 1:-1]

			if filename != "" and not filename in added_files:
				added_files.append(filename)
				if not filename.endswith(".source.txt"):
					files_without_source.append(filename)
		f.close()


		local_error = False

		added_files.sort()
		for f in added_files:
			ext_id = f.find(".")
			if ext_id != -1:
				ext = f[ext_id + 1:]
				if ext.endswith("source.txt"):
					real_db_file = f[:-len(".source.txt")]
					try:
						files_without_source.remove(real_db_file)
					except:
						out += "\t" + f + ": .source.txt found for non-existing file, expecting " + real_db_file + " in patch\n"
						ret = 1
						local_error = True
				else:
					db_dir = os.path.basename(os.path.dirname(f))
					if db_dir != ext:
						out += "\t" + f + ": File is not in proper directory according to extension\n"
						ret = 1
						local_error = True

		for f in files_without_source:
			out += "\t" + f + ": Does not have matching .source.txt file with license\n"
			ret = 1
			local_error = True

		if local_error:
			print "Patch", patch + ":"
			print out

	return ret;
		

if __name__ == '__main__':
	if len(sys.argv) == 1:
		print "Reviews patches for file-tests database."
		print """There are following rules currently:
 - Every file 'F' in file-tests database has to have matching 'F.source.txt'
   file with the license information. Note that case sensitivity is important
   and must be respected.
 - Every file with extension '.X' has to be in directory 'db/X' according to
   its extension. Note that case sensitivity is important and must be
   respected.
"""
		print "Usage: " + sys.argv[0] + " [[patch1], [patch2], ...]"
		print "Usage: " + sys.argv[0] + " *.patch"
		sys.exit(0)
	sys.exit(review_patches(sys.argv[1:]))