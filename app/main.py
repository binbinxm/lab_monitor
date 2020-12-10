import time
import serial
import binascii
import logging
import csv
from fastapi import FastAPI, Request
from typing import Optional
import threading
from multiprocessing import Lock


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
    if(len(data) != 23):
        logging.error('received unknown message')
        return [False, 0]

    val = binascii.b2a_hex(data)[-18:-4]
    vol = '%02x'%(int('0x' + val[-2:].decode('ascii'), 16)-0x33) + '%02x'%(int('0x' + val[-4:-2].decode('ascii'), 16)-0x33) + '%02x'%(int('0x' + val[-6:-4].decode('ascii'), 16)-0x33)
    vol = vol[0:5] + '.' + vol[-1]
    return [True, float(vol)]


def get_power_dlt645(ip):
    global lock
    global meters

    addr = meters[ip]['addr']
    port = meters[ip]['port']
    cmd_power = encode_dlt645(addr, '11', COMMAND_POWER)

    lock.acquire()
    time.sleep(0.1)
    ser = serial.Serial(port,2400,parity=serial.PARITY_EVEN,timeout=0.5)  
    if(not ser.isOpen()):
        logging.critical('cannot open serial port %s'%port)
        return False

    logging.debug('send command: %s'%binascii.b2a_hex(cmd_power))
    ser.write((cmd_power))
    data = (ser.readline())

    ser.close()
    lock.release()
    
    power = decode_dlt645(data)
    if(power[0]):
        power = int(power[1])
        logging.info('read meter - %s, %s, %sW.'%(ip,meters[ip]['addr'],power))
        meters[ip]['power'] = power
        meters[ip]['status'] = True
        return True
    else:
        logging.error('read meter - %s, %s, fail.'%(ip,meters[ip]['addr']))
        meters[ip]['power'] = -1
        meters[ip]['status'] = False
        return False


def load_from_csv(file_name): #integrity check? TBD
    reader = csv.reader(open(file_name, 'r'))
    d = {}
    for row in reader:
        ip, addr, port = row
        d[ip] = {'addr': addr, \
                'port':port, \
                'status':False, \
                'power': -1, \
                'time': -1}
        logging.debug('load from %s - %s: %s'%(file_name, ip, d[ip]))
    
    return d


def meters_loop(delay_time):
    while(True):
        for ip in meters.keys():
            time.sleep(delay_time)
            get_power_dlt645(ip)
        logging.info('meters loop - done')
                
     
COMMAND_HEADER = 'fefefefe'
COMMAND_POWER = '33333635'

lock = Lock()
#lock = Request.environ['HTTP_FLASK_LOCK']

# load meters
meters = load_from_csv('meter_list.csv')

# check meters
for ip in meters.keys():
    get_power_dlt645(ip)


t = threading.Thread(target=meters_loop, args=(5,), daemon=True)
#t.start()

app = FastAPI()


@app.get("/api/v1/power")
def get_power(request: Request, ip: Optional[str] = None):
    ts = time.time()
    if ip == None:
        ip = request.client.host
    d = {"elapse":-1,"error":True,"ipaddr": ip,"msg":"ip not found","power":-1,"time":int(ts),"version":"1.0"}
    if(ip in meters.keys()):
        d['error'] = True
        d['msg'] = 'meter offline'
        get_power_dlt645(ip)
        if(meters[ip]['status']):
            d['error'] = False
            d['msg'] = 'success'
            d['power'] = meters[ip]['power']

    d['elapse'] = round(time.time() - ts, 3)
    return d


@app.get("/api/v1/power_cached")
def get_power_cached(request: Request, ip: Optional[str] = None):
    ts = time.time()
    if ip == None:
        ip = request.client.host
    d = {"elapse":-1,"error":True,"ipaddr": ip,"msg":"ip not found","power":-1,"time":int(ts),"version":"1.0"}
    if(ip in meters.keys()):
        d['error'] = True
        d['msg'] = 'meter offline'
        #get_power_dlt645(ip)
        if(meters[ip]['status']):
            d['error'] = False
            d['msg'] = 'success'
            d['power'] = meters[ip]['power']

    d['elapse'] = round(time.time() - ts, 3)
    return d


@app.get("/api/v1/status")
def get_status():
    return meters

