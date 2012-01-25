import os
import sys
import errno
from subprocess import Popen, PIPE
import pickle
import mimetypes
import difflib
from pyfile import *

mimetypes.init()

metadata = get_simple_metadata(sys.argv[1])
stored_metadata = get_stored_metadata(sys.argv[1])

if is_regression(stored_metadata, metadata):
	sys.exit(1)




