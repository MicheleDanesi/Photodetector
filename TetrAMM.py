import socket
import time
import sys
import struct
import numpy as np
import scipy.fftpack
import Plot
from datetime import datetime

'''
NB: with ASCII:ON each row of the all four channels has 65 bytes
each number occupies 15 bytes plus the character /t and /r/n 
Executing sequentially acqon-read-acqoff the system acquires 10 rows of 4 channels

NB the class is written to read data in binary code, thus all instances that require
reading of data in ASCII need to be adjusted.
'''
''' -----------------------System Connection and initialization----------------------------'''

class quad:
    
  def __init__(self, host="192.168.0.10", port=10001, debug=False):
    self.host = host
    self.port = port
    self.data = []
    self.dacq = []
    self.samp = 0
    self.plot = Plot.PlotIM()
    self.nchan = 4
    self.debug = debug
    self.pht_second = True
    self.sumChannel = -1
    self.sumScaling = 0.25
    #self.plot.x = np.linspace(0, 100000, int(np.shape(self.data)[0]))
    #self.plot.data = self.data
    self.Nacq = 0
    try: 
        self.c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #self.c.setblocking(0)   # if you read without available data the socket will not block but it will
                                # raise an exception - socket.setblocking(flag)
    except socket.error:
        print('Failed to create socket.')
        sys.exit()
    try:
        self.c.connect((host, port))
        '''self.c.setblocking(0)''' 
    except socket.error:
        print("Failed to connect to ip " + host)
        
    print('Connection to socket ON')
    self.c.sendall(b'ascii:off\r\n')
    print('ASCII OFF: ' + self.c.recv(1024).decode('utf-8'))
    self.c.sendall(b'ifconfig\r\n')
    print(self.c.recv(1024).decode('utf-8'))
    self.c.sendall(b'chn:?\r\n')
    print(self.c.recv(7).decode('utf-8'))
    self.c.sendall(b'rng:0\r\n')
    print('RANGE: ' + self.c.recv(5).decode('utf-8'))
    self.c.sendall(b'status:?\r\n')
    print(self.c.recv(24).decode('utf-8'))
        
  def manual(self):
    print('Nchan: shows the current number of active channels and resets them.\n')
    print('rangeq: set the operation range (measured current and sensitivity)\n')
    print('get: takes a snapshot of just one measure.\n')
    print('acqon: starts the continuous acquisition of data.\n')
    print('acqoff: stops the acquisition.\n')
    print('fast: takes a number N of samples at the maximum acquisition frequency.\n')
    print('read: reads one time the response of the system.\n')
    print('write: writes a command to the system.\n')
    print('close: stops the connection with the instrument.\n')
    
  ''' ---------------------------System settings and requests-----------------------------'''
  
  def dodebug(self, x=True):
      self.debug = x
      
  def subsChan(self, x=True):
      self.brokeChan = x
      
  def subsPht(self, x=True):
      self.pht_second = x
        
  def Nchan(self):
    bb = str.encode('chn:?\r\n','utf-8')
    self.c.sendall(bb)
    lof = self.c.recv(5).decode('utf-8')
    self.flush()
    self.nchan = int(lof[4])
    return int(lof[4])
    
  def setNchan(self,x):
    x = str(x)
    bb = str.encode('chn:','utf-8') + str.encode(x +'\r\n','utf-8')
    self.c.sendall(bb)
    self.nchan = int(x);
    self.flush()
        
  def setRange(self,x):
    x = str(x)
    bb = str.encode('rng:','utf-8') + str.encode(x +'\r\n','utf-8')
    self.c.sendall(bb)
    self.flush()
    
  def nrsamp(self, x=5):
    x = int(x)
    bb = str.encode('nrsamp:5\r\n','utf-8')
    #bb = str.encode('naq:','utf-8') + str.encode(str(x)+'\r\n','utf-8') 
    self.c.sendall(bb)
    #self.data = self.recvf(x)
    if self.debug:
        print(self.data)
        print('data Tetramm class')
    print(self.c.recv(5))
    
  def setTRG(self, K):
    if K is True:
        x = 'ON'
    else:
        x = 'OFF'
    #self.c.setblocking(0)
    #self.c.setblocking(1)
    bb = str.encode('TRG:')+str.encode(x+'\r\n','utf-8')
    #self.flush()
    self.c.sendall(bb)
    '''
    ans = str(self.c.recv(5).decode('utf-8'))
    if ans == 'ACK\r\n':
        print(ans)
        print('Yeah baby')
    else:
        print('Command not acnowledged')
        K = False
    '''
    return(K)    
    
  def setTrgPol(self, K):
    if K is True:
        x = 'POS'
    else:
      x = 'NEG'
    bb = str.encode('TRGPOL:')+str.encode(x+'\r\n','utf-8')   
    self.c.sendall(bb)
    self.c.recv(5)
    
  ''' -----------------------------Acquisition functions-----------------------------------'''
  def get(self):
    self.c.sendall(b'get\r\n') 
    self.data = self.recvf()
  
  # It seems that the command NACQ does not work in the instrument itself
  '''
  def nacq(self, x=1):
    bb = str.encode('naq:2\r\n','utf-8')
    #bb = str.encode('naq:','utf-8') + str.encode(str(x)+'\r\n','utf-8') 
    self.c.sendall(bb)
    #self.data = self.recvf(x)
    #print(self.c.recv(100))
    if self.debug:
        print(self.data)
        print('data Tetramm class')
    print(self.c.recv(5))
  '''
  
  def acqon(self):  
    bb = str.encode('acq:on\r\n','utf-8') 
    self.c.sendall(bb)
            
  def acqoff(self):
    bb = str.encode('acq:off\r\n','utf-8') 
    self.c.sendall(bb)
    #print(self.c.recv(3).decode('utf-8'))
    #self.flush()
    
  def fast(self, x):
    self.samp = int(x)
    n = self.nchan;
    m = (n+1)*8*self.samp
    bb = str.encode('fastnaq:','utf-8') + str.encode(str(self.samp) +'\r\n','utf-8')
    self.c.sendall(bb)
    p = bytearray()
    while len(p) < struct.calcsize('>' + str((self.samp+1)*(n+1)) + 'd'):
        p = p + self.c.recv(m)
    try:
        data = struct.unpack('>' + str((self.samp+1)*(n+1)) + 'd', p)
    except:
        print('Buffer error, retry')
        return
    data = np.array(data).reshape([self.samp+1,n+1])
    self.data = data[0:-1,0:-1]
    if self.pht_second:
        self.data = self.addPht(self.data)    
    
  def whAcq(self, x, y=1):
    i = 1
    self.Nacq = y
    self.samp = int(x)
    self.fast(self.samp)
    self.dacq = self.data   

    while i < self.Nacq:#True:
        self.fast(self.samp)
        self.dacq = np.vstack((self.dacq, self.data))
        i += 1
        
  def naqCom(self):       
    print('Set the number of samples (1-2 billion):')
    self.samp = str(input())
    print(self.samp)
    n = self.Nchan();
    n = n*16*int(self.samp)
    print(n)
    self.c.recv(3).decode('utf-8')
    time.sleep(0.1)
    bb = str.encode('naq:','utf-8') + str.encode(self.samp +'\r\n','utf-8')
    self.c.sendall(bb)
    time.sleep(1)
    print(self.c.recv(n).decode('utf-8'))
    
  def test(self,x):
    self.samp = int(x)
    time.sleep(7)
    self.fast(self.samp)
    
    
  
  ''' ------------------------------Read and write functions-------------------------------'''
    
  def flush(self):    
    if self.debug:
        print(self.c.recv(17280))
    else:
        self.c.recv(17280)
        
  def recvAcq(self,x=1):
    x = int(x)
    p = self.c.recv((self.nchan+1)*x*8)
    try:
        data = struct.unpack('>' + str(self.nchan+1) + 'd', p)
        data = np.array(data[0:-1]).reshape(1,self.nchan)
    except:
        self.flush()
        data = np.ones(self.nchan+1)*float('NaN')
        return(data)
    if self.pht_second:
        data = self.addPht(data)    
    return(data)
    
  def recvf(self,x=1):
    x = int(x)
    p = self.c.recv((self.nchan+1)*x*8)
    try:
        data = struct.unpack('>' + str(self.nchan+1) + 'd', p)
        data = data[0:self.nchan]        
        if self.pht_second:
            data = self.addPht(data)
    except:
        if self.debug:
            print(self.c.recv(40))
        self.flush()
        data = np.ones(self.nchan+1)*float('NaN')
        
    return(data)
        
  def read(self,x):
    print(self.c.recv(x).decode('utf-8'))
    
  def readcheck(self):
    self.c.recv(1)
    
  def write(self, com):
    bb = str.encode(com,'utf-8') + str.encode('\r\n','utf-8')
    self.c.sendall(bb)
        
  def writeCom(self):
    print('Command:     ')
    x = str(input())
    bb = str.encode(x,'utf-8') + str.encode('\r\n','utf-8')
    self.c.sendall(bb)
    r = self.c.recv(2048).decode('utf-8')
    print(r)
 
  def fileWrite(self, fname='Fast_Data.txt', met='w+'):
    now = datetime.now()
    file = open(fname, 'a')
    file.write('\n\n'+now.strftime('%d %m %Y %H:%M:%S')+'\n\n')
    file.write('Acquisition number: 1\n\n')    
    if self.samp <= 100:
        for ii in range(self.Nacq):
            for jj in range(self.samp):
                dt = str(self.dacq[int(ii*self.samp+jj):int(ii*self.samp+jj+1),0:-1])+str(self.dacq[int(ii*self.samp+jj):int(ii*self.samp+jj+1),-1])
            dt = dt.replace('[', '')
            dt = dt.replace(']', '')
            file.write(dt+'\n\n')
            if ii == (self.Nacq-1):
                file.write('End of acquisition\n\n')
            else:
                file.write('Acquisition number: '+str(ii+2)+'\n\n')
        file.close()
    else:
        x1 = self.samp
        kk = 0 
        while x1 >= 100:
            x1 = x1-100   
            kk += 1 
        for ii in range(self.Nacq):
            for jj in range(kk):               
                for aa in range(100):
                    dt = str(self.dacq[int((ii*self.samp+aa)+jj*100):int((ii*self.samp)+aa+1+(jj+1)*100),0:-1])+str(self.dacq[int((ii*self.samp+aa)+jj*100):int((ii*self.samp)+aa+1+(jj+1)*100),-1])
                dt = dt.replace('[', '')
                dt = dt.replace(']', '')
                file.write(dt+'\n') 
                
            for aa in range(x1):
                dt = str(self.dacq[int((ii*self.samp+aa)+kk*100):int((ii*self.samp)+kk*100+aa+1),0:-1])+str(self.dacq[int((ii*self.samp+aa)+kk*100):int((ii*self.samp)+kk*100+aa+1),-1])
            dt = dt.replace('[', '')
            dt = dt.replace(']', '')
            file.write(dt+'\n\n')
            if ii == (self.Nacq-1):
                file.write('End of acquisition\n\n')
            else:
                file.write('Acquisition number: '+str(ii+2)+'\n\n')
            
    file.close()
    
  def fWdataAnalysis(self, fname='Fast_Data_Analysis.txt', met='w+'):
    file = open(fname, 'a')    
    if self.samp <= 100:
        for ii in range(self.Nacq):
            dt = str(self.dacq[int(ii*self.samp):int(ii*self.samp+self.samp),:])
            dt = dt.replace('[', '')
            dt = dt.replace(']', '')
            file.write(dt+'\n')
        file.close()
    else:
        x1 = self.samp
        kk = 0 
        while x1 >= 100:
            x1 = x1-100   
            kk += 1 
        for ii in range(self.Nacq):
            for jj in range(kk):
                dt = str(self.dacq[int((ii*self.samp)+jj*100):int((ii*self.samp)+(jj+1)*100),:])
                dt = dt.replace('[', '')
                dt = dt.replace(']', '')
                file.write(dt+'\n') 

            dt = str(self.dacq[int((ii*self.samp)+kk*100):int((ii*self.samp)+kk*100+x1),:])
            dt = dt.replace('[', '')
            dt = dt.replace(']', '')
            file.write(dt+'\n\n')
            
    file.close()
    
  def Widfile(self, filename, met='w+'):
    file = open(filename, met)    
    
    x1 = int(np.shape(self.data)[0])
    kk = 0 
    while x1 >= 100:
        x1 = x1-100   
        kk += 1 
    for jj in range(kk):
        dt = str(self.data[(jj*100):((jj+1)*100),:])
        dt = dt.replace('[', '')
        dt = dt.replace(']', '')
        file.write(dt+'\n') 

    dt = str(self.data[(kk*100):(kk*100+x1),:])
    dt = dt.replace('[', '')
    dt = dt.replace(']', '')
    file.write(dt+'\n')
            
    file.close()
        
  def addPht(self, data):
    if len(data) == 0:
        return(0)
    else: 
        if np.size(data) <= self.nchan:
            if self.sumChannel >=0:
                dataSum = data[0,1]
                data[0,self.sumChannel] = self.sumScaling*data[0,self.sumChannel]-np.sum(data,axis=1)+data[0,self.sumChannel]
                data = np.append(data,dataSum)
                data = np.array(data)
            else:
                data = np.append(data, np.sum(data))
                data = np.array(data)
        else:
            if self.sumChannel >=0:
                dataSum = np.array(data[:,self.sumChannel])
                data[:,self.sumChannel] = data[:,self.sumChannel]*self.sumScaling-np.sum(data,axis=1)+data[:,self.sumChannel]
                data = np.array(data)
                data = np.concatenate((data,dataSum[:,None]),axis=1)
               
            else:
                sumdata = np.array(np.sum(data,axis=1))
                data = np.array(data)
                data = np.concatenate((data,sumdata[:,None]),axis=1)
        return(data)
    
  ''' ----------------------------Plot & FFT functions----------------------------------'''
  def sfft(self, data=None):
    if data is None:
        data = self.data
    else:
        pass
    n = self.nchan
    if n == 4:
        yf1 = scipy.fftpack.rfft(data[:,0]/np.max(data[:,0]))
        yf2 = scipy.fftpack.rfft(data[:,1]/np.max(data[:,1]))
        yf3 = scipy.fftpack.rfft(data[:,2]/np.max(data[:,2]))
        yf4 = scipy.fftpack.rfft(data[:,3]/np.max(data[:,3]))
        yf = np.append(yf1, [yf2,yf3,yf4])
    else: 
      if n == 2:
            yf1 = scipy.fftpack.fft(data[:,0]/np.max(data[:,0]))
            yf2 = scipy.fftpack.fft(data[:,1]/np.max(data[:,1]))
            yf = np.append(yf1, yf2)
      else: 
         if n == 1:
                    yf = scipy.fftpack.fft(data[:,0]/np.max(data[:,0]))
        
    xf = np.linspace(0, 100000, int(np.shape(data)[0]))
    return(xf, yf)
    
    
  def Widsfft(self, k):
    n = 4
    if n == 4:
        yf1 = scipy.fftpack.rfft(self.data[-k:,0]/np.max(self.data[-k:,0]))
        yf2 = scipy.fftpack.rfft(self.data[-k:,1]/np.max(self.data[-k:,1]))
        yf3 = scipy.fftpack.rfft(self.data[-k:,2]/np.max(self.data[-k:,2]))
        yf4 = scipy.fftpack.rfft(self.data[-k:,3]/np.max(self.data[-k:,3]))
        
        return(yf1, yf2, yf3, yf4)
            
    else: 
      if n == 2:
            yf1 = scipy.fftpack.fft(self.data[-k:,0]/np.max(self.data[-k:,0]))
            yf2 = scipy.fftpack.fft(self.data[-k:,1]/np.max(self.data[-k:,1]))
            
            return(yf1, yf2)
      else: 
         if n == 1:
            yf1 = scipy.fftpack.fft(self.data[-k:,0]/np.max(self.data[-k:,0]))
            return(yf1)
    
    
        
  def plS(self, k1=8000, k2=9000):
    self.plot.x = np.linspace(0, int(np.shape(self.data)[0], int(np.shape(self.data)[0])))
    self.plot.data = self.data
    self.plot.k1 = int(k1)
    self.plot.k2 = int(k2)
    self.plot.Sig()
    
    
  def plfftA(self, k1=10, k2=500):
    [xf, yf] = self.sfft()
    self.plot.x = xf
    self.plot.y = yf
    self.plot.data = self.data
    l = int(np.shape(self.plot.x)[0])
    if k1 < 10:
       k1 = 10
    self.plot.k1 = int(k1*l/100000)
    self.plot.k2 = int(k2*l/100000)
    self.plot.fftAll()
    
  def plfft4(self, k1=10, k2=500):
    [xf, yf] = self.sfft()
    self.plot.x = xf
    self.plot.y = yf
    self.plot.data = self.data
    l = int(np.shape(self.plot.x)[0])
    if k1 < 10:
       k1 = 10
    self.plot.k1 = int(k1*l/100000)
    self.plot.k2 = int(k2*l/100000)
    self.plot.fft4()
    
  
    
    
    
  ''' -----------------------Close and Shutdown of connection----------------------------'''

  def close(self):
    self.c.close()
    
  def shutdown(self):
    self.c.shutdown(socket.SHUT_RDWR)
    

