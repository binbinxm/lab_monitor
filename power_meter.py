import serial
import binascii
ser = serial.Serial("/dev/ttyUSB0",2400,parity=serial.PARITY_EVEN,timeout=2)  
print(ser.isOpen())

cmd_voltage = b'\xFE\xFE\xFE\xFE\x68\x09\x66\x00\x04\x08\x19\x68\x11\x04\x33\x34\x34\x35\x49\x16'
cmd_current = b'\xFE\xFE\xFE\xFE\x68\x09\x66\x00\x04\x08\x19\x68\x11\x04\x33\x34\x35\x35\x4A\x16'
cmd_power   = b'\xFE\xFE\xFE\xFE\x68\x09\x66\x00\x04\x08\x19\x68\x11\x04\x33\x33\x36\x35\x4A\x16'
ser.write((cmd_voltage))
data = (ser.readline())
val = binascii.b2a_hex(data)[-16:-4]
vol = '%02x'%(int('0x' + val[-2:].decode('ascii'), 16)-0x33) + '%02x'%(int('0x' + val[-4:-2].decode('ascii'), 16)-0x33)
vol = vol[0:3] + '.' + vol[-1] + 'V'
print('voltage: ', vol)

ser.write((cmd_current))
data = (ser.readline())
print(data)
val = binascii.b2a_hex(data)[-18:-4]
vol = '%02x'%(int('0x' + val[-2:].decode('ascii'), 16)-0x33) + '%02x'%(int('0x' + val[-4:-2].decode('ascii'), 16)-0x33)
vol = vol[0:3] + '.' + vol[-1] + 'A'
print('current: ',vol)

ser.write((cmd_power))
data = (ser.readline())
print(data)
val = binascii.b2a_hex(data)[-18:-4]
print(val)
vol = '%02x'%(int('0x' + val[-2:].decode('ascii'), 16)-0x33) + '%02x'%(int('0x' + val[-4:-2].decode('ascii'), 16)-0x33) + '%02x'%(int('0x' + val[-6:-4].decode('ascii'), 16)-0x33)
vol = vol[0:5] + '.' + vol[-1] + 'W'
print('power:   ', vol)


ser.close()
