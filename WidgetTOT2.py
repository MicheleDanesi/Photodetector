import sys
from PyQt5.QtCore import Qt, QObject, pyqtSignal as Signal, pyqtSlot as Slot, QRunnable, QThreadPool, QTimer
from PyQt5.QtWidgets import QDoubleSpinBox, QComboBox, QCheckBox, QMessageBox, QLabel, QLineEdit, QLCDNumber, QApplication, QPushButton, QMainWindow, QVBoxLayout, QWidget, QHBoxLayout #from pyqtgraph import PlotWidget, plot
import numpy as np
import TetrAMM
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from PyQt5.QtGui import QPalette, QColor
import time
from datetime import datetime 
import h5py
import os



#################################### Classes for the main ###########################################
#Declaration of the signal utilized to pilot the Worker classes

class WorkerSignals(QObject):
    finish = Signal()
    progress = Signal(float)
    stop = Signal()
    
#--------------------------------- Timer dependent acquisition worker -----------------------------------------#   

# Class that defines the 'Get' routine, for single acquisitions or timer controlled acquisition. In this class are
# included also a schematic of the Pointer in real time and a schematic of the signals. The sampling time can be
# at mosto of 500ms if all the widgets are showing at the same time, otherwise the program can keep up to 300ms.
# Other functionalities should be implemented, like: the possibility to open or close plot windows while the program
# is running (connection of signals); decorative elements to the plots; find a more time-efficient way to refresh the
# plots without clearing the axes and re-drawing which is time-consuming; implement a trigger mode to control the cicles;
# impement a way to select the number of desired active channels. In this case it is all, default 4.
    
