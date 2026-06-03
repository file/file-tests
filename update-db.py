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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301,
# USA.

"""Run file(1) on all entries in db folder and save the output."""

from __future__ import print_function

import os
import sys
import getopt
from tqdm import tqdm
from pyfile.db import get_stored_files, get_stored_metadata, is_regression, get_diff, set_stored_metadata
from pyfile.file import print_file_info, get_simple_metadata, split_patterns, compile_patterns, is_compilation_supported, get_full_metadata
from multiprocessing.pool import ThreadPool

#: flag for error during :py:func:`update_all_files`
global_error = False


def update_all_files(file_name='file', magdir='Magdir', file_binary='file',
                     skip_patterns=False):
    """
    Run file(1) on all entries in db folder, save result in same folder

    Performs:
    (1) print a quick info on used file(1) binary
    (2) compiles patterns
    (3) Run in parallel on each db entry using a ThreadPool:
    (3a) get full metadata for file
    (3b) save metadata in db
    """
    print_file_info(file_binary)

    if not skip_patterns:
        split_patterns(magdir, file_name)
        compile_patterns(file_name, file_binary)
        compiled = is_compilation_supported(file_name, file_binary)

    entries = get_stored_files("db")
    if not entries:
        db_dir = os.path.join(os.getcwd(), 'db')     # TODO: not always correct
        raise ValueError('no files in db {0}'.format(db_dir))
        nentries = 1
    else:
        nentries = len(entries)
    visible_tasks_count = sum(1 for i in range(len(entries)) if not (i % 2))
    prog = tqdm(total=visible_tasks_count, bar_format='{l_bar}{bar:50}{r_bar}', ascii=' #')
    prog.set_description("Updating database")


    def store_mimedata(data):
        """Compute file output for single entry, save it."""
        entry, hide = data
        if skip_patterns:
            metadata = get_partial_metadata(entry, file_name, file_binary)
        else:
            metadata = get_full_metadata(entry, file_name, compiled, file_binary)

        if metadata['output'] is None:
            # Return the error back to the main thread safely
            return {"entry": entry, "hide": hide, "error": metadata['err']}
        else:
            set_stored_metadata(entry, metadata)
            return {"entry": entry, "hide": hide, "error": None}

    tasks = [(entry, index % 2) for index, entry in enumerate(entries)]
    global_error = False

    n_threads = 4

    # Use a context manager for the ThreadPool
    with ThreadPool(n_threads) as pool:
        # imap_unordered yields results as soon as any thread finishes
        for result in pool.imap_unordered(store_mimedata, tasks):
            entry = result["entry"]
            hide = result["hide"]
            error = result["error"]

            if error:
                global_error = True
                print(f'\nERROR for {entry}')
                print('ERROR running command', error[0])
                print('ERROR produced output', error[1])
                print("Error when executing File binary. Halting pool.")

                # This forcefully stops the pool from processing remaining queued items
                pool.terminate()
                break

            if not hide:
                prog.update(1)

    prog.close()
    print('')
    return global_error


def usage(ecode):
    """Print usage information and exit with given exit code."""
    print("Updates database.")
    print(sys.argv[0] +
          " [-v <version_name>] [-m <magdir>] [-b <file-binary>]")
    print("  Default path_to_magdir_directory='Magdir'")
    print("  Default version_name='file'")
    print("Examples:")
    print("  " + sys.argv[0] + " -v file-5.07;")
    print("  " + sys.argv[0] +
          " -v file-5.04-my-version -m file-5.04/magic/Magdir;")
    sys.exit(ecode)


def main():
    """Parse arguments and call :py:func:`update_all_files`."""
    file_name = 'file'
    file_binary = "file"
    magdir = "Magdir"
    skip_patterns = False
    args = sys.argv[1:]

    optlist, args = getopt.getopt(args, 'b:hm:v:s')

    for option, argument in optlist:
        if option == '-b':
            file_binary = argument
        elif option == '-m':
            magdir = argument
        elif option == '-h':
            usage(0)
        elif option == '-v':
            file_name = argument
        elif option == '-s':
            skip_patterns = True
        else:
            usage(1)

    sys.exit(update_all_files(file_name, magdir, file_binary, skip_patterns=skip_patterns))


# run this only if started as script from command line
if __name__ == '__main__':
    main()
