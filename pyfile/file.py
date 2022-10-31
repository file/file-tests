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

"""Wrapper for `file(1)` with additional pattern compilation & search."""

from __future__ import print_function

import os
import sys
import errno
from subprocess import Popen, PIPE
import hashlib
import re
from progressbar import ProgressBar


def print_file_info(file_binary='file'):
    """`print()` absolute path and version of given `file(1)` binary."""
    if not file_binary.startswith("/") and not file_binary.startswith("./") \
            and not file_binary.startswith("../"):
        popen = Popen('which ' + file_binary, shell=True, bufsize=4096,
                      stdout=PIPE)
        pipe = popen.stdout
        output_which = pipe.read().strip()
        if popen.wait() != 0:
            raise ValueError('could not query {0} for its version ({1})!'
                             .format(file_binary, output_which))
    else:
        output_which = file_binary
    popen = Popen(file_binary + " --version", shell=True, bufsize=4096,
                  stdout=PIPE)
    pipe = popen.stdout
    output_ver = pipe.read().strip()
    if popen.wait() not in (0, 1):
        raise ValueError('could not query {0} for its version ({1})!'
                         .format(file_binary, output_ver))
    print('using file from', output_which)
    print('version is', output_ver)


def mkdir_p(path):
    """Wrapper around :py:func:`os.makedirs` that catches EEXIST."""
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST:
            pass
        else:
            raise


def get_file_output(filename, binary="file"):
    """Run file(1) binary on given filename, return output."""
    popen = Popen(binary + " -b " + filename, shell=True, bufsize=4096,
                  stdout=PIPE, stderr=PIPE)
    pipe = popen.stdout
    output = pipe.read()
    output_err = popen.stderr.read()
    if popen.wait() != 0:
        return "Error while calling file, output: " + str(output) + \
               str(output_err)
    return output


def get_file_mime(filename, binary="file"):
    """Run file(1) binary with mime option on given filename, return output."""
    popen = Popen(binary + " -ib " + filename, shell=True, bufsize=4096,
                  stdout=PIPE, stderr=PIPE)
    pipe = popen.stdout
    output = pipe.read()
    output_err = popen.stderr.read()
    if popen.wait() != 0:
        return "Error while calling file, output: " + str(output) + \
               str(output_err)
    return output


def get_simple_metadata(filename, binary="file"):
    """
    Get output of `file` and `file -i` on given filename.

    Calls :py:func:`get_file_output` and :py:func:`get_file_mime` and saves
    them in a `dict` as fields `output` and `mime`.

    Quick version of :py:func:`get_full_metadata`.
    """
    metadata = {}
    metadata['output'] = get_file_output(filename, binary)
    metadata['mime'] = get_file_mime(filename, binary)
    return metadata


def _split_patterns(pattern_id=0, magdir="Magdir", file_name="file",
                    only_name=False):
    """
    Actual worker function for :py:func:split_patterns`.

    Creates `output` dir in `.mgc_temp`. Loops over pattern files in `magdir`
    and for each pattern found in each file creates an extra file in `output`
    dir with just that pattern.

    Output file name are just their pattern_id, starting with id given as arg.

    Arg `file_name` only used for getting dir name through hashing. `file(1)`
    is not called here.

    Returns number of pattern files thus created.
    """
    file_binary_hash = hashlib.sha224(file_name).hexdigest()
    outputdir = ".mgc_temp/" + file_binary_hash + "/output"
    mkdir_p(outputdir)

    files = os.listdir(magdir)
    files.sort()   # TODO: sort like the others?
    if not files:
        raise ValueError('no files found in Magdir {0}'
                         .format(os.path.join(os.getcwd(), magdir)))
    prog = ProgressBar(0, len(files), 50, mode='fixed', char='#')
    for loop_file_name in files:
        mfile = os.path.join(magdir, loop_file_name)
        if os.path.isdir(mfile):
            continue
        buff = ""
        in_pattern = False
        prog.increment_amount()
        print(prog, "Splitting patterns", end='\r')
        sys.stdout.flush()
        with open(mfile, "r") as reader:
            lines = reader.readlines()
        for line_idx, line in enumerate(lines):
            if line.strip().startswith("#") or not line.strip():
                continue
            # print(line.strip()
            if line.strip()[0].isdigit() or \
                    (line.strip()[0] == '-' and line.strip()[1].isdigit()):
                # start of next pattern. first write finished pattern to file
                if in_pattern:
                    with open(os.path.join(outputdir, str(pattern_id)), "w") \
                            as writer:
                        writer.write(buff)
                    in_pattern = False
                buff = ""
                if only_name:
                    if not re.match("^[0-9]*(\\s)*name", line.strip()):
                        continue
                in_pattern = True
                pattern_id += 1
                buff += "#" + loop_file_name + "\n"
                buff += "# Automatically generated from:\n"
                buff += "#" + loop_file_name + ":" + str(line_idx) + "\n"
                buff += line
            elif line.strip().startswith(">") or line.strip().startswith("!"):
                if in_pattern:
                    buff += line
                elif not only_name:
                    print("broken pattern in file '" + loop_file_name + "':" +
                          str(line_idx))
        if in_pattern:
            with open(os.path.join(outputdir, str(pattern_id)), "w") as writer:
                writer.write(buff)
    return pattern_id