class WorkerGet(QRunnable):
    
    def __init__(self, qobj, canv, canvP, fullPath, dataPath, pointLine, GsigLine, NumberData, ComboBox, attributes, fbool=True, debug=False, chSave=True, chSig=True, chPoint=True):
        super(WorkerGet, self).__init__()
        self.signals = WorkerSignals()
        self.qobj = qobj                    # definition of the TetrAMM class object
        self.qobj.dacq = qobj.dacq          # initialization of the dataacq matrix in the class object
        self.canv = canv                    # initialization of the imported widget from MainWindow
        self.canvB = self.canv
        self.canvP = canvP
        self.fullPath = fullPath
        self.dataPath = dataPath
        self.pointLine = pointLine
        self.GsigLine = GsigLine
        self.attributes = attributes
        self.bool = True
        self.fbool = fbool                  #boolean of single shot (True) or timer set (False)
        self.debug = debug
        self.saveCheckbox = chSave
        self.chSig = chSig
        self.chPoint = chPoint
        self.NumberData = NumberData
        self.ComboBox = ComboBox
         
        if self.GsigLine.text() == '':
            self.x = 50                     # self.x is the number of data that the user wants to plot on the Signal plot
        else:
            self.x = int(self.GsigLine.text())
        
    # NB. the run slot works on its own during operation, thus can communicate to themain only using the 
    #     previously defined signals (class WorkerSignals). Making the running sequens interact with other
    #     functions of the main will only slow down the calculations since the two, run and main work in different
    #     threads. I'm still not sure about functions that are owned by the worker class in this regard.
    
    @Slot()
    def run(self):
        #self.qobj.get()
        if self.NumberData.text() == '':
            ND = 1
        else:
            ND = int(self.NumberData.text())
        self.qobj.fast(ND)
        if ND > 1:
            self.qobj.data = np.mean(self.qobj.data, axis=0)
        
        if self.saveCheckbox.isChecked():
            start_time = time.time()
        if self.fbool == True:
            # Here many if/else instances are in place to differentiate the first acquisition to the rest, probably
            # there is a more efficient way to this. In this case the differentiation is in place when the data are
            # arrays or matricies
            # the next sections divide the coordinate calculus in various cases depending on the dimension of the 
            # data array and on the number of data that the user wants to plot            
            if np.size(self.qobj.dacq) == 0:
                self.qobj.dacq = self.qobj.data
                if self.chSig.isChecked():
                    self.xd = np.linspace(1, 1, 1)
                    self.yd1 = self.qobj.dacq[0]
                    self.yd2 = self.qobj.dacq[1]
                    self.yd3 = self.qobj.dacq[2]
                    self.yd4 = self.qobj.dacq[3]
                    self.yd5 = self.qobj.dacq[4]
            else:   
                self.qobj.dacq = np.vstack((self.qobj.dacq, self.qobj.data))
                if self.chSig.isChecked():
                    self.xd = np.linspace(1, int(np.shape(self.qobj.dacq)[0]), int(np.shape(self.qobj.dacq)[0]))
                    self.yd1 = self.qobj.dacq[:,0]
                    self.yd2 = self.qobj.dacq[:,1]
                    self.yd3 = self.qobj.dacq[:,2]
                    self.yd4 = self.qobj.dacq[:,3]
                    self.yd5 = self.qobj.dacq[:,4]
        else:
            if np.size(self.qobj.dacq) == 0:
                self.qobj.dacq = self.qobj.data
                if self.chSig.isChecked():
                    self.xd = np.linspace(1, 1, 1)
                    self.yd1 = self.qobj.dacq[0]
                    self.yd2 = self.qobj.dacq[1]
                    self.yd3 = self.qobj.dacq[2]
                    self.yd4 = self.qobj.dacq[3]
                    self.yd5 = self.qobj.dacq[4]
            else:
                self.qobj.dacq = np.vstack((self.qobj.dacq, self.qobj.data))        
                if self.chSig.isChecked():          
                    if len(self.qobj.dacq) < self.x:
                            
                        self.xd = np.linspace(-int(np.shape(self.qobj.dacq)[0]), 1, int(np.shape(self.qobj.dacq)[0]))
                        self.yd1 = self.qobj.dacq[:,0]
                        self.yd2 = self.qobj.dacq[:,1]
                        self.yd3 = self.qobj.dacq[:,2]
                        self.yd4 = self.qobj.dacq[:,3]
                        self.yd5 = self.qobj.dacq[:,4]
                        
                    else:       
                        self.xd = np.linspace(-(self.x+1), 1, self.x)
                        self.yd1 = self.qobj.dacq[-self.x:,0]
                        self.yd2 = self.qobj.dacq[-self.x:,1]
                        self.yd3 = self.qobj.dacq[-self.x:,2]
                        self.yd4 = self.qobj.dacq[-self.x:,3]
                        self.yd5 = self.qobj.dacq[-self.x:,4]
                  
        # Here is where the clearing and re-drawing of the canvas should be revised since this block works as a bottleneck
        # for the all run sequence
        
        if self.chSig.isChecked():
            self.canv.axes.cla()
            self.canv.axes.grid(visible=True, color='0.8', linewidth=0.3)
            if self.ComboBox.currentIndex() == 0:
                self.canv.axes.plot(self.xd, self.yd1, 'r*-',\
                                    self.xd, self.yd2, 'y*-',\
                                    self.xd, self.yd3, 'g*-',\
                                    self.xd, self.yd4, 'b*-')
                self.canv.axes.legend(['CH1', 'CH2', 'CH3', 'CH4'])
            if self.ComboBox.currentIndex() == 1:
                self.canv.axes.plot(self.xd, self.yd5, 'w*-')
                self.canv.axes.legend(['Sum'])
            if self.ComboBox.currentIndex() == 2:
                self.canv.axes.plot(self.xd, self.yd1, 'r*-',\
                                    self.xd, self.yd2, 'y*-',\
                                    self.xd, self.yd3, 'g*-',\
                                    self.xd, self.yd4, 'b*-',\
                                    self.xd, self.yd5, 'w*-')
                self.canv.axes.legend(['CH1', 'CH2', 'CH3', 'CH4', 'Sum'])
            
            self.canv.draw()
            
        
        # Routine that pilots the Pointer plot. When in single mode this block responds with a semi-error in the 
        # canvas drawing process which does not block the plotting nor the program but fill the IPhython console
        # I'm still not sure what causes this problem, it could be the various try-except-else routines. Again the
        # over-complication of this section is related to the type of data of the program, when is single shot it has
        # problems or imperfections, while in sampling mode works just fine
        
        if self.pointLine.text() == '':
            pl = 1
        else:
            pl = int(self.pointLine.text())
        if self.chPoint.isChecked() and int(np.shape(self.qobj.dacq)[0]) > pl:
            try:
                Yold = ((np.mean(self.qobj.dacq[-2*pl:-pl,0])+np.mean(self.qobj.dacq[-2*pl:-pl,1])-np.mean(self.qobj.dacq[-2*pl:-pl,3])-np.mean(self.qobj.dacq[-2*pl:-pl,2])))/(np.mean(self.qobj.dacq[-2*pl:-pl,0])+np.mean(self.qobj.dacq[-2*pl:-pl,2])+np.mean(self.qobj.dacq[-2*pl:-pl,1])+np.mean(self.qobj.dacq[-2*pl:-pl,3]))
                Xold = ((np.mean(self.qobj.dacq[-2*pl:-pl,1])+np.mean(self.qobj.dacq[-2*pl:-pl,2])-np.mean(self.qobj.dacq[-2*pl:-pl,0])-np.mean(self.qobj.dacq[-2*pl:-pl,3])))/(np.mean(self.qobj.dacq[-2*pl:-pl,0])+np.mean(self.qobj.dacq[-2*pl:-pl,2])+np.mean(self.qobj.dacq[-2*pl:-pl,1])+np.mean(self.qobj.dacq[-2*pl:-pl,3]))                
                Y = ((np.mean(self.qobj.dacq[-pl:,0])+np.mean(self.qobj.dacq[-pl:,1])-np.mean(self.qobj.dacq[-pl:,3])-np.mean(self.qobj.dacq[-pl:,2])))/(np.mean(self.qobj.dacq[-pl:,0])+np.mean(self.qobj.dacq[-pl:,2])+np.mean(self.qobj.dacq[-pl:,1])+np.mean(self.qobj.dacq[-pl:,3]))
                X = ((np.mean(self.qobj.dacq[-pl:,1])+np.mean(self.qobj.dacq[-pl:,2])-np.mean(self.qobj.dacq[-pl:,0])-np.mean(self.qobj.dacq[-pl:,3])))/(np.mean(self.qobj.dacq[-pl:,0])+np.mean(self.qobj.dacq[-pl:,2])+np.mean(self.qobj.dacq[-pl:,1])+np.mean(self.qobj.dacq[-pl:,3]))
            except:
                if pl == 1:
                    try:
                         Y = (self.qobj.dacq[-pl,0]+self.qobj.dacq[-pl,1]-self.qobj.dacq[-pl,2]-self.qobj.dacq[-pl,3])/(self.qobj.dacq[-pl,0]+self.qobj.dacq[-pl,2]+self.qobj.dacq[-pl,1]+self.qobj.dacq[-pl,3]) 
                         X = (self.qobj.dacq[-pl,1]+self.qobj.dacq[-pl,2]-self.qobj.dacq[-pl,0]-self.qobj.dacq[-pl,3])/(self.qobj.dacq[-pl,0]+self.qobj.dacq[-pl,2]+self.qobj.dacq[-pl,1]+self.qobj.dacq[-pl,3])
                    except:
                         Y = (self.qobj.dacq[0]+self.qobj.dacq[1]-self.qobj.dacq[2]-self.qobj.dacq[3])/(self.qobj.dacq[0]+self.qobj.dacq[2]+self.qobj.dacq[1]+self.qobj.dacq[3]) 
                         X = (self.qobj.dacq[1]+self.qobj.dacq[2]-self.qobj.dacq[0]-self.qobj.dacq[3])/(self.qobj.dacq[0]+self.qobj.dacq[2]+self.qobj.dacq[1]+self.qobj.dacq[3])
                    else:
                         Y = (self.qobj.dacq[-pl,0]+self.qobj.dacq[-pl,1]-self.qobj.dacq[-pl,2]-self.qobj.dacq[-pl,3])/(self.qobj.dacq[-pl,0]+self.qobj.dacq[-pl,2]+self.qobj.dacq[-pl,1]+self.qobj.dacq[-pl,3]) 
                         X = (self.qobj.dacq[-pl,1]+self.qobj.dacq[-pl,2]-self.qobj.dacq[-pl,0]-self.qobj.dacq[-pl,3])/(self.qobj.dacq[-pl,0]+self.qobj.dacq[-pl,2]+self.qobj.dacq[-pl,1]+self.qobj.dacq[-pl,3])                   
                else:
                    Y = ((np.mean(self.qobj.dacq[-pl:,0])+np.mean(self.qobj.dacq[-pl:,1])-np.mean(self.qobj.dacq[-pl:,3])-np.mean(self.qobj.dacq[-pl:,2])))/(np.mean(self.qobj.dacq[-pl:,0])+np.mean(self.qobj.dacq[-pl:,2])+np.mean(self.qobj.dacq[-pl:,1])+np.mean(self.qobj.dacq[-pl:,3]))
                    X = ((np.mean(self.qobj.dacq[-pl:,1])+np.mean(self.qobj.dacq[-pl:,2])-np.mean(self.qobj.dacq[-pl:,0])-np.mean(self.qobj.dacq[-pl:,3])))/(np.mean(self.qobj.dacq[-pl:,0])+np.mean(self.qobj.dacq[-pl:,2])+np.mean(self.qobj.dacq[-pl:,1])+np.mean(self.qobj.dacq[-pl:,3]))
            else:
                Yold = ((np.mean(self.qobj.dacq[-2*pl:-pl,0])+np.mean(self.qobj.dacq[-2*pl:-pl,1])-np.mean(self.qobj.dacq[-2*pl:-pl,3])-np.mean(self.qobj.dacq[-2*pl:-pl,2])))/(np.mean(self.qobj.dacq[-2*pl:-pl,0])+np.mean(self.qobj.dacq[-2*pl:-pl,2])+np.mean(self.qobj.dacq[-2*pl:-pl,1])+np.mean(self.qobj.dacq[-2*pl:-pl,3]))
                Xold = ((np.mean(self.qobj.dacq[-2*pl:-pl,1])+np.mean(self.qobj.dacq[-2*pl:-pl,2])-np.mean(self.qobj.dacq[-2*pl:-pl,0])-np.mean(self.qobj.dacq[-2*pl:-pl,3])))/(np.mean(self.qobj.dacq[-2*pl:-pl,0])+np.mean(self.qobj.dacq[-2*pl:-pl,2])+np.mean(self.qobj.dacq[-2*pl:-pl,1])+np.mean(self.qobj.dacq[-2*pl:-pl,3]))                
                Y = ((np.mean(self.qobj.dacq[-pl:,0])+np.mean(self.qobj.dacq[-pl:,1])-np.mean(self.qobj.dacq[-pl:,3])-np.mean(self.qobj.dacq[-pl:,2])))/(np.mean(self.qobj.dacq[-pl:,0])+np.mean(self.qobj.dacq[-pl:,2])+np.mean(self.qobj.dacq[-pl:,1])+np.mean(self.qobj.dacq[-pl:,3]))
                X = ((np.mean(self.qobj.dacq[-pl:,1])+np.mean(self.qobj.dacq[-pl:,2])-np.mean(self.qobj.dacq[-pl:,0])-np.mean(self.qobj.dacq[-pl:,3])))/(np.mean(self.qobj.dacq[-pl:,0])+np.mean(self.qobj.dacq[-pl:,2])+np.mean(self.qobj.dacq[-pl:,1])+np.mean(self.qobj.dacq[-pl:,3]))

            self.canvP.axes.cla()
            self.canvP.axes.grid(visible=True, color='0.8', linewidth=0.3)
            self.canvP.axes.set_xlim(-1,1)
            self.canvP.axes.set_ylim(-1,1)
            
            if 'Xold' in locals():
                self.canvP.axes.plot(Xold, Yold, 'yo', X, Y, 'ro', ms=50)
            else:
                self.canvP.axes.plot(X, Y, 'ro', ms=50)
            self.canvP.draw()
        
        if self.saveCheckbox.isChecked():
            with h5py.File(self.fullPath,'a') as file:
                if self.dataPath in file:
                    #if np.shape(self.qobj.dacq[:,0]) == 100:
                        
                    #file[self.dataPath].resize(int(np.shape(self.qobj.dacq)[0]), axis=0)
                    print(file[self.dataPath])
                    file[self.dataPath][int(np.shape(self.qobj.dacq)[0]-1),:] = self.qobj.data[None,:]
                    #file[self.dataPath][-1,:] = self.qobj.data 
                else:                
                    file.create_dataset(self.dataPath, data=np.nan((100,self.qobj.nchan+1)), dtype='d', maxshape=(100,self.qobj.nchan+1))
                    file[self.dataPath][0,:] = self.qobj.data[None,:]
                    file[self.dataPath].attrs['Sampling Time'] = self.attributes[0]
                    file[self.dataPath].attrs['Correction factor'] = self.attributes[1]
                    file[self.dataPath].attrs['Corrected channel'] = self.attributes[2]
                    file[self.dataPath].attrs['Position um'] = self.attributes[3]
            
        if self.bool == False:
            self.signals.stop.emit()
                  
        self.signals.finish.emit()
    # I'm not sure if this Slot works properly since sometimes the program skips this block and many repetitive 
    # button pushing are needed to impose a stop to the data sampling
    @Slot()   
    def stop(self):
        self.bool = False 
        
