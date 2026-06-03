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
import subprocess
import hashlib
import re
from tqdm import tqdm

def print_file_info(file_binary='file'):
    """`print()` absolute path and version of given `file(1)` binary."""

    if not any(file_binary.startswith(p) for p in ("/", "./", "../")):
        resolved_path = shutil.which(file_binary)
        if not resolved_path:
            raise ValueError(f"could not find '{file_binary}' in PATH")
        output_which = resolved_path.encode('utf-8')
    else:
        output_which = file_binary.encode('utf-8')

    try:
        # Pass args as a list instead of a string to avoid shell=True
        result = subprocess.run(
            [file_binary, "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False # We handle return codes manually below
        )
    except Exception as e:
        raise ValueError(f"failed to execute {file_binary}: {e}")

    output_ver = result.stdout.strip()

    if result.returncode not in (0, 1):
        raise ValueError('could not query {0} for its version ({1})!'
                         .format(file_binary, output_ver))

    # If you need strings for printing, decode them safely
    print('using file from', output_which.decode('utf-8', errors='ignore'))
    print('version is', output_ver.decode('utf-8', errors='ignore'))

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
    try:
        # Pass arguments as a list to avoid shell parsing issues with filenames
        # subprocess.run handles reading both stdout and stderr concurrently without deadlocks
        result = subprocess.run(
            [binary, "-b", filename],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False
        )
    except Exception as e:
        return f"Error executing process: {e}"

    # Check the return code safely
    if result.returncode != 0:
        return ("Error while calling file, output: " +
                str(result.stdout) + str(result.stderr))

    # Modern decode with 'replace' or 'ignore' to prevent UnicodeDecodeErrors
    # if the file command returns strange bytes.
    return result.stdout.decode('utf-8', errors='replace')

def get_file_mime(filename, binary="file"):
    """Run file(1) binary with mime option on given filename, return output."""
    try:
        # Passing arguments as a list removes shell=True and handles spaces/special characters safely.
        # subprocess.run dynamically drains stdout and stderr simultaneously to prevent deadlocks.
        result = subprocess.run(
            [binary, "-ib", filename],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False
        )
    except Exception as e:
        return f"Error executing process: {e}"

    if result.returncode != 0:
        return ("Error while calling file, output: " +
                str(result.stdout) + str(result.stderr))

    # Using errors='replace' protects you from crashing if a file outputs malformed UTF-8 characters.
    return result.stdout.decode('utf-8', errors='replace')

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
    file_binary_hash = hashlib.sha224(file_name.encode()).hexdigest()
    outputdir = ".mgc_temp/" + file_binary_hash + "/output"
    mkdir_p(outputdir)

    files = os.listdir(magdir)
    files.sort()   # TODO: sort like the others?
    if not files:
        raise ValueError('no files found in Magdir {0}'
                         .format(os.path.join(os.getcwd(), magdir)))
    prog = tqdm(total=len(files), bar_format='{l_bar}{bar:50}{r_bar}', ascii=' #')
    prog.set_description("Splitting patterns")
    for loop_file_name in files:
        mfile = os.path.join(magdir, loop_file_name)
        if os.path.isdir(mfile):
            continue
        buff = ""
        in_pattern = False
        prog.update(1)
        with open(mfile, "r") as reader:
            lines = reader.readlines()
        for line_idx, line in enumerate(lines):
            if line.strip().startswith("#") or not line.strip():
                continue
            # print(line.strip())
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
    file_binary_hash = hashlib.sha224(file_name.encode()).hexdigest()
    magdir = ".mgc_temp/" + file_binary_hash + "/output"
    files = os.listdir(magdir)
    if not files:
        raise ValueError('no files found in Magdir {0}'
                         .format(os.path.join(os.getcwd(), magdir)))
    files.sort(key=lambda x: [int(x)])
    mkdir_p(".mgc_temp")
    mkdir_p(".mgc_temp/" + file_binary_hash)
    mkdir_p(".mgc_temp/" + file_binary_hash + "/tmp")
    prog = tqdm(total=len(files), bar_format='{l_bar}{bar:50}{r_bar}', ascii=' #')
    prog.set_description("Compiling patterns")

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
        prog.update(1)
    print("")

import subprocess

def get_partial_metadata(infile, file_name, file_binary="file"):
    """
    plain output of file ("output") and mime type ("mime").

    As opposed to :py:func:`get_full_metadata` does not include the relevant
    line in magic file ("pattern"), which makes this much faster and easier
    and avoids the trouble of compiling lots of patterns that need lots of
    disc space.
    """
    # --- 1. Get plain file description (-b) ---
    cmd1 = [file_binary, "-b", infile]
    try:
        result1 = subprocess.run(cmd1, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    except Exception as e:
        return dict(output=None, mime=None, pattern=None, suffix=None, err=(" ".join(cmd1), str(e)))

    out_curr = result1.stdout
    if result1.returncode != 0:
        return dict(output=None, mime=None, pattern=None, suffix=None,
                    err=(" ".join(cmd1), out_curr.strip()))

    # --- 2. Get mime type (-bi) ---
    cmd2 = [file_binary, "-bi", infile]
    try:
        result2 = subprocess.run(cmd2, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    except Exception as e:
        return dict(output=None, mime=None, pattern=None, suffix=None, err=(" ".join(cmd2), str(e)))

    mime = result2.stdout
    if result2.returncode != 0:
        return dict(output=None, mime=None, pattern=None, suffix=None,
                    err=(" ".join(cmd2), mime.strip()))

    # --- 3. Extract suffix safely ---
    # Using python's built-in pathlib or rfind is safer for extracting extensions
    index = infile.rfind('.') # Use rfind to get the actual extension if there are dots in the path directory
    if index == -1:
        suffix = b"" if isinstance(out_curr, bytes) else ""
    else:
        suffix = infile[index:]
        # Match types if your legacy code expects bytes for suffix
        if isinstance(out_curr, bytes) and isinstance(suffix, str):
            suffix = suffix.encode('utf-8')

    # Ensure everything going to the database is a decoded string, not bytes
    return dict(
        output=out_curr.decode('utf-8', errors='replace') if isinstance(out_curr, bytes) else out_curr,
        mime=mime.decode('utf-8', errors='replace') if isinstance(mime, bytes) else mime,
        pattern="" if isinstance(out_curr, str) else "",
        suffix=suffix.decode('utf-8', errors='replace') if isinstance(suffix, bytes) else suffix
    )

import os
import hashlib
import subprocess

def get_full_metadata(infile, file_name="file", compiled=True, file_binary="file"):
    """
    file-output plus binary search to find the relevant line in magic file.

    Run `file(1)` repeatedly with different magic files created in
    :py:func`compile_patterns` until the one pattern is identified that defines
    the `file(1)` output of the given `infile`.
    """
    compiled_suffix = ".mgc" if compiled else ""
    file_binary_hash = hashlib.sha224(file_name.encode()).hexdigest()
    magdir = f".mgc_temp/{file_binary_hash}/output"

    try:
        files = os.listdir(magdir)
        files.sort(key=lambda x: int(x))
    except Exception as e:
        return dict(output=None, mime=None, pattern=None, suffix=None,
                    err=("Sorting files", f"Failed to list/sort {magdir}: {e}"))

    os.makedirs(".mgc_temp", exist_ok=True)

    # Divide and conquer: find the relevant pattern
    idx_left = 0
    idx_rigt = len(files) - 1
    idx_curr = idx_rigt
    out_rigt = None

    while True:
        magic_file_path = f".mgc_temp/{file_binary_hash}/.find-magic.tmp.{idx_curr}{compiled_suffix}"

        # Safe array arguments instead of shell strings
        cmd = [file_binary, "-b", infile, "-m", magic_file_path]

        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        except Exception as e:
            return dict(output=None, mime=None, pattern=None, suffix=None, err=(" ".join(cmd), str(e)))

        out_curr = result.stdout
        if result.returncode != 0:
            return dict(output=None, mime=None, pattern=None, suffix=None,
                        err=(" ".join(cmd), out_curr.strip()))

        if out_rigt is None:
            out_rigt = out_curr

        if out_curr != out_rigt:
            idx_left = idx_curr
        else:
            idx_rigt = idx_curr
            out_rigt = out_curr

        # FIX 1: Use absolute integer division (//) to avoid infinite float matching loops
        if idx_curr == idx_left + (idx_rigt - idx_left) // 2:
            if out_rigt != out_curr:
                idx_curr += 1
                out_curr = out_rigt

            file_curr = files[idx_curr]

            # FIX 2: Open with latin-1 encoding to safely read raw magic patterns without crashing
            try:
                with open(os.path.join(magdir, file_curr), "r", encoding="latin-1") as reader:
                    buf = reader.read()
            except Exception as e:
                buf = f"Error reading pattern file: {e}"

            # --- Mime check block ---
            magic_mime_path = f"{os.path.dirname(file_binary)}/../magic/magic.mime.mgc"
            if os.path.exists(magic_mime_path):
                cmd = [file_binary, "-bi", infile, "-m", f"{os.path.dirname(file_binary)}/../magic/magic"]
            else:
                cmd = [file_binary, "-bi", infile, "-m", magic_file_path]

            try:
                mime_result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
                mime = mime_result.stdout
            except Exception as e:
                return dict(output=None, mime=None, pattern=None, suffix=None, err=(" ".join(cmd), str(e)))

            if mime_result.returncode != 0:
                return dict(output=None, mime=None, pattern=None, suffix=None,
                            err=(" ".join(cmd), mime.strip()))

            # --- Extract Suffix safely ---
            index = infile.rfind('.') # Use rfind for accurate path extension matching
            if index == -1:
                suffix = b"" if isinstance(out_curr, bytes) else ""
            else:
                suffix = infile[index:]
                if isinstance(out_curr, bytes) and isinstance(suffix, str):
                    suffix = suffix.encode('utf-8')

            # Ensure data tracking types stay aligned (bytes comparison)
            if (out_curr == b"data\n" or out_curr == "data\n") and idx_curr == 0:
                buf = ""

            # Ensure everything going to the database is a decoded string, not bytes
            return dict(
                output=out_curr.decode('utf-8', errors='replace') if isinstance(out_curr, bytes) else out_curr,
                mime=mime.decode('utf-8', errors='replace') if isinstance(mime, bytes) else mime,
                pattern=buf.decode('utf-8', errors='replace') if isinstance(buf, bytes) else buf,
                suffix=suffix.decode('utf-8', errors='replace') if isinstance(suffix, bytes) else suffix
            )
        else:
            idx_curr = idx_left + (idx_rigt - idx_left) // 2

def is_compilation_supported(file_name="file", file_binary="file"):
    """Determine whether data from :py:func:`compile_patterns` is available."""
    file_binary_hash = hashlib.sha224(file_name.encode()).hexdigest()
    if os.system(file_binary + " /bin/sh -m .mgc_temp/" + file_binary_hash +
                 "/.find-magic.tmp.0.mgc > /dev/null") != 0:
        print('')
        print("This file version doesn't support compiled patterns "
              "=> they won't be used")
        return False

    print('Compiled patterns will be used')
    print('')
    return True
