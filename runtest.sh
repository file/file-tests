#!/bin/sh

# Copyright (c) 2006 Red Hat, Inc. All rights reserved. This copyrighted material 
# is made available to anyone wishing to use, modify, copy, or
# redistribute it subject to the terms and conditions of the GNU General
# Public License v.2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Author: <Your Name> 

if [ -f /usr/bin/rhts-environment.sh ]; then
	. /usr/bin/rhts-environment.sh
	. /usr/lib/beakerlib/beakerlib.sh
else
rlJournalStart() {
}
rlPhaseStartSetup() {
}
rlAssertRpm() {
}
rlRun() {
    "$@"
}
rlServiceStop() {
}
rlPhaseEnd() {
}
rlPhaseStartTest() {
}
rlPhaseStartCleanup() {
}
rlServiceRestore() {
}
rlJournalPrintText() {
}
rlJournalEnd() {
}
fi

PACKAGE="file"
SLEEP_TIME="1234567890123456789012345678901234567890123456789012345678"

rlJournalStart
    rlPhaseStartSetup
        rlAssertRpm ${PACKAGE}
#        rlRun "ulimit -c unlimited"
#        rlServiceStop abrtd
    rlPhaseEnd

    rlPhaseStartTest
# this test tests one file at time
	for f in $(find db -name '*.pickle' -type f); do  
	    rlRun python test-file.py "${f%.pickle}"
	done
# this tests all files in 4 threads and is much more faster
#	rlRun "python fast-regression-test.py"
    rlPhaseEnd

    rlPhaseStartCleanup
#        rlRun "rm -f core.*"
#        rlServiceRestore abrtd
#        rlRun "ulimit -c 0"
    rlPhaseEnd
rlJournalPrintText
rlJournalEnd