#-------------------------------------- Automatic acquisition Worker -----------------------------------------#   
 
# This section works in the background. The only visible element is the LCD widget that counts the number of acquired data
# This worker starts acquiring at the maximum sampling speed of the computer and of the program, thus managing to increase
# the efficiency of the program should result in a quicker sampling. Now the system works with a timing of approximately
# 4/5 microseconds.
    
class WorkerAcq(QRunnable):
    
    def __init__(self, qobj, lcd, fullPath, dataPath, attributes):
        super(WorkerAcq, self).__init__()
        self.signals = WorkerSignals()
        self.qobj = qobj
        self.bool = True
        self.cou = 0
        self.lcd = lcd
        self.fullPath = fullPath
        self.dataPath = dataPath
        self.attributes = attributes
        self.TRGstate = False #default setting of the trigger is false
        

    @Slot()
    def run(self):
        self.qobj.data = []
        ii = 0
        # Start of acquisition 
        self.qobj.acqon()
        file = h5py.File(self.fullPath,'a')
        
        # While-True loop that can be stopped by the AcqOFF Push Button through the stop Slot. Again I'm not shure the
        # stop works perfectly. As before it could be a problem of sequencing of the commands in the program
        while self.bool == True:
            if self.TRGstate:
                # I have to read the buffer looking for the header util the footer of the trigger signal
                start_time = time.time()
                try:
                    dt = self.qobj.recvAcq()
                    dt = np.append(dt, time.time()-start_time)
                    if self.dataPath in file:
                        file[self.dataPath].resize(int(np.shape(file[self.dataPath])[0])+1, axis=0)
                        file[self.dataPath][-1,:] = dt 
                    else:                
                        file.create_dataset(self.dataPath, data=dt[None,:], dtype='d', maxshape=(None,self.qobj.nchan+2))
                        file[self.dataPath].attrs['Correction factor'] = self.attributes[0]
                        file[self.dataPath].attrs['Corrected channel'] = self.attributes[1]
                        
                except:
                    self.cou -= 1
                self.cou += 1
                ii += 1
                if ii == 10:
                   self.lcd.display(self.cou) 
                   ii = 0
            else:
                start_time = time.time()            
                dt = self.qobj.recvAcq()
                dt = np.append(dt, time.time()-start_time)
                if self.dataPath in file:
                    file[self.dataPath].resize(int(np.shape(file[self.dataPath])[0])+1, axis=0)
                    file[self.dataPath][-1,:] = dt 
                else:                
                    file.create_dataset(self.dataPath, data=dt[None,:], dtype='d', maxshape=(None,self.qobj.nchan+2))
                    file[self.dataPath].attrs['Correction factor'] = self.attributes[0]
                    file[self.dataPath].attrs['Corrected channel'] = self.attributes[1]
                self.cou += 1
                ii += 1
                if ii == 10:
                   self.lcd.display(self.cou) 
                   ii = 0    
        self.lcd.display(self.cou)    
        self.qobj.flush()               # These flushes and readings of the TetrAMM class are needed to 
                                        # get rid of the over-reading or the wrong reading of the socket bus.
                                        # To keep in mind that reading and interpreting the data from the instruments
                                        # requires the exact number of read bites.
        self.qobj.acqoff()
        file.close()
        # Routine to write all the acquired data on a file after the acquisition so that the process does not limit
        # the acquisition time.
        
        self.signals.finish.emit()
        
    @Slot()   
    def stop(self):
        self.bool = False
        
    @Slot()   
    def TRG(self, k):
        self.TRGstate = self.qobj.setTRG(k)
        if k:
            self.file.write('\nTrigger ON\n\n')
        
#-------------------------------------- Fast acquisition worker -----------------------------------------#         
        
class WorkerFast(QRunnable):
    
    def __init__(self, qobj, fullPath, dataPath, attributes, x=100000, y=1, filename='Fast'):
        super(WorkerFast, self).__init__()
        self.signals = WorkerSignals()
        self.qobj = qobj
        self.bool = True
        self.Ndata = x
        self.Nacq = y
        self.fullPath = fullPath
        self.dataPath = dataPath
        self.attributes = attributes

    @Slot()
    def run(self):
        
        with h5py.File(self.fullPath,'a') as file:
            for ii in range(self.Nacq):
                self.qobj.fast(self.Ndata)
                if self.dataPath in file:
                    self.dataPath = self.dataPath_old+'_'+str(ii)
                    file.create_dataset(self.dataPath, data=self.qobj.data, dtype='d')
                    file[self.dataPath].attrs['Correction factor'] = self.attributes[0]
                    file[self.dataPath].attrs['Corrected channel'] = self.attributes[1]
                    file[self.dataPath].attrs['Number of data'] = self.attributes[2]
                    file[self.dataPath].attrs['Number of acquisitions'] = self.attributes[3] 
                else:
                    self.dataPath_old = self.dataPath
                    self.dataPath = self.dataPath_old+'_'+str(ii)
                    file.create_dataset(self.dataPath, data=self.qobj.data, dtype='d')
                    file[self.dataPath].attrs['Correction factor'] = self.attributes[0]
                    file[self.dataPath].attrs['Corrected channel'] = self.attributes[1]
                    file[self.dataPath].attrs['Number of data'] = self.attributes[2]
                    file[self.dataPath].attrs['Number of acquisitions'] = self.attributes[3]        
        self.signals.finish.emit()
                
