#!/usr/bin/python3
# -*- coding:utf-8 -*-

# module pyrtlsdr, scipy is needed

#FIXME: Use socket to transfer data to: 1.specific remote server;
#                                       2.localhost so the data can be processed in another process.
#       Or you can use pipe for local transmission, but I suggest socket to avoid redundant codes.
#       0/100

import os,sys
import socket
import datetime
import threading as MTP
import scipy
from apscheduler.schedulers.background import BackgroundScheduler
from lib import NRtlSdr
sys.path.append("/etc/tola")
import tola_conf as init

# generate data path
os.system('mkdir -p ' + init.path)
# generate logger
print(init.logger)
if init.logger == 'stdout':
    logger = sys.stdout
else:
    logger = open(init.logger, 'w')
logger.write('-'*50)
logger.write('\n' + str(datetime.datetime.utcnow()) + '\n')

def main():
    tola = NRtlSdr()
    tuner_sema = MTP.Semaphore(0)
    writer_sema = MTP.Semaphore(0)
    reg_sema = MTP.Semaphore(0)
    reg_sema.release()
    BUFF_mutex = MTP.Lock()
    tune = True
    BUFF = []
    threads = []
    
    tola.set_center_freq(init.center_freq)
    tola.set_freq_correction(init.err_ppm)
    tola.set_sample_rate(init.sample_rate)
    tola.set_bandwidth(init.bandwidth)
    tola.set_gain(init.gain)
    tola.set_direct_sampling(init.direct_samp)
    
    init.sample_size[1] = (2 * init.sample_rate * init.sample_size[1])//init.sample_size[0]
   
    logger.write("Applying settings over. Now I'll print all the settings:\n")
    logger.write('Center frenquency: ' + str(tola.get_center_freq()) + ' Hz.\n')
    logger.write('Frequency correction: ' + str(tola.get_freq_correction()) + ' ppm.\n')
    logger.write('Sample rate: ' + str(tola.get_sample_rate()) + ' Hz.\n')
    logger.write('Bandwidth: ' + str(tola.get_bandwidth()) + ' MHz.\n')
    logger.write('Amplifier gain: ' + str(tola.get_gain()) + ' dB.\n')
    logger.write('Tuner type: ' + str(tola.get_tuner_type()) + '.\n')
    logger.flush()
    
    threads.append(MTP.Thread(target = tuner, 
        args = (tola, init.sample_size, tuner_sema, writer_sema, reg_sema, BUFF_mutex, tune, BUFF)))
    
    threads.append(MTP.Thread(target = writer, 
        args = (BUFF, tune, writer_sema, BUFF_mutex, logger, init.path)))
    
    if init.if_ipv4:
        threads.append(MTP.Thread(target = servant4, 
            args = (socket.AF_INET, '', tuner_sema, reg_sema, tune, logger)))
    if init.if_ipv6:
        threads.append(MTP.Thread(target = servant6, 
            args = (socket.AF_INET6, '', tuner_sema, reg_sema, tune, tola, logger)))
    
    #for i in range(1, 20):
    #    tuning(tola, init.sample_size)
    for thread in threads:
        thread.start()
    
    for thread in threads[2:]:
        thread.join()

    
def tuner(sdr, size, tuner_sema, writer_sema, reg_sema, BUFF_mutex, tune, BUFF):
    while True:
        reg_sema.acquire()
        for i in range(0,2):
            ans = tuning(sdr, size)
            BUFF_mutex.acquire()
            BUFF.append(ans)
            BUFF_mutex.release()
            writer_sema.release()
        reg_sema.release()
        tuner_sema.acquire()
    

def tuning(sdr, size):
    # the return is [time, center_freq, data ]
    BUFFER = [datetime.datetime.utcnow(), init.center_freq, ]
    for i in range(0, size[1]):
        BUFFER.append(sdr.read_bytes(size[0]))
    return BUFFER

