import csv
from datetime import datetime
import os

class Log:

    """Class that represents a log to be used to log data from the device.
       The directory parameter can only be a single directory.
       Example: logs is valid but logs/test_1 is not valid."""

    def __init__(self, directory, name=None):
        self.directory = directory
        if name == None:
            self.name = self.__generate_log_name()
        else:
            self.name = name
        self.file = self.__create_file()
        self.log = self.__create_log()

    def close_log(self) -> None:

        """Close the log when its done being used."""

        self.file.close()
    
    def __create_file(self):

        """Creates the csv file to be used."""

        file = open(self.name, "w", newline='')
        return file

    def __create_log(self):

        """Creates a csv writer object."""

        log = csv.writer(self.file)
        return log

    def __create_log_directory(self) -> None:

        """Creates the directory for the logs to be stored."""

        os.system(f'mkdir {self.directory}')

    def __generate_log_name(self) -> str:

        """Generates a log name based on the current date and time."""

        date = list(str(datetime.now()))

        for i in range(len(date)):
            if date[i] == " ":
                date[i] = "_"
            if date[i] == ":":
                date[i] = "."

        if self.directory != None:
            self.__create_log_directory()
            name = f"{self.directory}/" + "raw_" +"".join(date) + ".csv" 
        else:
            name = "raw_" + "".join(date) + ".csv"
            
        return name
