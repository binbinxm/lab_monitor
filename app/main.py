import serial
import binascii
import logging
from fastapi import FastAPI, Request



def encode_dlt645(addr, ctrl, data):
    addr = addr[10:12] + addr[8:10] + addr[6:8] + addr[4:6] + addr[2:4] + addr[0:2]
    data = bytearray.fromhex(data)
    command = bytearray.fromhex('68') + bytearray.fromhex(addr) + bytearray.fromhex('68') + bytearray.fromhex(ctrl) + bytearray.fromhex(str('%02d'%len(data))) + data
    
    # caculate cs
    cs = 0
    for i in range(0,len(command)):
        cs += command[i]
    cs = cs % 256
    
    # add header
    command = bytearray.fromhex(COMMAND_HEADER) + command

    # add cs
    command += bytearray([cs])

    # add tail
    command += bytearray.fromhex('16')

    return bytes(command)


def decode_dlt645(data):
    logging.debug('received message: %s'%binascii.b2a_hex(data))
    val = binascii.b2a_hex(data)[-18:-4]
    vol = '%02x'%(int('0x' + val[-2:].decode('ascii'), 16)-0x33) + '%02x'%(int('0x' + val[-4:-2].decode('ascii'), 16)-0x33) + '%02x'%(int('0x' + val[-6:-4].decode('ascii'), 16)-0x33)
    vol = vol[0:5] + '.' + vol[-1] + 'W'
    return vol

def get_power_dlt645(addr):

    cmd_power = encode_dlt645(addr, '11', COMMAND_POWER)
    logging.debug('send command: %s'%binascii.b2a_hex(cmd_power))

    ser = serial.Serial("/dev/ttyUSB0",2400,parity=serial.PARITY_EVEN,timeout=0.3)  
    logging.debug('serial port open? %s'%str(ser.isOpen()))

    ser.write((cmd_power))
    data = (ser.readline())
    val = decode_dlt645(data)

    ser.close()
    return val


COMMAND_HEADER = 'fefefefe'
COMMAND_POWER = '33333635'


app = FastAPI()

@app.get("/")
def read_root(request: Request):
    return {"Hello": get_power_dlt645('200906008376'), 'id': request.client.host}