def split_patterns(magdir="Magdir", file_name="file"):
    """
    Given a dir with magic pattern files, create dir with isolated patterns.

    First create isolated pattern files for patterns with a "name" attribute.
    Then create pattern files for all patterns.
    """
    pattern_id = _split_patterns(0, magdir, file_name, True)
    _split_patterns(pattern_id, magdir, file_name)

    print('')


def compile_patterns(file_name="file", file_binary="file"):
    """
    Creates increasingly complex magic files.

    Loops over isolated patterns, re-assembles original magic files pattern by
    pattern and always re-creates a magic file. Creates files
    `.mgc_temp/HASH/.find-magic.tmp.PATTERN-ID.mgc` used by
    :py:func:`get_full_metadata`.

    This requires quite some space on disc.
    """
    file_binary_hash = hashlib.sha224(file_name).hexdigest()
    magdir = ".mgc_temp/" + file_binary_hash + "/output"
    files = os.listdir(magdir)
    if not files:
        raise ValueError('no files found in Magdir {0}'
                         .format(os.path.join(os.getcwd(), magdir)))
    files.sort(key=lambda x: [int(x)])
    mkdir_p(".mgc_temp")
    mkdir_p(".mgc_temp/" + file_binary_hash)
    mkdir_p(".mgc_temp/" + file_binary_hash + "/tmp")
    prog = ProgressBar(0, len(files), 50, mode='fixed', char='#')

    for file_index, loop_file_name in enumerate(files):
        out_file = ".mgc_temp/" + file_binary_hash + "/.find-magic.tmp." + \
                   str(file_index) + ".mgc"
        if not os.path.exists(out_file):
            with open(os.path.join(magdir, loop_file_name), "r") as reader:
                buf = reader.read()
            # read name of original pattern file in magic dir from first line
            mfile = buf.split("\n")[0][1:]

            # iteratively re-assemble original pattern file
            with open(os.path.join(".mgc_temp/" + file_binary_hash +
                                   "/tmp/" + mfile), "a") as appender:
                appender.write(buf)
                appender.flush()
            # tmp = open(".mgc_temp/" + file_binary_hash + "/.find-magic.tmp",
            #            "a")
            # tmp.write(buf)
            # tmp.flush()
            # tmp.close()
            # os.chdir(".mgc_temp")
            # print("cp .mgc_temp/.find-magic.tmp " +
            #       ".mgc_temp/.find-magic.tmp." + str(file_index) + ";" +
            #       file_binary + " -C -m .mgc_temp/.find-magic.tmp." +
            #       str(file_index) + ";")
            # mv .find-magic.tmp." + str(file_index) + ".mgc .mgc_temp/;

            # os.system("cp .mgc_temp/" + file_binary_hash +
            #           "/.find-magic.tmp .mgc_temp/" + file_binary_hash +
            #           "/.find-magic.tmp." + str(file_index) + ";" +
            #           "file -C -m .mgc_temp/" + file_binary_hash +
            #           "/.find-magic.tmp." + str(file_index) + ";")
            cmd = file_binary + " -C -m .mgc_temp/" + file_binary_hash + "/tmp"
            ret_code = os.system(cmd)
            if ret_code != 0:
                raise ValueError('command {0} returned non-zero exit code {1}!'
                                 .format(cmd, ret_code))
            if os.path.exists("tmp.mgc"):    # TODO: move without forking shell
                ret_code = os.system("mv tmp.mgc " + out_file)
                if ret_code != 0:
                    raise ValueError('moving tmp.mgc to {0} failed with code '
                                     '{1}!'.format(out_file, ret_code))
            # os.chdir("..")
        prog.increment_amount()
        print(prog, "Compiling patterns", end='\r')
        sys.stdout.flush()
    print("")


def get_partial_metadata(infile, file_name, file_binary="file"):
    """
    plain output of file ("output") and mime type ("mime").

    As opposed to :py:func:`get_full_metadata` does not include the relevant
    line in magic file ("pattern"), which makes this much faster and easier
    and avoids the trouble of compiling lots of patterns that need lots of
    disc space.
    """
    cmd = file_binary + " -b " + infile
    popen = Popen(cmd, shell=True, bufsize=4096, stdout=PIPE)
    pipe = popen.stdout
    out_curr = pipe.read()
    if popen.wait() != 0:
        return dict(output=None, mime=None, pattern=None, suffix=None,
                    err=(cmd, out_curr.strip()))

    cmd = file_binary + " -bi " + infile
    popen = Popen(cmd, shell=True, bufsize=4096, stdout=PIPE)
    pipe = popen.stdout
    mime = pipe.read()
    if popen.wait() != 0:
        return dict(output=None, mime=None, pattern=None, suffix=None,
                    err=(cmd, mime.strip()))
    index = infile.find('.')
    if index == -1:
        suffix = ""
    else:
        suffix = infile[index:]
    return dict(output=out_curr, mime=mime, pattern="", suffix=suffix)