######################################### Widget custom classes ###########################################        
        
        
        
class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        self.axes.set_facecolor('xkcd:black')
        self.axes.grid(visible=True, color='0.8', linewidth=0.3)
        super(MplCanvas, self).__init__(fig)
          
class Color(QWidget):   
    def __init__(self, C):
        super(Color, self).__init__()
        self.setAutoFillBackground(True)
        self.pal = self.palette()
        self.pal.setColor(QPalette.Window, C)
        self.setPalette(self.pal)
        
    def changeC(self, Col):
        self.pal.setColor(QPalette.Window, Col)
        self.setPalette(self.pal)

class Second(QMainWindow):
    def __init__(self, title, width, height, parent=None):
        super(Second, self).__init__()       
        self.setWindowTitle(title)
        self.setGeometry(10,50, width, height)
        
class GetWindow(QWidget):
    def __init__(self, toolbar, canvas, line, label):  
        super().__init__()
        
        self.toolbar = toolbar
        self.canvas = canvas
        self.line = line
        self.label = label
    
        self.LineLabel = QHBoxLayout()
        self.LineLabel.addWidget(self.label)
        self.LineLabel.addWidget(self.line)
        self.LineLabel.setAlignment(Qt.AlignLeft)
        self.LineLabel.addStretch(1)
        
        self.pointer = QVBoxLayout()
        self.pointer.addWidget(self.toolbar)
        self.pointer.addWidget(self.canvas)
        
        self.layout = QVBoxLayout()
        self.layout.addLayout(self.LineLabel)
        self.layout.addLayout(self.pointer)
        self.setLayout(self.layout)
    
    def refresh(self):
        self.pointer.removeWidget(self.toolbar)
        self.pointer.removeWidget(self.canvas)
        
        self.pointer.addWidget(self.toolbar)
        self.pointer.addWidget(self.canvas)
        
        
class FastWindow(QWidget):
    def __init__(self, toolbarS, canvasS, toolbarA, canvasA, pline, plabel, fbutton, Abutton, Cbutton):
        super().__init__()
        
        self.toolbarS = toolbarS
        self.toolbarA = toolbarA
        self.canvasS = canvasS
        self.canvasA = canvasA
        self.pline = pline
        self.plabel = plabel
        self.fbutton = fbutton
        self.Abutton = Abutton
        self.Cbutton = Cbutton
        
        self.hbox = QHBoxLayout()
        self.hbox.addWidget(self.plabel)
        self.hbox.addWidget(self.pline)
        self.hbox.addWidget(self.fbutton)
        self.hbox.addWidget(self.Abutton)
        self.hbox.addWidget(self.Cbutton)
        
        self.vbox = QVBoxLayout()
        self.vbox.addWidget(self.toolbarS)
        self.vbox.addWidget(self.canvasS)
        self.vbox.addWidget(self.toolbarA)
        self.vbox.addWidget(self.canvasA)
        
        self.layout = QVBoxLayout()
        self.layout.addLayout(self.hbox)
        self.layout.addLayout(self.vbox)
        self.setLayout(self.layout)
        
    def refresh(self):
        self.vbox.removeWidget(self.toolbarS)
        self.vbox.removeWidget(self.canvasS)
        self.vbox.removeWidget(self.toolbarA)
        self.vbox.removeWidget(self.canvasA)
        
        self.vbox.addWidget(self.toolbarS)
        self.vbox.addWidget(self.canvasS)
        self.vbox.addWidget(self.toolbarA)
        self.vbox.addWidget(self.canvasA)
      
        

#################################### Main window program ###########################################

class MainWindow(QMainWindow):
    
    def __init__(self):
        super().__init__() #when a Qt object is subclassed you always need to 
                           #call the super__init__() function 
        # set dimension of the window and title
        