def writer(BUFF, tune, writer_sema, BUFF_mutex, logger, path):
    while True:
        writer_sema.acquire()
        try:
            BUFF_mutex.acquire()
            mana = BUFF.pop()
            BUFF_mutex.release()
        except IndexError:
            continue

        fname = init.path + mana.pop(0).strftime(str(init.sample_rate/(1024*1024)) + 'MHz' +'_UTC_%m-%d-%H:%M:%S:%f', )
        fname += "_cfreq_" + str(mana.pop(0))
        f = open(fname, 'wb')
        logger.write(str(mana[0]))
        for manas in mana:
            manas = scipy.array(manas, dtype = scipy.uint8)
            manas.tofile(f)
        f.close()
        logger.write('writer has finished his job.\n')
        logger.flush()

def dingshi(sema, logger):
    logger.write(datetime.datetime.now().strftime('%y-%m-%d %H:%M:%S') +  ' -> tuner_sema released.\n')
    sema.release()

def servant4(protocol, ip, tuner_sema, reg_sema, tune, logger, port = 65421):
    mysock = socket.socket(protocol, socket.SOCK_STREAM)
    mysock.bind(('', port))
    mysock.listen(1)
    logger.write('ipv4 waiting for connection.\n')
    
    ipv4_threads = []

    while True:
        sock, addr = mysock.accept()
       
        #judge whether there is already a connection existed
        #if true, shutdown the new 
        if ipv4_threads == []:             
            pass
        elif ipv4_threads[-1].isAlive(): 
            sock.close()
            logger.write('only 1 connection is allowed\n')
            continue

        #receive 'hello' to establish a connection 
        msg = sock.recv(1024)
        if msg == b'hello':
            #send a message to show client that connection is established
            sock.send(b'connection is established')
            #start a MTP to conduct it
            t = MTP.Thread(target=tcplink, args=(sock, addr, sema, tola, logger))
            ipv4_threads.append(t)
            t.start()
        else:
            sock.close()

    
def servant6(protocol, ip, tuner_sema, reg_sema, tune, tola, logger, port = 65420):
    mysock = socket.socket(protocol, socket.SOCK_STREAM)
    mysock.bind(('', port))
    mysock.listen(1)
    logger.write('ipv6 waiting for connection.\n')
     
    ipv6_threads = []
   
    while True:
        sock, addr = mysock.accept()
        
        #judge whether there is already a connection existed
        #if true, shutdown the new 
        if ipv6_threads == []:         #first running
            pass
        elif ipv6_threads[-1].isAlive():   #if connection exist, shut down new
            sock.close()
            logger.write('only 1 connection is allowed\n')
            continue

        #receive 'hello' to establish a connection 
        msg = sock.recv(1024)
        if msg == b'hello':         
            #send a message to show client that connection is established
            sock.send(b'connection is established')
            #start a MTP to conduct it
            t = MTP.Thread(target=tcplink, args=(sock, addr, tuner_sema, reg_sema, tola, logger))
            ipv6_threads.append(t)
            t.start()
        else:
            sock.close() 

def tcplink(sock, addr, tuner_sema, reg_sema, tola, logger):
    logger.write('start serving!\n')
    i = 0
    while True:
        msg = sock.recv(1024)
        logger.write(str(msg))
        if msg == b'shutdown':
            os.system('kill ' + str(os.getpid()))
        elif msg == b'run':
            #receive start time 
            date_msg = sock.recv(1024)    
            date_msg = date_msg.decode('utf-8')
            logger.write(date_msg)
            logger.write('\n')

            #set start time
            scheduler = BackgroundScheduler()
            scheduler.add_job(func=dingshi, args=(tuner_sema, logger, ), trigger='date', run_date = date_msg) 
            scheduler.start()

        elif msg == b'freq':
            init.center_freq = float(sock.recv(1024).decode())

            reg_sema.acquire()
            tola.set_center_freq(init.center_freq)
            reg_sema.release()

            logger.write('Center frenquency: ' + str(tola.get_center_freq()) + ' Hz.\n')

        elif msg == b'':        #disconnect
            i = i+1
            if i==10 :
                sock.close()
                break
    logger.write('connection lost\n')
   
    
   
if __name__ == '__main__':
    main()
