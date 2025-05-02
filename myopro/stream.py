def process_data(data:str) -> list:
    """
    Process incoming data and turn it into a list.
    """
    data = data.split(',')
    for i in range(len(data)):
        if '\n' in data[i]:
            data[i] = data[i].replace('\n', '')

    return data

def validate_data(data:list) -> list:
    """
    Validate incoming data. Fixes an issue with the time output of the
    serial transmition string. If data is not valid will return ['INVALID'].
    """
    if data[0] not in ['E', 'H']:
        return ['INVALID']

    separator = str(data[1]).index('.')
    if len(str(data[1])) != separator + 10:
        fix = list(data[1]) # use .index for string and then do the stuff
        while len(fix) != separator + 10:
            fix.insert(separator + 1, "0")
        data[1] = "".join(fix)

    return data

def compile_model_data(data:list, parameters:list) -> list:
    """
    Returns a filtered list of data based on the parameters wanted.
    """
    parameter_index = {"device_type": 0, "time": 1, "tricep_emgs": 2, "bicep_emgs": 3,
                  "tricep_effort": 4, "bicep_effort": 5, "joint_position": 6,
                  "battery_current": 7, "sync_bit": 8, "daq_0": 9, "daq_1": 10}
    
    model_data = []
    for parameter in parameters:
        model_data.append(data[parameter_index[parameter]])
    return model_data

def print_data(data:list) -> None:
    """
    Print the data to the screen
    """
    print(",".join(data))