#---------------------------------- Main Widget setup ---------------------------------------------#        
        self.setWindowTitle('TetrAMM')
        widthW = 400
        heightW = 450
        #self.setMaximumSize(widthW,heightW)
        #self.setFixedSize(widthW,heightW)
        self.setGeometry(10,50, widthW, heightW) 

        # Get function
                
        self.getON = QPushButton('Get on')
        self.getON.setFixedSize(110,20)
        self.getOFF = QPushButton('Get off')
        self.getOFF.setFixedSize(110,20)
        self.getClean = QPushButton('Clean memory')
        self.getClean.setFixedSize(110,20)
        
        self.getONCheck = False
        #self.getON.setCheckable(True) #set if the button is cheackable or not (default: not)
        self.getON.setStyleSheet('QPushButton {color: black; background-color : pink}')
        self.getON.clicked.connect(self.getONClicked)
        
        self.getOFFCheck = False
        #self.getOFF.setCheckable(True) #set if the button is cheackable or not (default: not)
        self.getOFF.setStyleSheet('QPushButton {color: black; background-color : purple}')
        self.getOFF.clicked.connect(self.getOFFClicked)
        
        self.getCleanCheck = False
        #self.getClean.setCheckable(True) #set if the button is cheackable or not (default: not)
        self.getClean.setStyleSheet('QPushButton {color: black; background-color : white}')
        self.getClean.clicked.connect(self.getCleanClicked)
        
        self.getLaTime = QLabel(self)
        self.getLaTime.setText('Timer[ms] (>500)')
        self.getTime = QLineEdit(self)
        self.getTime.setFixedSize(110,20)
        self.getTime.setPlaceholderText('Single shot')
        
        self.getLaSig = QLabel(self)
        self.getLaSig.setText('Show signal  ')
        self.getChSig = QCheckBox()
        self.getChSig.setChecked(True)
        self.getLaPoint = QLabel(self)
        self.getLaPoint.setText('Show pointer')
        self.getChPoint = QCheckBox()
        self.getChPoint.setChecked(True)
        
        self.getNDlabel = QLabel(self)
        self.getNDlabel.setText('Set averaged data')
        self.getNumberData = QLineEdit(self)
        self.getNumberData.setFixedSize(110,20)
        self.getNumberData.setPlaceholderText('Default 1')
        
        self.getSpinBox = QDoubleSpinBox()
        self.getSpinBox.setRange(0,20)
        self.getSpinBox.setDecimals(3)
        self.getSpinBox.setSingleStep(0.005)
        
        self.getSpinBox.valueChanged.connect(self.getSpinBoxValueChange)
        self.scalingFactor = 0
        self.scalingChannel = 0
        
        self.getComboBox = QComboBox()
        self.getComboBox.addItem('Signals')
        self.getComboBox.addItem('Sum signals')
        self.getComboBox.addItem('All')
        
        self.getComboBox.activated.connect(self.getComboActivated)
        self.getComboBox.currentTextChanged.connect(self.getComboTextChange)
        self.getComboBox.currentIndexChanged.connect(self.getComboIndexChange)
        
        self.getComboBoxChannel = QComboBox()
        self.getComboBoxChannel.setEditable(True)
        self.getComboBoxChannel.addItem('None')
        self.getComboBoxChannel.addItem('CH1')
        self.getComboBoxChannel.addItem('CH2')
        self.getComboBoxChannel.addItem('CH3')
        self.getComboBoxChannel.addItem('CH4')
        self.getComboBoxChannel.currentIndexChanged.connect(self.getComboSelectChannel)
        
        self.getPositionLine = QLineEdit(self)
        self.getPositionLine.setFixedSize(110,20)
        self.getPositionLine.setPlaceholderText('Sigmoid [um]')
                        
        getV1 = QVBoxLayout()
        getV1.addWidget(self.getON)
        getV1.addWidget(self.getOFF)
        getV1.addWidget(self.getClean)
        getV1.addWidget(self.getPositionLine)
        getV1.addStretch(1)
        getV1.setAlignment(Qt.AlignLeft)
        
        getH1 = QHBoxLayout()
        getH1.addWidget(self.getLaTime)
        getH1.addWidget(self.getTime)
        getH1.addStretch(1)
        getH1.setAlignment(Qt.AlignLeft)
        
        getH2 = QHBoxLayout()
        getH2.addWidget(self.getLaSig)
        getH2.addWidget(self.getChSig)
        getH2.addWidget(self.getLaPoint)
        getH2.addWidget(self.getChPoint)
        #getH2.addStretch(1)
        getH2.setAlignment(Qt.AlignLeft)
        
        getH4 = QHBoxLayout()
        getH4.addWidget(self.getNDlabel)
        getH4.addWidget(self.getNumberData)
        #getH3.addStretch(1)
        getH4.setAlignment(Qt.AlignLeft)
        
        getH3 = QHBoxLayout()
        getH3.addWidget(self.getSpinBox)
        getH3.addWidget(self.getComboBoxChannel)
        getH3.addWidget(self.getComboBox)
        #getH3.addStretch(1)
        getH3.setAlignment(Qt.AlignLeft)
        
        getV2 = QVBoxLayout()
        getV2.addLayout(getH1)
        getV2.addLayout(getH2)
        getV2.addLayout(getH4)
        getV2.addLayout(getH3)
        getV2.addStretch(1)
        
        GetBox = QHBoxLayout()
        GetBox.addLayout(getV1)
        GetBox.addLayout(getV2)
        GetBox.addStretch(1)
        
        #Pop-up window for Get
        
        self.canvasA = MplCanvas(self, width=6, height=4, dpi=100)
        self.toolbarA = NavigationToolbar(self.canvasA, self)
        self.xA = []
        self.yA = np.zeros((1,4))
        
        self.GsigLab = QLabel(self)
        self.GsigLab.setText('Plotting extream (0-100): ')
        self.GsigLin = QLineEdit(self)
        self.GsigLin.setFixedSize(110,20)
        
        self.canvasP = MplCanvas(self, width=5, height=5, dpi=100)
        self.toolbarP = NavigationToolbar(self.canvasP, self)
        self.xP = 0
        self.yP = 0
        
        self.pointLab = QLabel(self)
        self.pointLab.setText('Set number of averaged data: ')
        self.pointLin = QLineEdit(self)
        self.pointLin.setFixedSize(110,20)
        
        self.gcount = 0
        
        spacer1 = QHBoxLayout()
        spacerLab1 = QLabel(self)
        spacerLab1.setText('********************************************************')
        spacer1.addWidget(spacerLab1)
        spacer1.setAlignment(Qt.AlignCenter)
        
        
        #Acquisition
        
        self.acqON = QPushButton('Acq. ON')
        self.acqOFF = QPushButton('Acq. OFF')
        self.Trigger = QPushButton('Trigger')
        
        self.acqONCheck = False
        self.acqON.setStyleSheet('QPushButton {background-color : green}')
        self.acqON.clicked.connect(self.acqONClicked)                     
                             
        self.acqOFFCheck = False
        self.acqOFF.setStyleSheet('QPushButton {background-color : red}')
        self.acqOFF.clicked.connect(self.acqOFFClicked) 
        
        self.TriggerCheck = False
        self.Trigger.setStyleSheet('QPushButton {color: lightblue; background-color : brown}')
        self.Trigger.clicked.connect(self.TriggerClicked)
        
        self.LCDAcq = QLCDNumber()
        self.LCDAcq.setFixedSize(250,70)
        self.LCDAcq.setDigitCount(7)
        self.LCDlaAcq = QLabel(self)
        self.LCDlaAcq.setText('Number of acq. data')
        
        acqV1 = QVBoxLayout()
        acqV1.addWidget(self.acqON)
        acqV1.addWidget(self.acqOFF)
        acqV1.addWidget(self.Trigger)
        acqV1.addStretch(1)
        acqV1.setAlignment(Qt.AlignLeft)
        
        acqV2 = QVBoxLayout()
        acqV2.addWidget(self.LCDAcq)
        acqV2.addWidget(self.LCDlaAcq)
        acqV2.addStretch(1)
        acqV2.setAlignment(Qt.AlignCenter)
        
        AcqBox = QHBoxLayout()
        AcqBox.addLayout(acqV1)
        AcqBox.addLayout(acqV2)
        AcqBox.addStretch(1)
        AcqBox.setAlignment(Qt.AlignCenter)
        
        spacer2 = QHBoxLayout()
        spacerLab2 = QLabel(self)
        spacerLab2.setText('********************************************************')
        spacer2.addWidget(spacerLab2)
        spacer2.setAlignment(Qt.AlignCenter)
        
        self.acount = 0
        
        #Fast acquisition
        
        self.FastB = QPushButton('Fast acquisition')
        
        self.FastBCheck = False
        #self.FastB.setCheckable(True) #set if the button is cheackable or not (default: not)
        self.FastB.setStyleSheet('QPushButton {color: white; background-color : blue}')
        self.FastB.clicked.connect(self.FastBClicked)
        
        self.fastNla = QLabel(self)
        self.fastNla.setText('Pre-set: 1000')
        self.fastNli = QLineEdit(self)
        self.fastNli.setFixedSize(110,20)
        self.fastNli.setPlaceholderText('Num. of data')
        
        self.fastNacqLa = QLabel(self)
        self.fastNacqLa.setText('Pre-set:       1')
        self.fastNacqLi = QLineEdit(self)
        self.fastNacqLi.setFixedSize(110,20)
        self.fastNacqLi.setPlaceholderText('Num. of fast Acq.')
        
        fastV1 = QVBoxLayout()
        fastV1.addWidget(self.FastB)
        fastV1.addStretch(1)
        fastV1.setAlignment(Qt.AlignLeft)
        
        fastH1 = QHBoxLayout()
        fastH1.addWidget(self.fastNla)
        fastH1.addWidget(self.fastNli)
        fastH1.addStretch(1)
        fastH1.setAlignment(Qt.AlignLeft)
        
        fastH2 = QHBoxLayout()
        fastH2.addWidget(self.fastNacqLa)
        fastH2.addWidget(self.fastNacqLi)
        fastH2.addStretch(1)
        fastH2.setAlignment(Qt.AlignLeft)
        
        fastV2 = QVBoxLayout()
        fastV2.addLayout(fastH1)
        fastV2.addLayout(fastH2)
        fastV2.addStretch(1)
        fastV2.setAlignment(Qt.AlignLeft)
        
        FastBox = QHBoxLayout()
        FastBox.addLayout(fastV1)
        FastBox.addLayout(fastV2)
        FastBox.addStretch(1)
        FastBox.setAlignment(Qt.AlignLeft)
        
        #Fast Layout Pop-up window
        
        self.redraw = QPushButton('Redraw')
        self.fall = QPushButton('Draw all')
        self.fclean = QPushButton('Clear axes')
        
        self.fcleanCheck = False
        #self.fclean.setCheckable(True) #set if the button is cheackable or not (default: not)
        self.fclean.setStyleSheet('QPushButton {color: black; background-color : red}')
        self.fclean.clicked.connect(self.fcleanClicked)
        
        self.redrawCheck = False
        #self.redraw.setCheckable(True) #set if the button is cheackable or not (default: not)
        self.redraw.setStyleSheet('QPushButton {color: black; background-color : green}')
        self.redraw.clicked.connect(self.redrawClicked)
        
        self.fall.Check = False
        #self.fall.setCheckable(True) #set if the button is cheackable or not (default: not)
        self.fall.setStyleSheet('QPushButton {color: black; background-color : blue}')
        self.fall.clicked.connect(self.fallClicked)
        
        self.canvasS = MplCanvas(self, width=3, height=2, dpi=100)
        self.toolbarS = NavigationToolbar(self.canvasS, self)
        self.xS = []
        self.yS = np.zeros((1,4))
        self.k1S = 0
        self.k2S = 0
        
        self.canvasfftA = MplCanvas(self, width=3, height=2, dpi=100)
        self.toolbarfftA = NavigationToolbar(self.canvasfftA, self)
        self.xfftA = []
        self.yfftA = np.zeros((1,4))
        self.k1fftA = 0
        self.k2fftA = 0
        
        self.fcount = 0
        
        spacer3 = QHBoxLayout()
        spacerLab3 = QLabel(self)
        spacerLab3.setText('********************************************************')
        spacer3.addWidget(spacerLab3)
        spacer3.setAlignment(Qt.AlignCenter)
        
        #Open/Close buttons
        
        self.Open = QPushButton('Open connection')
        self.Close = QPushButton('Close connection')
        self.SaveSettings = QPushButton('Save settings')
        
        self.OpenCheck = False
        self.Open.setStyleSheet('QPushButton {color: green; background-color : gray}')
        self.Open.clicked.connect(self.OpenClicked)
        
        self.CloseCheck = False
        self.Close.setStyleSheet('QPushButton {color: red; background-color : gray}')
        self.Close.clicked.connect(self.CloseClicked)
        
        self.SaveSettingsCheck = False
        self.SaveSettings.setStyleSheet('QPushButton {color: black; background-color : gray}')
        self.SaveSettings.clicked.connect(self.SaveSettingsClicked)
        try:
            with open(r'TetrAMM_Data/Settings', 'r') as file:
                self.getTime.insert(str(int(file.readline()[16:-1])))
                self.scalingFactor = float(file.readline()[-6:-1])
                self.getSpinBox.setValue(self.scalingFactor)
                self.scalingChannel = int(file.readline()[-2])
                self.getComboBoxChannel.setCurrentIndex(self.scalingChannel+1)
                self.getComboBoxChannel.setCurrentText(str(file.readline()[24:-1]))
                self.getNumberData.insert(str(int(file.readline()[15:-1])))
                self.fastNli.insert(str(file.readline()[21:-1])) 
                self.fastNacqLi.insert(str(file.readline()[29:]))
        except:
            self.getTime.insert(str(0))
            self.scalingFactor = 0
            self.scalingChannel = -1
    
        self.fullPath = None
        self.dataPath = None
        
        conBox = QVBoxLayout()
        conBox.addWidget(self.Open)
        conBox.addWidget(self.Close)
        conBox.addWidget(self.SaveSettings)
        conBox.setAlignment(Qt.AlignRight)
         
        self.saveLabel = QLabel(self)
        self.saveLabel.setText('Save data (Y/N) ')
        self.saveCheckbox = QCheckBox()
        self.saveCheckbox.setChecked(True)
        saveHbox = QHBoxLayout()
        saveHbox.addWidget(self.saveLabel)
        saveHbox.addWidget(self.saveCheckbox)
        saveHbox.setAlignment(Qt.AlignLeft)
        
        self.expSaveLabel = QLabel(self)
        self.expSaveLabel.setText('EXPERIMENT NAME')
        self.expSaveLine = QLineEdit(self)
        self.expSaveLine.setFixedSize(110,20)
        self.expSaveLine.setPlaceholderText('EXPERIMENT')
        
        self.datasetSaveLabel = QLabel(self)
        self.datasetSaveLabel.setText('DATASET NAME')
        self.datasetSaveLine = QLineEdit(self)
        self.datasetSaveLine.setFixedSize(110,20)
        self.datasetSaveLine.setPlaceholderText('DATASET')
        
        saveVbox = QVBoxLayout()
        saveVbox.addWidget(self.expSaveLabel)
        saveVbox.addWidget(self.expSaveLine)
        saveVbox.addWidget(self.datasetSaveLabel)
        saveVbox.addWidget(self.datasetSaveLine)
        saveVbox.setAlignment(Qt.AlignLeft)
        
        saveBox = QVBoxLayout()
        saveBox.addLayout(saveHbox)
        saveBox.addLayout(saveVbox)
                           
        #Color Quadrant
        
        self.c1 = QColor()
        self.c1.setRgbF(1,0,0)
        self.c2 = QColor()
        self.c2.setRgbF(1,1,0)
        self.c3 = QColor()
        self.c3.setRgbF(0,0,1)
        self.c4 = QColor()
        self.c4.setRgbF(0,1,0)
        
        self.col1 = Color(self.c1)
        self.col2 = Color(self.c2)
        self.col3 = Color(self.c3)
        self.col4 = Color(self.c4)
        
        
        cv1box = QHBoxLayout()
        self.col1.setFixedSize(50,50)
        cv1box.addWidget(self.col1)
        self.col2.setFixedSize(50,50)
        cv1box.addWidget(self.col2)
        cv1box.setSpacing(1)
        cv2box = QHBoxLayout()
        self.col3.setFixedSize(50,50)
        cv2box.addWidget(self.col3)
        self.col4.setFixedSize(50,50)
        cv2box.addWidget(self.col4)
        cv2box.setSpacing(1)
        ColBox = QVBoxLayout()
        ColBox.addLayout(cv1box)
        ColBox.addLayout(cv2box)
        ColBox.setAlignment(Qt.AlignLeft)

        bottomBox =  QHBoxLayout()
        bottomBox.addLayout(saveBox)
        bottomBox.addLayout(ColBox)
        bottomBox.addLayout(conBox)

        box = QVBoxLayout()
        box.addLayout(GetBox)
        box.addLayout(spacer1)
        box.addLayout(AcqBox)
        box.addLayout(spacer2)
        box.addLayout(FastBox)
        box.addLayout(spacer3)
        box.addLayout(bottomBox)
        
        
        container = QWidget()
        container.setLayout(box)
      
        
        self.setCentralWidget(container)
        
  
 ########################################## Functions of MainWindow ######################################

