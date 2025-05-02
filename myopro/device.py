from decimal import Decimal
from myopro.daq import DAQ
from myopro.log import Log
from myopro.stream import *
import json
import serial
import time

class Device:
    """
    Class that connects to and uses the Myopro device
    """
    def __init__(self, port, baudrate=115200, bytesize=serial.EIGHTBITS,
                 parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, 
                 timeout=None, xonxoff=False, rtscts=False, write_timeout=None,
                 dsrdtr=False, inter_byte_timeout=None, exclusive=None):
        """
        Inits and connects to device with specified values
        """
        # Parameters for serial connection (Internal use only)
        self.__port = port
        self.__baudrate = baudrate
        self.__bytesize = bytesize
        self.__parity = parity
        self.__stopbits = stopbits
        self.__timeout = timeout
        self.__xonxoff = xonxoff
        self.__rtscts = rtscts
        self.__dsrdtr = dsrdtr
        self.__write_timeout = write_timeout
        self.__dsrdtr = dsrdtr
        self.__inter_byte_timeout = inter_byte_timeout
        self.__exclusive = exclusive

        # Creates serial connection
        self.connection = serial.Serial(port=self.__port, baudrate=self.__baudrate,
                                        bytesize=self.__bytesize, parity= self.__parity,
                                        stopbits=self.__stopbits, timeout=self.__timeout, 
                                        xonxoff=self.__xonxoff, rtscts=self.__rtscts,
                                        dsrdtr=self.__dsrdtr ,write_timeout=self.__write_timeout,  
                                        inter_byte_timeout=self.__inter_byte_timeout,
                                        exclusive=self.__exclusive)
        time.sleep(1) # Give the device a second to power on without device will lock trying to read
                      # ahead of what is there

        # Open gain mapping json
        f = open("myopro/gain_mapping.json")
        self.gain_mapping = json.load(f)

        # Variables of device wrapper
        self.streaming = False
        self.log = None
        on_boot_dm_parameters = self.get_dual_mode_parameters() # Get & define dual mode parameters on boot
        self.daq_device = None
        # Dual mode parameters are needed on boot to be able to fill in when they are set if the user does
        # not want to set every parameter that is available
        self.dual_mode_type = on_boot_dm_parameters[0]
        self.e1_max = on_boot_dm_parameters[1]
        self.e2_max = on_boot_dm_parameters[2]
        self.effort_delta_threshold_biceps_or_close = on_boot_dm_parameters[3]
        self.effort_delta_threshold_triceps_or_open = on_boot_dm_parameters[4]
        self.constant_velocity = on_boot_dm_parameters[5]
        self.proportional_multiplier = on_boot_dm_parameters[6]
        self.sensitivity = on_boot_dm_parameters[7]
        self.curviness = on_boot_dm_parameters[8]
        self.low_range_rom_degree_threshold_to_enable_hold_position = on_boot_dm_parameters[9]
        self.high_range_rom_degree_threshold_to_enable_hold_position = on_boot_dm_parameters[10]
        self.hbridge_overheat_prevention_time_enabled = on_boot_dm_parameters[11]
        self.time_until_no_motor_command = on_boot_dm_parameters[12]
        self.battery_current_threshold = on_boot_dm_parameters[13]
        self.alarm_volume = on_boot_dm_parameters[14]
        self.__internal_dual_mode_parameters = on_boot_dm_parameters

        self.speed_trackbar = self.__map(float(self.proportional_multiplier), 0.25,3.25,1,20)

    def connect(self):
        """
        Connect to the device if the connection is not open.
        """
        if self.connection.is_open == False:
            self.connection.open()
        else:
            print('The connection is already open!')

    def disconnect(self):
        """
        Disconnect from the device if the connection is open.
        """
        if self.connection.is_open == True:
            self.connection.close()
        else:
            print('There is no connection open!')

    def stream_data(self, stream_time, log=True, command=None, command_interval:int=0, print_data:bool=False, directory:str=None,
                    print_time:bool=False, print_time_interval=0, use_daq=False, create_model=False, model_parameters=None, return_data=False):
        """
        Streams data to log. Runs for specified time or until keyboard interrupt.
        The amount of time for streaming is in seconds.
        None can be given as a stream time if it is it will run until there is a keyboard interrupt
        """
        if log:
            file = Log(directory)
            file.file.write(str(self.get_bicep_gain()) + ' ' + str(self.get_tricep_gain()) + '\n')
            file.file.write(str(self.get_dual_mode_parameters()).replace('[', '').replace(']', '').replace('\'', '') + '\n')
        self.get_dual_mode_parameters
        if stream_time:
            start_time = time.time()

        if command_interval or print_time:
            prev_sec = 0
        
        if create_model:
            if model_parameters == None:
                raise Exception("Model Parameters not specified.")
            else:
                model = Log(directory, name=file.name.replace('raw', 'model'))
                model.log.writerow(model_parameters)

        if return_data:
            to_return = []
            if create_model:
                stop = len(model_parameters)
            for i in range(11):
                if i == stop:
                    break
                to_return.append([])

        print_cooldown = 0
        command_cooldown = 0
        prev_sec = 0

        self.connection.write(b"$\x1b! 2 1\n")
        while time.time() - start_time < stream_time or stream_time == None:
            try:
                data = self.connection.readline().decode('UTF-8')
                data = process_data(data)
                data = validate_data(data)

                if data[0] != 'INVALID':
                    if use_daq and self.daq_device != None:
                        values = self.daq_device.read_values()
                        for value in values:
                            data.append(value)
                    else:
                        raise Exception("DAQ is not connected!")
                    if print_data:
                        print(",".join(data))
                    if log:
                        file.log.writerow(data)
                    if create_model:
                        model_data = compile_model_data(data, model_parameters)
                        model.log.writerow(model_data)
                    if return_data:
                        for i in range(len(to_return)):
                            if create_model:
                                to_return[i].append(model_data[i])
                            else:
                                to_return[i].append(data[i])
                    if print_time or command_interval:
                        if int(time.time() - start_time) > prev_sec:
                            prev_sec = int(time.time() - start_time)
                            if print_time and print_cooldown == 0:
                                print(int(prev_sec))
                                print_cooldown = print_time_interval
                            else:
                                print_cooldown -= 1
                            if command_cooldown == 0 and command != None:
                                command(self)
                                command_cooldown = command_interval
                            else:
                                command_cooldown -= 1
                        
            except KeyboardInterrupt:
                break

        self.connection.write(b"$\x1b! 2 0\n")
        if log:
            file.close_log()
        if create_model:
            model.close_log()
        if return_data:
            return to_return

    def get_mode(self) -> int:
        """
        Gets the mode of the device.
        """
        self.connection.write(b"$f\n")
        response = self.connection.readline().decode()
        while response[0:2] != '$f':
            response = self.connection.readline().decode()

        self.__clear_output_buffer()
        return int(response[5])

    def set_mode(self, mode):
        """
        Set the mode of the device. Input can be a str or int.
        0 - None, 1 - Bicep, 2 - Tricep, 3 - Dual\n
        Information from Myopro2 Bluetooth Communication Protocol
        """
        cmd = f"$0 {str(mode)}\n"
        self.connection.write(cmd.encode())
        self.__clear_output_buffer()

    def get_bicep_tricep_effort(self) -> tuple:
        """
        Get the bicep and tricep effort. 
        Format: (Bicep Effort, Tricep Effort)
        """
        data = self.get_single_bluetooth_string()
        return int(data[5]), int(data[4])

    def get_bicep_gain(self) -> float:
        """
        Get the bicep gain.
        """
        self.connection.write(b"$5 3\n")
        response = self.connection.readline().decode()
        while response[0:2] != '$5':
            response = self.connection.readline().decode()

        bicep_gain = int(response[5:7])
        self.__clear_output_buffer()

        self.connection.write(b"$m 1\n")
        response = self.connection.readline().decode()
        while response[0:2] != "$m":
            response = self.connection.readline().decode()
        
        bicep_boost = int(response[5:7])
        self.__clear_output_buffer()

        parameters = [bicep_gain, bicep_boost]
        gain = Decimal('0.2')

        while (self.gain_mapping[str(gain)] != parameters):
            gain += Decimal('0.2')

        return float(gain)

    def set_bicep_gain(self, gain:float) -> None:
        """
        Set the bicep gain. The values must be between 0.0 - 20.0 and must
        have an even decimal place.\n
           
        Valid decimal values: XX.2, XX.4, XX.6, XX.8
        """
        parameters = self.gain_mapping[str(gain)]

        cmd = f"$3 3 {parameters[0]}\n"
        self.connection.write(cmd.encode())
        self.__clear_output_buffer()

        cmd = f"$k 1 {parameters[1]}\n"
        self.connection.write(cmd.encode())
        self.__clear_output_buffer()

    def get_tricep_gain(self):
        """
        Get the tricep gain.
        """
        self.connection.write(b"$5 3\n")
        response = self.connection.readline().decode()
        while response[0:2] != '$5':
            response = self.connection.readline().decode()

        tricep_gain = int(response[7:])
        self.__clear_output_buffer()

        self.connection.write(b"$n 1\n")
        response = self.connection.readline().decode()
        while response[0:2] != "$n":
            response = self.connection.readline().decode()
        
        tricep_boost = int(response[5:7])
        self.__clear_output_buffer()

        parameters = [tricep_gain, tricep_boost]
        gain = Decimal('0.2')

        while (self.gain_mapping[str(gain)] != parameters):
            gain += Decimal('0.2')

        return float(gain)

    def set_tricep_gain(self, gain:float):
        """
        Set the bicep gain. The values must be between 0.0 - 20.0 and must
        have an even decimal place.\n
           
        Valid decimal values: XX.2, XX.4, XX.6, XX.8
        """
        parameters = self.gain_mapping[str(gain)]

        cmd = f"$4 3 {parameters[0]}\n"
        self.connection.write(cmd.encode())
        self.__clear_output_buffer()

        cmd = f"$l 1 {parameters[1]}\n"
        self.connection.write(cmd.encode())
        self.__clear_output_buffer()   

    def get_effort_threshold(self):
        """
        Gets and returns the bicep and tricep effort thresholds.
        """
        parameters = self.get_dual_mode_parameters()
        return parameters[3], parameters[4]

    def set_effort_threshold(self, et_bicep, et_tricep):
        """
        Set the bicep and tricep effort thresholds. If you only want to set one 
        set the one you don't want to set to None.
        """
        self.set_dual_mode_parameters(effort_delta_threshold_biceps=et_bicep, 
                                      effort_delta_threshold_triceps=et_tricep)

    def get_data_string(self):
        """
        Get a single event serial transmission string.
        """
        data = ['']
        self.connection.write(b"$\x1b! 2 1\n")

        while data[0] != 'E':
            data = self.connection.readline().decode('Ascii').strip().split(',')
            data = validate_data(data)            

        self.connection.write(b"$\x1b! 2 0\n")
        self.__clear_output_buffer()
        return data
    
    def start_streaming(self):
        self.connection.write("$\x1b! 2 1\n".encode("ascii"))
        self.connection.readline()
        self.connection.readline()

    def stop_streaming(self):
        self.connection.write(b"$\x1b! 2 0\n")
        self.__clear_output_buffer()
        
    def get_string_while_streaming(self):
        data = ['']
        while data[0] != 'E':
            data = self.connection.readline().decode('Ascii').strip().split(',')
            data = validate_data(data)
        return data

    def get_dual_mode_parameters(self):
        """
        Gets the 15 dual mode parameters are returns them in a list. 
        The order of values are below. See bluetooth protocol for more info
        on what each parameter is.
        
        0 - dual_mode_type\n
        1 - e1_max\n
        2 - e2_max\n
        3 - effort_delta_threshold_biceps_or_close\n
        4 - effort_delta_threshold_triceps_or_open\n
        5 - constant_velocity\n
        6 - proportional_multiplier\n
        7 - sensitivity\n
        8 - curviness\n
        9 - low_range_rom_degree_threshold_to_enable_hold_position\n
        10 - high_range_rom_degree_threshold_to_enable_hold_position\n
        11 - hbridge_overheat_prevention_time_enabled\n
        12 - time_until_no_motor_command\n
        13 - battery_current_threshold\n
        14 - alarm_volume\n
        15 - write_to_eeprom\n
        Information from Myopro2 Bluetooth Communication Protocol
        """
        self.connection.write(b'$\x1bz\n')

        response = self.connection.readline().decode()
        while response[0:5] != '$\x1bz 1':
            response = self.connection.readline().decode()

        parameters = []
        parameter = ''

        for i in range(6, len(response)):
            if response[i] not in ['$', '\x1b', 'z']:
                if response[i] == ' ' or response[i] == '\n':
                    parameters.append(parameter)
                    parameter = ''
                else:
                    parameter += response[i]

        self.__clear_output_buffer()
        return parameters

    def set_dual_mode_parameters(self, dual_mode_type=None, e1_max=None, e2_max=None,
                                 effort_delta_threshold_biceps=None, effort_delta_threshold_triceps=None,
                                 constant_velocity=None, proportional_multiplier=None, sensitivity=None,
                                 curviness=None, low_range_rom=None, high_range_rom=None,
                                 overheat_prevention=None, no_motor_command=None, 
                                 battery_current_threshold=None, alarm_volume=None, write_to_eeprom=1):
        """
        Set the dual mode parameters of the device. Parameter limits 
        listened below. See bluetooth protocol for more information.
    
        dual_mode_type (0-4)\n
        e1_max and e2_max (0-200)\n
        effort_delta_threshold_biceps_or_close
        and effort_delta_threshold_triceps_or_open (0-100)\n
        constant_velocity (0-100)\n
        proportional_multiplier (0-5)\n
        sensitivity (1-100)\n
        curviness (1-10)\n
        low_range_rom_degree_threshold_to_enable_hold_position (0-100)\n
        high_range_rom_degree_threshold_to_enable_hold_position (0-100)\n
        hbridge_overheat_prevention_time_enabled (0-1)\n
        time_until_no_motor_command (0-3600\n
        battery_current_threshold (0-1500)\n
        alarm_volume (0-50)\n
        write_to_eeprom (0-1)\n
    
        Information from Myopro2 Bluetooth Communication Protocol
        """
        parameters = locals()
        i = 0
        cmd = '$\x1by'

        for key in parameters.keys():
            if key != 'self':
                cmd += ' '
                if parameters[key] == None:
                    parameters[key] = self.__internal_dual_mode_parameters[i]
                else:
                    self.__internal_dual_mode_parameters[i] = parameters[key]
                cmd += str(parameters[key])
                i += 1
                if(i > len(self.__internal_dual_mode_parameters) - 1):
                    cmd += ' '
                    break
                
        cmd += str(parameters['write_to_eeprom']) + '\n'
        self.__update_internal_dual_mode_parameters()
        self.connection.write(cmd.encode())
        self.__clear_output_buffer()

    def run_command(self, input:str) -> str:
        """
        Run any command from the bluetooth protocal and have the response returned.
        You do not need to input the $ or new line just the command and values.\n
        Example call: run_command("g") - This call would get the battery.
        """
        cmd = f'${input}\n' 
        self.connection.write(cmd.encode())
        
        result = ''
        response = self.connection.readline().decode('UTF-8')
        while response != "$OK\n":
            result += response
            response = self.connection.readline().decode('UTF-8')

        return result

    def connect_daq(self, channels) -> None:
        """
        Initalize a daq device to be used along side the Myopro.
        See DAQ class documentation for information on channels parameter.
        """
        self.daq_device = DAQ(channels)

    def __update_internal_dual_mode_parameters(self):
        """
        Updates the dual mode parameter attributes of the class
        """
        self.dual_mode_type = self.__internal_dual_mode_parameters[0]
        self.e1_max = self.__internal_dual_mode_parameters[1]
        self.e2_max = self.__internal_dual_mode_parameters[2]
        self.effort_delta_threshold_biceps_or_close = self.__internal_dual_mode_parameters[3]
        self.effort_delta_threshold_triceps_or_open = self.__internal_dual_mode_parameters[4]
        self.constant_velocity = self.__internal_dual_mode_parameters[5]
        self.proportional_multiplier = self.__internal_dual_mode_parameters[6]
        self.sensitivity = self.__internal_dual_mode_parameters[7]
        self.curviness = self.__internal_dual_mode_parameters[8]
        self.low_range_rom_degree_threshold_to_enable_hold_position = self.__internal_dual_mode_parameters[9]
        self.high_range_rom_degree_threshold_to_enable_hold_position = self.__internal_dual_mode_parameters[10]
        self.hbridge_overheat_prevention_time_enabled = self.__internal_dual_mode_parameters[11]
        self.time_until_no_motor_command = self.__internal_dual_mode_parameters[12]
        self.battery_current_threshold = self.__internal_dual_mode_parameters[13]
        self.alarm_volume = self.__internal_dual_mode_parameters[14]
        self.speed_trackbar = self.__map(float(self.proportional_multiplier), 0.25,3.25,1,20)

    def __clear_output_buffer(self):
        """
        Clears the output buffer until the next '$OK\\n' is found.
        """
        response = self.connection.readline().decode('UTF-8')
        while response != "$OK\n":
            response = self.connection.readline().decode('UTF-8')

    def __map(self, value,a,b,c,d):
        #a= value min , b = value max , c = out min , d = out max
        #this function liniarly maps a data from a range to another range
        # Written by Amin
        return ((value-a)/(b-a))*(d-c) +c
