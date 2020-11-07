import time
import serial
import binascii
import logging
import csv
from fastapi import FastAPI, Request
from typing import Optional

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
    if(len(data) != 23): return False

    logging.debug('received message: %s'%binascii.b2a_hex(data))
    val = binascii.b2a_hex(data)[-18:-4]
    vol = '%02x'%(int('0x' + val[-2:].decode('ascii'), 16)-0x33) + '%02x'%(int('0x' + val[-4:-2].decode('ascii'), 16)-0x33) + '%02x'%(int('0x' + val[-6:-4].decode('ascii'), 16)-0x33)
    vol = vol[0:5] + '.' + vol[-1]
    return float(vol)


def get_power_dlt645(addr, port):
    cmd_power = encode_dlt645(addr, '11', COMMAND_POWER)
    ser = serial.Serial(port,2400,parity=serial.PARITY_EVEN,timeout=0.3)  
    if(not ser.isOpen()):
        logging.critical('cannot open serial port %s'%port)
        return False

    logging.debug('send command: %s'%binascii.b2a_hex(cmd_power))
    ser.write((cmd_power))
    data = (ser.readline())
    val = decode_dlt645(data)

    ser.close()
    return val


def load_from_csv(file_name): #integrity check? TBD
    reader = csv.reader(open(file_name, 'r'))
    d = {}
    for row in reader:
        ip, addr, port = row
        d[ip] = {'addr': addr, 'port':port, 'status':False}
        logging.debug('load from %s - %s: %s'%(file_name, ip, d[ip]))
    
    return d


def check_meter(ip):
    if(get_power_dlt645(meters[ip]['addr'], meters[ip]['port'])):
        logging.info('check alive - %s, %s, pass.'%(ip,meters[ip]['addr']))
        return True
    else:
        logging.error('check alive - %s, %s, fail.'%(ip,meters[ip]['addr']))
        return False


COMMAND_HEADER = 'fefefefe'
COMMAND_POWER = '33333635'

# load meters
meters = load_from_csv('meter_list.csv')

# check meters
for ip in meters.keys():
    if(check_meter(ip)):    meters[ip]['status'] = True


app = FastAPI()


@app.get("/api/v1/power")
def get_power(request: Request, ip: Optional[str] = None):
    ts = time.time()
    if ip == None:
        print('ip == None')
        ip = request.client.host
    d = {"elapse":-1,"error":True,"ipaddr": ip,"msg":"ip not found","power":-1,"time":int(ts),"version":"1.0"}
    if(ip in meters.keys()):
        d['error'] = False
        d['ipaddr'] = ip
        d['msg'] = 'meter offline'
        meters[ip]['status'] = False
        power = get_power_dlt645(meters[ip]['addr'], meters[ip]['port'])
        if power:
            d['msg'] = 'success'
            d['power'] = int(power)
            meters[ip]['status'] = True
            logging.info('read meter - %s, %s, %dW'%(ip, meters[ip]['addr'], power))

    d['elapse'] = round(time.time() - ts, 3)
    return d


@app.get("/api/v1/status")
def get_status():
    return meters