#---------------------------------------- Worker & objects definitions -------------------------------------------#      

    def OpenClicked(self):
        #self.OpenCheck = self.Open.isChecked()
        #if self.OpenCheck == True:
        self.quad = TetrAMM.quad()
        self.getSpinBoxValueChange(self.scalingFactor)
        self.getComboSelectChannel(self.scalingChannel+1)
        self.count = 0
        self.TRG = False
        self.fbool = True
        self.debug = True
        self.freq = 0
        self.threadpool = QThreadPool()
        
 
 #-------------------------------------- Automatic acquisition routine -----------------------------------------#   

    def acqOFFClicked(self):
        self.workerAcq.stop()
        print('Acquisition stopped')
        self.acqON.setStyleSheet('QPushButton {background-color : green}')
        self.acqON.setEnabled(True)
        self.workerAcq = WorkerAcq(self.quad, self.LCDAcq, self.fullPath, self.dataPath, self.attributes)
        
    def acqONClicked(self):
    
        self.path = 'TetrAMM_Data/'
        if os.path.isfile(self.path+self.expSaveLine.text()):
            self.h5FileName = self.expSaveLine.text()+'.hdf5'
        else:
            if self.expSaveLine.text() == '':
                self.h5FileName = 'General_Data_Acquisition'+'.hdf5'
            else:
                self.h5FileName = self.expSaveLine.text()+'.hdf5'                
        self.fullPath = self.path+self.h5FileName
        
        if self.datasetSaveLine.text() == '':
             self.dataPath = 'Dataset'+str(self.acount)
        else:
            self.dataPath = self.datasetSaveLine.text()
        self.attributes = [self.scalingFactor, self.scalingChannel+1]
            
        self.workerAcq = WorkerAcq(self.quad, self.LCDAcq, self.fullPath, self.dataPath, self.attributes)    
        self.acqON.setStyleSheet('QPushButton {color : white; background-color : black}')
        self.acqON.setEnabled(False)
        self.workerAcq.signals.finish.connect(self.finishAcq)
        self.threadpool.start(self.workerAcq)
               
    def finishAcq(self):
        if  self.dataPath == 'Dataset'+str(self.acount):
            self.acount += 1 
        else:
            pass
      
    def TriggerClicked(self):
        if self.TRG:
            self.TRG = False
            self.Trigger.setStyleSheet('QPushButton {color : lightblue; background-color : brown}')
            try:
                self.workerAcq.TRG(False)
                print('Trigger OFF')
            except:
                print('OFF NAK')
        else:
            self.TRG = True
            self.Trigger.setStyleSheet('QPushButton {color : white; background-color : black}')
            try:
                self.workerAcq.TRG(True)
                print('Trigger ON')
            except:
                print('ON NAK')
        
        
        
    
    