def get_full_metadata(infile, file_name="file", compiled=True,
                      file_binary="file"):
    """
    file-output plus binary search to find the relevant line in magic file.

    Run `file(1)` repeatedly with different magic files created in
    :py:func`compile_patterns` until the one pattern is identified that defines
    the `file(1)` output of the given `infile`.
    """
    compiled_suffix = ".mgc"
    if not compiled:
        compiled_suffix = ""
    file_binary_hash = hashlib.sha224(file_name).hexdigest()
    magdir = ".mgc_temp/" + file_binary_hash + "/output"
    files = os.listdir(magdir)
    files.sort(key=lambda x: [int(x)])
    tlist = []
    mkdir_p(".mgc_temp")

    # Divide and conquer: find the relevant pattern
    idx_left = 0                # left-most index to consider
    idx_rigt = len(files) - 1   # right-most index to consider
    idx_curr = idx_rigt         # some index in the middle we currently test

    # out_left = ""             # ouput at idx_left, unused
    out_rigt = None             # output at idx_rigt

    while True:
        file_curr = files[idx_curr]          # file name at idx_curr
        cmd = file_binary + " -b " + infile + " -m .mgc_temp/" + \
              file_binary_hash + "/.find-magic.tmp." + str(idx_curr) + \
              compiled_suffix
        # print(file_binary + " " + infile + " -m .mgc_temp/" +
        #       file_binary_hash + "/.find-magic.tmp." + str(idx_curr) +
        #       compiled_suffix)
        popen = Popen(cmd, shell=True, bufsize=4096, stdout=PIPE)
        pipe = popen.stdout
        out_curr = pipe.read()
        if popen.wait() != 0:
            return dict(output=None, mime=None, pattern=None, suffix=None,
                        err=(cmd, out_curr.strip()))
        if out_rigt is None:   # first iteration, uses complete magic file
            out_rigt = out_curr
        # idx_left---------idx_curr---------idx_rigt
        # out_left   ==    out_curr     \solution here
        if out_curr != out_rigt:
            idx_left = idx_curr
            # out_left = out_curr
        # idx_left-------------------idx_curr-------------------idx_rigt
        #   solution here/           out_curr        ==         out_rigt
        else:
            idx_rigt = idx_curr
            out_rigt = out_curr

        # are we done?
        if idx_curr == idx_left + (idx_rigt - idx_left) / 2:
            # idx_* are so close together that next iteration idx_curr would
            # not change --> we are done
            if out_rigt != out_curr:
                idx_curr += 1
                out_curr = out_rigt
            file_curr = files[idx_curr]
            # if file_curr in PATTERNS:
            # PATTERNS.remove(file_curr);
            # print(idx_curr, file_curr)
            with open(os.path.join(magdir, file_curr), "r") as reader:
                buf = reader.read()
            if os.path.exists(os.path.dirname(file_binary) +
                              "/../magic/magic.mime.mgc"):
                cmd = file_binary + " -bi " + infile + " -m " + \
                      os.path.dirname(file_binary) + "/../magic/magic"
            else:
                cmd = file_binary + " -bi " + infile + " -m .mgc_temp/" + \
                      file_binary_hash + "/.find-magic.tmp." + str(idx_curr) +\
                      compiled_suffix
            popen = Popen(cmd, shell=True, bufsize=4096, stdout=PIPE)
            pipe = popen.stdout
            mime = pipe.read()
            if popen.wait() != 0:
                return dict(output=None, mime=None, pattern=None, suffix=None,
                            err=(cmd, mime.strip()))
            tlist.append(out_curr)
            index = infile.find('.')
            if index == -1:
                suffix = ""
            else:
                suffix = infile[index:]
            if out_curr == "data\n" and idx_curr == 0:
                buf = ""
            return dict(output=out_curr, mime=mime, pattern=buf, suffix=suffix)
        else:
            # continue: set idx_curr to middle between idx_left and idx_rigt
            idx_curr = idx_left + (idx_rigt - idx_left) / 2


def is_compilation_supported(file_name="file", file_binary="file"):
    """Determine whether data from :py:func:`compile_patterns` is available."""
    file_binary_hash = hashlib.sha224(file_name).hexdigest()
    if os.system(file_binary + " /bin/sh -m .mgc_temp/" + file_binary_hash +
                 "/.find-magic.tmp.0.mgc > /dev/null") != 0:
        print('')
        print("This file version doesn't support compiled patterns "
              "=> they won't be used")
        return False

    print('Compiled patterns will be used')
    print('')
    return True
