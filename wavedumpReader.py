# WaveDumpReader: Read data produced by CAEN digitizers using the WaveDump program
#  Copyright (C) 2017 T.J. Langford - Yale University thomas.langford@yale.edu
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from numpy import fromfile, dtype, array
from os import path
import matplotlib.pylab as plt
import numpy as np

# =============================================
# ============= Data File Class ===============
# =============================================


class DataFile:
    def __init__(self, fileName, is742=False):
        """
        Initializes the dataFile instance to include the fileName, access time,
        and the number of boards in the file. Also opens the file for reading.

        The file must have been collected with the OUTPUT_FILE_HEADER option
        set to YES. Otherwise, the reader will fail.
        """
        self.fileName = path.abspath(fileName)
        self.file = open(self.fileName, 'rb')
        self.recordLen = 0
        self.oldTimeTag = 0.
        self.timeTagRollover = 0
        self.boardId = 0
        self.is742 = is742

    def getNextTrigger(self):

        """
        This function returns  the next trigger from the dataFile. It reads WaveDump's 6 long-word header into i0-i5,
        unpacks them, and then reads the next event. It returns a RawTrigger object, which includes the fileName,
        location in the file, and the trace as a numpy array.
        """

        try:
            if self.is742:
                # Read the 8 long-words of the event header
                i0, i1, i2, i3, i4, i5, i6, i7 = fromfile(self.file, dtype='I', count=8)
            else:
                # Read the 6 long-words of the event header
                i0, i1, i2, i3, i4, i5 = fromfile(self.file, dtype='I', count=6)
        except ValueError:
            return None

        if self.is742:
            eventSize = (i0-32)//4
        else:
            eventSize = (i0 - 24) // 2

        self.boardId = i1

        # Instantize a RawTrigger object
        trigger = RawTrigger()
        # Fill the file position
        trigger.filePos = self.file.tell()

        trigger.pattern = i2
        trigger.channel = i3
        trigger.eventCounter = i4
        trigger.triggerTimeTag = i5


        if trigger.triggerTimeTag < self.oldTimeTag:
            self.timeTagRollover += 1
            self.oldTimeTag = float(i5)
        else:
            self.oldTimeTag = float(i5)

        # correcting triggerTimeTag for rollover
        if self.is742:
            # GROUP TRIGGER TIME TAG records the Trigger arrival time into a 30‐bit number (steps of 8.5 ns). This is
            # the physical trigger information of the event.
            trigger.triggerTimeTag += self.timeTagRollover*(2**30)
        else:
            trigger.triggerTimeTag += self.timeTagRollover*(2**31)

        # convert from ticks to us since the beginning of the file
        if self.is742:
            # For 742 Fast trigger, the time clock is 117.1875 MHz
            trigger.triggerTime = trigger.triggerTimeTag * 8.533333333e-3
        else:
            # For 751, the clock is 125 MHz, which is 8 ns for each point, and the unit of trigger time is us, so the count
            # should be times 8 ns to get the true time in us
            trigger.triggerTime = trigger.triggerTimeTag * 8e-3

        if self.is742:
            trigger.DC_offset = i6
            trigger.Start_Index_Cell = i7

        if not self.is742:
            # create a data-type of unsigned 16bit integers with the correct ordering
            dt = dtype('<H')

            # Use numpy's fromfile to read binary data and convert into a numpy array all at once
            trigger.trace = fromfile(self.file, dtype=dt, count=eventSize)
        else:
            dt = dtype(np.float32)
            trigger.trace = fromfile(self.file, dtype=dt, count=eventSize)

        return trigger

    def close(self):
        """
        Close the open data file. Helpful when doing on-the-fly testing
        """
        self.file.close()


# =============================================
# ============ Raw Trigger Class ==============
# =============================================


class RawTrigger:
    def __init__(self):
        """
        This is a class to contain a raw trigger from the .dat file. This is before any processing is done. It will
        contain the raw trace, as well as the fileName of the .dat file and the location of this
        trigger in the raw data.
        """
        self.pattern = 0
        self.channel = 0
        self.eventCounter = 0
        self.triggerTimeTag = 0
        self.triggerTime = 0

        # Only for 742
        self.DC_offset = 0
        self.Start_Index_Cell = 0

        self.trace = array([])
        self.filePos = 0

    def display(self):

        """
        A method to display the recorded trace in the RawTrigger object
        """

        fig = plt.figure()
        ax = fig.add_subplot(111)

        plt.plot(self.trace, label="Channel {}".format(self.channel))
        ax.legend(loc=0)

        # place a text box in upper left in axes coords with details of event
        textstr = 'File Position: {}\nTrigger Time (us): {}\nEvent Counter: {}' \
            .format(self.filePos, self.triggerTime, self.eventCounter)

        ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=10,
                verticalalignment='top', bbox=dict(facecolor='white', alpha=0.7))

        ymin, ymax = plt.ylim()

        plt.ylim(ymax=ymax + (ymax - ymin) * .25)

        plt.xlabel('Samples')
        plt.ylabel('Channel')
        plt.grid()

