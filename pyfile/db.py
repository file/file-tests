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

"""Load file(1) output from db, compare it, store output in db."""


import os
import json
import difflib
import mimetypes
from cStringIO import StringIO
mimetypes.init()


# suffix for files containing saved metadata
DB_FILE_SUFFIX = '.json'


def get_stored_metadata(filename):
    """Retrieve metadata stored for given entry in db."""
    with open(filename + DB_FILE_SUFFIX, 'rt') as file_handle:
        return json.load(file_handle)


def set_stored_metadata(filename, metadata):
    """Store given metadata for given entry in db."""
    with open(filename + DB_FILE_SUFFIX, 'wt') as file_handle:
        json.dump(metadata, file_handle, check_circular=False, indent=4,
                  sort_keys=True)


def is_regression(meta1, meta2, exact=False, ratio=0.7):
    """
    Determine whether two file(1) outputs for same entry are incompatible.

    Metadata can be obtained from py:func`get_stored_metadata` or
    :py:func:`file.get_full_metadata`.

    :param dict meta1: metadata for entry1.
    :param dict meta2: metadata for entry2.
    :param bool exact: whether output has to match letter for letter (True) or
                       whether slight changes are allowed.
    :param float ratio: Amount of difference required for slightly different
                        entries to be considered the same:
                        `0` = all changes allowed; `1` = need perfect match.
    :returns: True if there is a (significant) difference between `meta1`
              and `meta2`.

    .. todo:: Reduce code duplication with function get_diff
    """
    if meta1['output'] is None or meta2['output'] is None:
        return True
    if meta1['output'] != meta2['output']:
        # previous file didn't detect it, so we hope new output is ok
        if not meta1['output'].endswith("data\n"):
            if exact:
                if meta1['output'] != meta2['output']:
                    return True
            else:
                match = difflib.SequenceMatcher(None, meta1['output'],
                                                meta2['output']).ratio()
                if match < ratio:
                    # print >> sys.stderr, "Expected:%sGot     :%s" \
                    #          % (meta2['output'], meta1['output'])
                    return True

    mime = meta2['mime'].split(":")[-1].split(";")[0].strip()
    old_mime = meta1['mime'].split(":")[-1].split(";")[0].strip()

    # if old_mime is empty, then previous version of File didn't know that
    # filetype.  we will hope that new mime is right.
    if old_mime and old_mime != mime:
        ext = os.path.splitext(mime)[-1]
        # it's not error if new mimetype is correct type for that extension.
        if ext in mimetypes.types_map.keys():
            expected = mimetypes.types_map[ext]
            if expected == mime:
                return True
            # else:
            #   print >> sys.stderr, "Expected:%s" % (expected)
        # print >> sys.stderr, "Expected:%s\nGot     :%s" % (old_mime, mime)
        return True
    return False


def get_diff(meta1, meta2, exact=False, ratio=0.7):
    """
    Get textual description about how well file(1) outputs match.

    Like :py:func:`is_regression`, except the output is a description instead
    of just a bool.

    .. todo:: Reduce code duplication with function is_regression
    """
    if meta1['output'] is None or meta2['output'] is None:
        return "Output is None, was there error during File execution?"

    text = ""
    if meta1['output'] != meta2['output']:
        # previous file didn't detect it, so we hope new output is ok
        if not meta1['output'].endswith("data\n"):
            if exact:
                if meta1['output'] != meta2['output']:
                    text = "Expected :%sGot      :%s" % (meta1['output'],
                                                         meta2['output'])
            else:
                match = difflib.SequenceMatcher(None, meta1['output'],
                                                meta2['output']).ratio()
                if match < ratio:
                    text = "Expected :%sGot      :%s" % (meta1['output'],
                                                         meta2['output'])

    mime = meta2['mime'].split(":")[-1].split(";")[0].strip()
    old_mime = meta1['mime'].split(":")[-1].split(";")[0].strip()

    want_mime_diff = False

    # if old_mime is empty, then previous version of File didn't know that
    # filetype.  we will hope that new mime is right.
    if old_mime and old_mime != mime:
        ext = os.path.splitext(mime)[-1]
        # it's not error if new mimetype is correct type for that extension.
        if ext in mimetypes.types_map.keys():
            expected = mimetypes.types_map[ext]
            if expected != mime:
                want_mime_diff = True
        want_mime_diff = True    # TODO: this invalidates lines above
    if want_mime_diff:
        text += "Expected :%sGot      :%s" % (meta1['mime'], meta2['mime'])

    if text != "":
        if ('pattern' in meta1) and ('pattern' in meta2) and \
                meta1['pattern'] != "" and meta2['pattern'] != "":
            for line in difflib.unified_diff(
                    StringIO(meta1['pattern']).readlines(),
                    StringIO(meta2['pattern']).readlines()):
                text += line
    return text


def get_stored_files(dir_name, subdir=True, *args):
    r"""
    Return a list of file names found in directory 'dir_name'.

    If 'subdir' is True, recursively access subdirectories under 'dir_name'.
    Additional arguments, if any, are file extensions to match filenames.
    Matched file names are added to the list.
    If there are no additional arguments, all files found in the directory are
    added to the list.
    Example usage: file_list = dirEntries(r'H:\TEMP', False, 'txt', 'py')
    Only files with 'txt' and 'py' extensions will be added to the list.
    Example usage: file_list = dirEntries(r'H:\TEMP', True)
    All files and all the files in subdirectories under H:\TEMP will be added
    to the list.
    """
    file_list = []
    for file_name in os.listdir(dir_name):
        dirfile = os.path.join(dir_name, file_name)
        if os.path.isfile(dirfile):
            if not args:
                if not dirfile.endswith(DB_FILE_SUFFIX) and \
                        not dirfile.endswith(".source.txt"):
                    file_list.append(dirfile)
            else:
                if os.path.splitext(dirfile)[1][1:] in args:
                    file_list.append(dirfile)
        # recursively access file names in subdirectories
        elif os.path.isdir(dirfile) and subdir:
            # print "Accessing directory:", dirfile
            file_list.extend(get_stored_files(dirfile, subdir, *args))
    return file_list
