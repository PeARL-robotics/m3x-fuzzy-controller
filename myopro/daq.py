#from __future__ import absolute_import, division, print_function
from myopro.console_examples_util import config_first_detected_device
from builtins import *
from mcculw import ul
from mcculw.device_info import DaqDeviceInfo

class DAQ:

    """Class to handle process related to a daq device. 
       When initializing the class the channels parameter specifies which 
       channels the connection will access.\n
       For example if you wanted to access channels 0 and 1 you would have the parameter be
       (0, 1)."""

    def __init__(self, channels):
        dev_id_list = []
        self.board_num = 0
        config_first_detected_device(self.board_num, dev_id_list)

        self.daq_dev_info = DaqDeviceInfo(self.board_num)
        if not self.daq_dev_info.supports_analog_input:
            raise Exception('Error: The DAQ device does not support analog input.')
        
        self.ai_info = self.daq_dev_info.get_ai_info()
        self.ai_range = self.ai_info.supported_ranges[0]
        self.channels = channels
        
    def read_values(self, to_eng_units=True):
        """
        Read data from the DAQ device using the channels given on initalization.
        """
        data = []
        for channel in self.channels:
            value = ul.a_in(self.board_num, channel, self.ai_range)
            if to_eng_units:
                value = ul.to_eng_units(self.board_num, self.ai_range, value)
            data.append(value)
        return data

    def disconnect(self):
        """
        Disconnect from the DAQ device.
        """
        ul.release_daq_device(self.board_num)
