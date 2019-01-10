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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301,
# USA.

from __future__ import print_function

import os
import sys
from pyfile import *
from pyfile.progressbar import ProgressBar
from pyfile.threadpool import *
import mutex


def compare_all_files(file_name='file', magdir='Magdir', exact=False):
    pool = ThreadPool(4)
    m = mutex.mutex()

    split_patterns(magdir, file_name)
    compile_patterns(file_name)
    compiled = is_compilation_supported(file_name)

    entries = get_stored_files("db")

    def store_mimedata(data):
        metadata = get_full_metadata(data[0], file_name, compiled)
        stored_metadata = get_stored_metadata(data[0])
        text = "PASS " + data[0]
        if is_regression(stored_metadata, metadata, exact):
            text = "FAIL " + data[0] + "\n" + \
                   get_diff(stored_metadata, metadata, exact)
        return text

    def data_print(data):
        print(data)
        m.unlock()

    def data_stored(data):
        m.lock(data_print, data)

    for i, entry in enumerate(entries):
        # Insert tasks into the queue and let them run
        pool.queueTask(store_mimedata, (entry, i % 2), data_stored)

    # When all tasks are finished, allow the threads to terminate
    pool.joinAll()
    print('')


def main():
    """Parse arguments, call :py:func:`compare_all_files`."""
    file_name = 'file'
    magdir = "Magdir"
    exact = False

    if len(sys.argv) >= 3:
        file_name = sys.argv[1]
        magdir = sys.argv[2]
    elif (len(sys.argv) == 2 and sys.argv[1] == "-h") or len(sys.argv) == 1:
        print("Compares files in database with output of current file binary.")
        print(sys.argv[0] + " [path_to_magdir_directory] [file_name]")
        print("  Default path_to_magdir_directory='Magdir'")
        print("  Default file_name='file'")
        print("Examples:")
        print("  " + sys.argv[0] + " file-5.07;")
        print("  " + sys.argv[0] + " file-5.07 file-5.04/magic/Magdir;")
        sys.exit(0)

    if magdir == "exact":
        exact = True
        magdir = "Magdir"

    if len(sys.argv) == 4 and sys.argv[3] == "exact":
        exact = True

    file_name = sys.argv[1]
    compare_all_files(file_name, magdir, exact)


# run this only if started as script from command line
if __name__ == '__main__':
    main()
