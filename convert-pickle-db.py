#!/usr/bin/env python

""" Convert metdata saved as .pickle (old format) to json (the new format).

Use this if there are .pickle files in your db/ folder

.. codeauthor:: Intra2net AG <opensource@intra2net.com>
"""

import sys
import os
from os.path import isfile
import pickle
from pyfile.db import set_stored_metadata, get_stored_files


def main():
    """
    Main function, called when running file as script

    see module doc for more info
    """
    # get all names of files (except .json, .source.txt) in db
    # (luckily, there is no .pickle nor .json as entry in db)
    entries = get_stored_files("db")

    # loop over all entries
    n_errors = 0
    n_converted = 0
    for entry in entries:
        # continue if there is no pickle with saved metadata
        old_filename = entry + '.pickle'
        if not isfile(old_filename):
            continue

        try:
            # unpickle stored metadata, save as json
            with open(old_filename, 'r') as file_handle:
                metadata = pickle.load(file_handle)
            set_stored_metadata(entry, metadata)

            # remove pickle
            os.unlink(old_filename)
            n_converted += 1
        except Exception as exc:
            print('Could not convert {}: {}'.format(entry, exc))
            n_errors += 1

    print('Converted {} entries, {} conversion attempts failed'
          .format(n_converted, n_errors))

    return 1 if n_errors else 0


if __name__ == '__main__':
    sys.exit(main())
