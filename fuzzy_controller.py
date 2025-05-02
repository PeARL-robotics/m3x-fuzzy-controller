from decimal import Decimal
from myopro.log import Log
import fuzzylab as fl
import winsound
import myopro
import time

# Set Up Fuzzy Systems
nde_fis = fl.readfis('new_dom_eff')
noe_fis = fl.readfis('new_opp_eff')

# Constants
TEST_TIME = 30.0
GAIN_MAX = 20.0
GAIN_MIN = 1
EFFORT_THRESHOLD_MAX = 65
EFFORT_THRESHOLD_MIN = 10
TRACKING = ['time', 'et_b', 'et_t', 'gb', 'gt', 'e_b', 'e_t', 'pose', 'daq_0', 'daq_1', 'intention']

# Pick choices in starting parameters and controller state
choice = input('Pick a starting point: (sen, nor, res)')
if choice == 'sen': 
    et_b = 10
    et_t = 10
elif choice == 'res':
    et_b = 45
    et_t = 45
elif choice == 'nor':
    et_b = 25
    et_t = 25
    
choice = input("Use the fuzzy controllers: (y, n)")
if choice == 'y': use_controller = True
elif choice == 'n': use_controller = False
    
gb = Decimal('10.0')#(str(random.randint(1, 20)) + '.0') # Gain for Biceps
gt = Decimal('10.0')#(str(random.randint(1, 20)) + '.0') # Gain for Triceps
print(et_b, et_t, gb, gt)
print(f"Controller Active: {use_controller}")

# Init Myopro device
ser = myopro.Device('com5') 
ser.set_mode(3) # set to dual
ser.set_dual_mode_parameters(dual_mode_type=3) # set to proportional
ser.connect_daq([0,1])

ser.set_effort_threshold(et_b, et_t)
ser.set_bicep_gain(gb)
ser.set_tricep_gain(gt)

# Init file to keep track of data
file = Log('improvement_tests/original_moved_sensor')
file.log.writerow(TRACKING)
file.log.writerow(('START', et_b, et_t, gb, gt, 0, 0, 0, 0.0, 0.0, 'no'))

raw = Log('improvement_tests/original_moved_sensor/raw')
raw.log.writerow((et_b, et_t, use_controller))

# Tuning Loop (For now program will loop for around 30 seconds and then ask
# if it should continue)
start_time = time.time()
data = ser.get_data_string()
prev_pose = int(data[6])
intention = 'no'
winsound.MessageBeep()
while time.time() - start_time < TEST_TIME:
    # Get data for iteration
    data = ser.get_data_string()
    e_b = abs(int(data[5]))
    e_t = abs(int(data[4]))
    net_e = e_b - e_t
    if len(data) == 9:
        pose = int(data[6])
    else:
        pose = int(data[14])
    daq_0, daq_1 = ser.daq_device.read_values()

    # Determine intention and whether 
    no_check = [prev_pose + i for i in range(-1, 1)]

    if pose > prev_pose: #and e_b >= 25:
        intention = 'bicep'
    elif pose < prev_pose:# and e_t >= 25:
        intention = 'tricep'
    elif pose == prev_pose: #and e_b < 25 and e_t < 25:
        intention = 'no'

    if use_controller:
        if intention == 'bicep':
            gb += round(fl.evalfis(nde_fis, [float(gb), 1]))
            gt += round(fl.evalfis(noe_fis, [float(net_e), 1]))
        elif intention == 'tricep':
            gt += round(fl.evalfis(nde_fis, [float(gt), 1]))
            gb += round(fl.evalfis(noe_fis, [float(-net_e), 1]))
        elif intention == 'no':
            gb += round(fl.evalfis(nde_fis, [float(gb), 0]))
            gt += round(fl.evalfis(noe_fis, [float(net_e), 0]))

        if gb > GAIN_MAX:
            gb = GAIN_MAX
        elif gb < GAIN_MIN:
            gb = GAIN_MIN

        if gt > GAIN_MAX:
            gt = GAIN_MAX
        elif gt < GAIN_MIN:
            gt = GAIN_MIN

        #ser.set_effort_threshold(et_b, et_t)
        ser.set_bicep_gain(float(gb))
        ser.set_tricep_gain(float(gt))
        #print(gb, gt)
    
    print(f'{time.time() - start_time} intention = {intention}, pose={pose}, gb = {gb}, gt = {gt}, daq_0 = {daq_0}, daq_1 = {daq_1}')
    prev_pose = pose
    file.log.writerow([data[1], et_b, et_t, gb, gt, e_b, e_t, pose, daq_0, daq_1, intention])
    raw.log.writerow(data) # Raw device data just in case something goes wrong.

ser.daq_device.disconnect()
ser.disconnect()
file.close_log()
raw.close_log()
winsound.MessageBeep()