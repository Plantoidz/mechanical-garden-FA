import serial
import keyboard
import time
import os, signal
import random
import regex_spm


def setup_serial(PORT="/dev/ttyUSB0", baud_rate=9600):

    try:

        if PORT is None: raise Exception('No Serial Port Provided!')

        # configure the serial connections (the parameters differs on the device you are connecting to)
        ser = serial.Serial(port=PORT, baudrate=baud_rate)

        print("Serial port " + PORT + " opened  Baudrate " + str(baud_rate))

        return ser
        #waitForArduino()

    except serial.SerialException:

        raise Exception('Cannot access provided serial port!')


def send_to_arduino(ser, string_to_send):

    if ser is None:
        raise Exception('Serial cannot be None!')

    start_marker = '<'
    end_marker = '>'

    string_with_markers = start_marker + string_to_send + end_marker

    print('serial string is:', string_with_markers)

    ser.write(string_with_markers.encode('utf-8')) # encode needed for Python3


data_started = False
data_buf = ""
message_complete = False

def check_received_arduino_signal(ser):

    if ser is None:
        raise Exception('Serial cannot be None!')

    start_marker = '<'
    end_marker = '>'
    global data_started
    global data_buf
    global message_complete

    if ser.inWaiting() > 0 and message_complete == False:

        # decode needed for Python3 
        x = ser.read().decode("utf-8") # ser.readline().decode('utf-8').strip()


        print("["+x+"]")


        if data_started == True:

            if x != end_marker:
                data_buf = data_buf + x
            else:
                data_started = False
                message_complete = True

            print("databuf = " , data_buf); 

        elif x == start_marker:

            data_buf = ''
            data_started = True

        print("["+x+"] == ["+ start_marker+"] == ",  x == start_marker)


    if message_complete == True:

        message_complete = False
        return data_buf

    else:

        return "XXX" 


#==================

def wait_for_arduino(ser):

    # wait until the Arduino sends 'Arduino is ready' - allows time for Arduino reset
    # it also ensures that any bytes left over from a previous message are discarded

    print("Waiting for Arduino to reset")

    msg = ""

#    start_signal = "<>".encode()
#    serialPort.read_until(start_signal)

    while msg.find("Arduino is ready") == -1:


        msg = check_received_arduino_signal(ser)

        if not (msg == 'XXX'):

            print("[",msg,"]")

    print("ARDUINO IS READY")

