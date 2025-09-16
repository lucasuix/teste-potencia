import os
import sys
import zipfile
from datetime import datetime

class PathManager:
    """A utility class to manage file paths within the application.

    This class provides static and class methods to handle file paths
    and file operations consistently across the application.

    Methods:
        is_pyinstaller_bundle(): Check if the application is running as a PyInstaller bundle.
        get_path(file_name, is_user_dir=False): Get the absolute path of a file, considering PyInstaller environment and user directories.

    """

    @staticmethod
    def is_pyinstaller_bundle():
        """Check if the application is running as a PyInstaller bundle."""
        return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")

    @staticmethod
    def get_path(file_name, is_user_dir=False):
        """Get the absolute path of a file, considering PyInstaller environment and user directories."""
        if is_user_dir:
            # Directly expand the user directory path (e.g., '~/Documents')
            return os.path.expanduser(file_name)
        else:
            # For application paths, especially relevant when running as a PyInstaller bundle
            base_path = getattr(
                sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__))
            )
            return os.path.join(base_path, file_name)

class CompileLogs:
    """A class to compile log files into a zip archive."""

    def __init__(self, log_dir="log", output_dir="~/Documents/Tecsci"):
        self.log_dir = log_dir
        self.output_dir = PathManager.get_path(output_dir, is_user_dir=True)
        self.log_files = []

    def find_log_files(self):
        """Find all .txt files in the log directory."""
        log_path = PathManager.get_path(self.log_dir)
        for root, dirs, files in os.walk(log_path):
            for file in files:
                if file == "temp.txt":
                    temp_file_path = os.path.join(root, file)
                    os.remove(temp_file_path)
                elif file.endswith(".txt") or file.endswith(".csv"):
                    self.log_files.append(os.path.join(root, file))

    def zip_logs(self):
        """Create a zip file containing all the found log files, and delete them after it's done"""
        if not self.log_files:
            print("No log files found to zip.")
            return

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        zip_file_name = f"{current_time}.zip"
        zip_file_path = os.path.join(self.output_dir, zip_file_name)

        with zipfile.ZipFile(zip_file_path, "w") as zipf:
            for log_file in self.log_files:
                zipf.write(log_file, arcname=os.path.basename(log_file))
        print(f"Logs have been zipped into {zip_file_path}")

        for log_file in self.log_files:
            os.remove(log_file)

    def run(self):
        """Execute the process to locate log files, compile them into a zip archive, and delete old logs."""
        self.find_log_files()
        self.zip_logs()


class Peripheral:
    def __init__(self,id, name, commands):
        """Initialize a new Peripheral instance."""
        self.id = id
        self.name = name
        self.commands = commands
        self.status = "--"


#Creating the peripherals objects.
peripherals_list = {
    "bateria"           : Peripheral(0, "Curto - Bateria", ["LIGBT"]),
    "dcdc"              : Peripheral(1, "Curto - DCDC", ["LIGDC"]),
    "teste1a"           : Peripheral(2, "Tensão DCDC/Load/StepUp", ["LIGDC"]),
    "teste1b"           : Peripheral(3, "Circ Carga Bateria", ["LIGCB"]),
    "bateria_isolada"   : Peripheral(4, "Bateria Isolada", ["LIGCB"]),
    "temp_alarm1"       : Peripheral(5, "Alarme Temp1", ["ACTP1"]),
    "temp_return1"      : Peripheral(6, "Retorno Temp1", ["ACTPA"]),
    "temp_alarm2"       : Peripheral(7, "Alarme Temp2", ["ACTP2"]),
    "temp_return2"      : Peripheral(8, "Retorno Temp2", ["ACTPA"]),
    "pwm"               : Peripheral(9, "Teste PWM", ["LIGBT"]),
    "pwm_pth"           : Peripheral(10, "PWM com ENPTH", ["LIGBT"]),
}

# Teste de Comunicação - Segunda seção
communication_test_list = {
    "inclinometro"      : Peripheral(11, "Inclinômetro", ["TCOM"]),
    "adc"               : Peripheral(12, "ADC", ["TCOM"]),
    "rak"               : Peripheral(13, "RAK", ["TCOM"]),
    "rtc"               : Peripheral(14, "RTC", ["TCOM"]),
    "serial_number"     : Peripheral(15, "Serial Number", ["TCOM"]),
    "eeprom"            : Peripheral(16, "EEPROM", ["TCOM"]),
    "ponte_h"           : Peripheral(17, "Ponte H", ["TCOM"]),
}