#------------------------------------------- Fast acquisition routine -----------------------------------------#
              
    def FastBClicked(self):  
        
        if self.fastNacqLi.text() != '':
            self.Nacq = int(self.fastNacqLi.text())
        else:
            self.Nacq = 1
        if self.fastNli.text() != '':
            self.Ndata = int(self.fastNli.text())
        else: 
            self.Ndata = 1000
        
        if self.saveCheckbox.isChecked:
            self.path = 'TetrAMM_Data/'
            if os.path.isfile(self.path+self.expSaveLine.text()):
                self.h5FileName = self.expSaveLine.text()+'.hdf5'
            else:
                if self.expSaveLine.text() == '':
                    self.h5FileName = 'General_Data_Fast'+'.hdf5'
                else:
                    self.h5FileName = self.expSaveLine.text()+'.hdf5'                
            self.fullPath = self.path+self.h5FileName
            
            if self.datasetSaveLine.text() == '':
                 self.dataPath = 'Dataset'+str(self.fcount)
            else:
                self.dataPath = self.datasetSaveLine.text()
        self.attributes = [self.scalingFactor, self.scalingChannel+1, self.Ndata, self.Nacq]
        
        self.workerFast = WorkerFast(self.quad, self.fullPath, self.dataPath, self.attributes)
        self.workerFast.Ndata = self.Ndata
        self.workerFast.Nacq = self.Nacq
        
        self.FastB.setStyleSheet('QPushButton {color : white; background-color : blue}')
        self.quad.data = []
        
        self.workerFast.signals.finish.connect(self.finishFast)
        self.threadpool.start(self.workerFast)
        
        print('Fast acquisition done')
        self.workerFast = WorkerFast(self.quad, self.fullPath, self.dataPath, self.attributes)
        self.fplotLabel = QLabel(self)
        self.fplotline = QLineEdit(self)
        self.fplotline.setFixedSize(110,20)
        self.fplotline.setPlaceholderText('1st Acq shown')
    
        self.fastwin = FastWindow(self.toolbarS, self.canvasS, self.toolbarfftA, self.canvasfftA, self.fplotline, self.fplotLabel, self.redraw, self.fall, self.fclean)
        
        self.fClearCanv()
        self.fastwin.show()
            
        
    def finishFast(self):
        self.fcount += 1
        print('Fast acquisition routine completed')
        self.fastRfile()
        self.quad.data = np.array([])

        
    def fastRfile(self):        
        with h5py.File(self.fullPath,'r') as file:
            print(self.dataPath)
            self.loaddata = file[self.dataPath+'_'+str(0)][:,:]
            for ii in range(self.Nacq-1):
                self.loaddata = np.concatenate((self.loaddata,file[self.dataPath+'_'+str(ii+1)]), axis=0) 
        self.plotS()
        
    
    def plotS(self, NumAcq=0, k1=0, k2=0):
        k2 = self.Ndata-1
        self.xS = np.linspace(0, self.Ndata, self.Ndata)
        self.k1S = int(0)
        self.k2S = self.Ndata
        self.canvasS.axes.plot(self.xS[self.k1S:self.k2S], self.loaddata[(NumAcq*self.Ndata+self.k1S):(NumAcq*self.Ndata+self.k2S),0], 'b', \
                 self.xS[self.k1S:self.k2S],self.loaddata[(NumAcq*self.Ndata+self.k1S):(NumAcq*self.Ndata+self.k2S),1], 'y', \
                 self.xS[self.k1S:self.k2S],self.loaddata[(NumAcq*self.Ndata+self.k1S):(NumAcq*self.Ndata+self.k2S),2], 'g', \
                 self.xS[self.k1S:self.k2S],self.loaddata[(NumAcq*self.Ndata+self.k1S):(NumAcq*self.Ndata+self.k2S),3], 'r')
        self.canvasS.axes.set_xlabel('Number data')
        self.canvasS.axes.set_facecolor('xkcd:black')
        self.canvasS.axes.grid(visible=True, color='0.8', linewidth=0.3)
        self.canvasS.draw()
        
        
        [self.xfftA, self.yfftA] = self.quad.sfft(data=self.loaddata[(NumAcq*self.Ndata):((NumAcq+1)*self.Ndata),:])
        l = int(np.shape(self.xfftA)[0])
        if k1 < 10:
            k1 = 10
        self.k1fftA = int(k1*l/100000)
        self.k2fftA = int(k2*l/100000)
        M = np.max([np.max(abs(self.yfftA[self.k1fftA:self.k2fftA])), \
                    np.max(abs(self.yfftA[(l+self.k1fftA):(l+self.k2fftA)])), \
                    np.max(abs(self.yfftA[(2*l+self.k1fftA):(2*l+self.k2fftA)])), \
                    np.max(abs(self.yfftA[(3*l+self.k1fftA):(3*l+self.k2fftA)]))])
        self.canvasfftA.axes.plot(self.xfftA[self.k1fftA:self.k2fftA],abs(self.yfftA[self.k1fftA:self.k2fftA]/M),'b', \
                self.xfftA[self.k1fftA:self.k2fftA],abs(self.yfftA[(l+self.k1fftA):(l+self.k2fftA)]/M),'y', \
                self.xfftA[self.k1fftA:self.k2fftA],abs(self.yfftA[(2*l+self.k1fftA):(2*l+self.k2fftA)]/M),'g', \
                self.xfftA[self.k1fftA:self.k2fftA],abs(self.yfftA[(3*l+self.k1fftA):(3*l+self.k2fftA)]/M),'r') 
        self.canvasfftA.axes.set_xlabel('Frequency [Hz]')
        self.canvasfftA.axes.set_facecolor('xkcd:black')
        self.canvasfftA.axes.grid(visible=True, color='0.8', linewidth=0.3)
        self.canvasfftA.draw()
        
         
    def fClearCanv(self):
        self.canvasS.axes.cla()
        self.canvasS.axes.set_facecolor('xkcd:black')
        self.canvasS.axes.grid(visible=True, color='0.8', linewidth=0.3)
        self.canvasS.draw()
        self.canvasfftA.axes.cla()
        self.canvasfftA.axes.set_facecolor('xkcd:black')
        self.canvasfftA.axes.grid(visible=True, color='0.8', linewidth=0.3)
        self.canvasfftA.draw()
        
    def redrawClicked(self):
        a = int(self.fplotline.text())
        if a > self.Nacq:
            self.fplotline.setText('Not as many acquisitions')
        else:
            self.plotS(NumAcq=(a-1))
            self.fastwin.refresh()
   
    def fallClicked(self):        
        self.fClearCanv()
        for ii in range(self.Nacq):
            self.plotS(ii)
        self.fastwin.refresh()
            
    def fcleanClicked(self):
            self.fClearCanv()
            self.fastwin.refresh()
           
      
