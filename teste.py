import serial
import time

def aguardar_ack(ser, timeout=1.0):
    """
    Aguarda até receber 'RXACKOK' ou até timeout.
    
    Retorna:
    - Tuple: (status_bool, resposta_string)
    """
    inicio = time.time()
    buffer = ""

    while time.time() - inicio < timeout:
        if ser.in_waiting:
            buffer += ser.read(ser.in_waiting).decode(errors='ignore')
            if "ACKOK" in buffer:
                return True, buffer.strip()
        else:
            time.sleep(0.005)

    return False, buffer.strip()

ser = serial.Serial(
        port='COM5',
        baudrate=115200,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        timeout=2,
        write_timeout=2,
        rtscts=False,    # Desabilita hardware flow control
        dsrdtr=False,    # Desabilita DSR/DTR
        xonxoff=False    # Desabilita software flow control
        )  


# msg = f"$cTime,{int(time.time())}"
# msg = "$cSerialNumber,0000000000001"
ser.timeout = 20
ser.write(b"DESBT")
time.sleep(2)
ser.write(b"LIGBT")
time.sleep(2)
ser.reset_input_buffer()
ser.write(b"$cTime,1757338736")
response = ser.read_until().decode()
print(response)


