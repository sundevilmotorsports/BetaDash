

class SerialHandler:
    def __init__(self, serial_port, baudrate):
        self.serial_port = serial_port
        self.baudrate = baudrate
        self.serial = serial.Serial(self.serial_port, self.baudrate)
        self.data = {'x': [], 'y': []}



    