#----------------------------------------- Get acquisition routine -----------------------------------------#   
    def getONClicked(self):
        
        if self.getPositionLine.text() == '':
            umPosition = -1;
        else:
            umPosition = float(self.getPositionLine.text())
        
        if self.saveCheckbox.isChecked():
            self.path = 'TetrAMM_Data/'
            if os.path.isfile(self.path+self.expSaveLine.text()+'.hdf5'):
                
                self.h5FileName = self.expSaveLine.text()+'.hdf5'
            else:
                if self.expSaveLine.text() == '':
                    self.h5FileName = 'General_Data_Get'+'.hdf5'
                else:
                    self.h5FileName = self.expSaveLine.text()+'.hdf5'               
            self.fullPath = self.path+self.h5FileName
            
            if self.datasetSaveLine.text() == '':
                 self.dataPath = 'Dataset_'+str(self.gcount).zfill(3)
            else:
                self.dataPath = self.datasetSaveLine.text()+'_'++str(self.gcount).zfill(3)
            self.attributes = [int(self.getTime.text()), self.scalingFactor, self.scalingChannel+1, umPosition]
        else:
            self.fullPath = None
            self.dataPath = None
        
        if self.getChSig.isChecked():
            self.getwinS = GetWindow(self.toolbarA, self.canvasA, self.GsigLin, self.GsigLab)
            self.getwinS.show()
            
        if self.getChPoint.isChecked():
            self.getwinP = GetWindow(self.toolbarP, self.canvasP, self.pointLin, self.pointLab)
            self.getwinP.show()
            
        if self.getTime.text() == '' or int(self.getTime.text()) == 0:
            self.fbool = True
            self.workerGet = WorkerGet(self.quad, self.canvasA, self.canvasP, self.fullPath, self.dataPath, self.pointLin, self.GsigLin, self.getNumberData, self.getComboBox, self.attributes, self.fbool, self.debug, self.saveCheckbox, self.getChSig, self.getChPoint)
            self.workerGet.signals.finish.connect(self.finishGet)
            self.threadpool.start(self.workerGet)
            
        else:              
            x = int(self.getTime.text())
            if x < 500:
                self.getLaTime.setText('T > 500ms !')
                print('Invalid sampling time')
            else:
                self.getON.setStyleSheet('QPushButton {color : white; background-color : black}')
                self.getON.setEnabled(False)
                self.quad.data = np.array([])
                self.fbool = False
                self.freq = x
                self.timer = QTimer()
                self.timer.setInterval(self.freq)
                self.timer.timeout.connect(self.startQrun)
                self.timer.start()
                 
            
    def startQrun(self):
        #self.start_time = time.time()
        self.workerGet = WorkerGet(self.quad, self.canvasA, self.canvasP, self.fullPath, self.dataPath, self.pointLin, self.GsigLin, self.getNumberData, self.getComboBox, self.attributes, self.fbool, self.debug, self.saveCheckbox, self.getChSig, self.getChPoint)
        self.workerGet.signals.stop.connect(self.stopGet)
        self.workerGet.signals.finish.connect(self.finishGet)
        self.threadpool.start(self.workerGet)
            
    def stopGet(self):
        self.timer.stop() 

    def finishGet(self):
        pass
        
    def getOFFClicked(self):
        self.timer.stop()
        print('Get acquisition stopped')
        self.getON.setStyleSheet('QPushButton {background-color : pink}')
        self.getON.setEnabled(True)
        self.freq = 0
        if self.dataPath == 'Dataset'+str(self.gcount):
            self.gcount += 1
        self.workerGet = WorkerGet(self.quad, self.canvasA, self.canvasP, self.fullPath, self.dataPath, self.pointLin, self.GsigLin, self.getNumberData, self.getComboBox, self.attributes, self.fbool, self.debug, self.saveCheckbox, self.getChSig, self.getChPoint)
        self.quad.dacq = np.array([])
        
    def getCleanClicked(self):
        self.quad.dacq = []
        print('Data acquisition cleared')
        
    def getComboActivated(self, index):
        print('Activated index: ', index)
    
    def getComboTextChange(self, s):
        print('Text changed: ', s) 
        
    def getComboIndexChange(self, index):
        print('Index changed: ', index)
        
    def getComboSelectChannel(self, index):
        try:
            self.quad.sumChannel = index - 1
        except:
            pass
    def getSpinBoxValueChange(self, s):
        try:
            self.quad.sumScaling = round(s, 3)
        except:
            pass
#------------------------------------ Exit from Widget panel routine -----------------------------------------#
     
    def SaveSettingsClicked(self):
        self.file = open(r'TetrAMM_Data/Settings', 'w')
        self.file.write('Timer sampling: '+self.getTime.text()+'\n'\
                        'Sum scaling: '+str(self.quad.sumScaling)+'\n'\
                        'Corrected channel index: '+str(self.quad.sumChannel)+'\n'\
                        'Corrected channel text: '+self.getComboBoxChannel.currentText()+'\n'\
                        'Averaged data: '+self.getNumberData.text()+'\n'\
                        'Fast number of data: '+self.fastNli.text()+'\n'\
                        'Fast number of acquisitions: '+self.fastNacqLi.text())
        self.file.close()
        
    def CloseClicked(self):
        #self.CloseCheck = self.Close.isChecked()
        #if self.CloseCheck == True:
        win = QWidget()
        
        msgBox = QMessageBox(win)
        msgBox.setIcon(QMessageBox.Information)
        msgBox.setText('Save the data')
        msgBox.setStandardButtons(QMessageBox.Save | QMessageBox.Close)
        msgBox.buttonClicked.connect(mbc)
    
        returnvalue = msgBox.exec()
        if returnvalue == QMessageBox.Save:
            if self.quad.data == []:
                self.quad.close()
                print('No data to save - Connection closed')
            else:
                self.quad.Widfile('DATA_SAVED.txt')
                self.quad.close()
                print('Data saved - Connection closed')
        else:
            self.quad.close()
            print('Connection closed')
        win.show()
        
    
            
def mbc(i):
    pass
            

########################################### Main call function ############################################
        
def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    main = MainWindow()
    main.show()
    app.exec()
    
if __name__ == '__main__':
    main()



