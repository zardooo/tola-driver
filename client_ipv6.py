import socket
import time

mysock = socket.socket(socket.AF_INET6,socket.SOCK_STREAM)
#mysock.connect(("2001:470:4c22:ae86:babe:41:10b9:6b2e",65420))
#mysock.connect(("2402:f000:4:33:808::8ce",65420))
mysock.connect(("",65420))

mysock.send(b'hello')
time.sleep(1)

msg = mysock.recv(1024)
print(msg.decode())

mysock.send(b'run')
time.sleep(1)

#input start time
print('input start time [Y-M-D H:M:S][2000-01-01 01:01:01]:')
#print('for example: 2019-05-9 8:36:10')
datetime = input()
mysock.send(datetime.encode())

#input centre frequency
#print('input centre frequency(MHz):')
#freq = float(input()) * 1000000
#mysock.send(str(freq).encode())

#mysock.send(b'shutdown')
#time.sleep(1)
#mysock.send((str(90*1000*1000)).encode())

time.sleep(600)
