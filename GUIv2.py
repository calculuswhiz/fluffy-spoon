#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
from subprocess import call, Popen, PIPE
from math import *
from PyQt5 import uic, QtCore
from PyQt5.QtCore import Qt, QObject, pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (QWidget, QApplication,
        QGridLayout, QMainWindow, QStatusBar, QTableWidgetItem,
        QLabel, QButtonGroup, QPushButton, QRadioButton, QLineEdit, QSpinBox)

import Xlib

import RetoolGUI

def rad(angleD):
    return angleD*pi/180

def deg(angleR):
    return angleR*180/pi

def cot(theta):
    return 1/tan(theta)

def quadform(a, b, c):
    # Quadratic formula
    rad = b*b-4*a*c
    if rad<0 or a==0:
        return [-1, -1]
    sqf = sqrt(rad)
    return [(-b+sqf)/(2*a),(-b-sqf)/(2*a)]

# pyuic5 RetoolGUI.ui -o GUIv2.py

'''
Bonus to Gameconquerors:
See PowerAngleCircle.as for reference. Allow first turn shot display:
::push bunch of properties; pushbyte 0; ifne ofs0056;
07 28 90 24 00 14 10 00 00
turn -1?
07 28 90 24 aa 14 10 00 00
'''

class MW(QMainWindow, RetoolGUI.Ui_MainWindow):
    def __init__(self, parent=None):
        super(MW, self).__init__(parent)
        self.setupUi(self)
        self.initwin()

    def initwin(self):
        # First turn estimator:
        ftemap = QPixmap("./estimator.png")
        ftelabel = QLabel()
        ftelabel.setPixmap(ftemap)
        self.statusBar().addWidget(ftelabel)
        ftelabel.setAlignment(Qt.AlignBottom)
        
        self.move(50, 50)

        self.acq_btn.clicked.connect(self.drawRect)
        self.calc_btn.clicked.connect(self.solve_tank)
        self.flipwind_btn.clicked.connect(self.invert)
        self.bytesline.mouseReleaseEvent = self.cheatselect
        self.bytesline.mouseDoubleClickEvent = self.cheatcopy
        self.v1ack_btn.clicked.connect(self.drawRectv1)
        self.openGC.clicked.connect(self.openGameConqueror)
        
    def openGameConqueror(self):
        gcproc = Popen(["gameconqueror"])
        
    def cheatselect(self, e):
        self.bytesline.selectAll()
        
    def cheatcopy(self, e):
        self.bytesline.copy()
        call(["notify-send", "Copied"])
        
    def setWHv1(self, rectw, recth):
        self.wbox.setValue(int(rectw))
        self.hbox.setValue(int(recth))
        self.v1Solver()
        
    def setWH(self, rectw, recth):
        self.wbox.setValue(int(rectw))
        self.hbox.setValue(int(recth))
        self.solve_tank()
    
    def drawRectv1(self):
        self.lower()
        pair = Popen(["./deathmeasure"], stdout=PIPE).communicate()[0].decode('utf-8').split()
        self.setWHv1(pair[0], pair[1])
    
    def drawRect(self):
        self.lower()
        pair = Popen(["./deathmeasure"], stdout=PIPE).communicate()[0].decode('utf-8').split()
        self.setWH(pair[0], pair[1])

    def invert(self):
        # self.radNorm.setChecked(True)
        self.windbox.setValue(-self.windbox.value())

    def solve_tank(self):
        # Sanity check.
        shotstring=""
        
        self.calcTable.setSortingEnabled(False)

        # Earth:
        gc = 9.529745042492918
        wf = 0.08173443651742651    # wind
        # hover:
        if(self.radHover.isChecked()):
            hc = 3.660218073939021
        else:
            hc = 7.313616408030493*int(self.radBigHover.isChecked())
        
        if(hc!=0):
            shotstring = "(HOVER)"
        # boomer:
        bc = 0.07690605021520115*int(self.radBoom.isChecked())
        if(bc!=0):
            shotstring = "(BOOMERANG)"
        
        v_0 = None
        

        dx = self.wbox.value()
        dy = self.hbox.value()
        barrel = 14
        # barrel = self.anglebox.value()
        w = self.windbox.value()
        # hang = int(self.radHover.isChecked())
        
        if self.radDig.isChecked():
            # dy = -dy
            pass
        
        # Solve these equations:
        # x=v_0*cos(theta)*t
        # Other x terms:
        #   Hover:     hc*v_0*cos(theta)
        #   Wind:      .5*wf*w*(t**2)
        #   Boomer:    -.5*bc*v_0*cos(theta)*(t**2)
            
        # y=v_0*sin(theta)*t-1/2*gc*(t**2)
        pairlist=[]
        # barrel = 15
        for theta in range(0,360):
            inversion = 1
            if self.radDig.isChecked():
                theta = -theta+360
                dy = -self.hbox.value()
                inversion = -2
        
            theta = rad(theta)
            if v_0 is None:
                diffx = 20
                vat = -1
                for n in range(1,101):
                    t = quadform(gc/2, -n*sin(theta), (dy - barrel *sin(theta)))[0]
                    x = n*cos(theta)*t + .5*wf*w*t**2 + hc*n*cos(theta) - .5*bc*n*cos(theta)*t**2
                    # print(fabs(x-dx))
                    # if fabs(x-(dx)) < fabs(diffx):
                    if fabs(x-(dx - barrel * cos(theta))) < fabs(diffx):
                        # Debug:
                        # print(str(n)+":\t", round(x), round(dx), round(fabs(dx-x)))
                        # diffx = (dx) -x
                        diffx = (dx - barrel * cos(theta) ) -x
                        vat = n
                
                theta = deg(theta)
                if self.radDig.isChecked():
                    theta = -theta+360
                
                if(fabs(diffx)<5.0):
                    # print(theta)
                    pairlist.append((fabs(diffx), vat, theta))
            else:
                print("Error. Broken.")
                self.vbox.setText(str(-1.0))
        pairlist.sort()
        self.calcTable.setRowCount(len(pairlist))
        for i in range(0, len(pairlist)):
            self.calcTable.setItem(i, 0, QTableWidgetItem(str(round(pairlist[i][1],0))))
            self.calcTable.setItem(i, 1, QTableWidgetItem(str(round(pairlist[i][2],0))))
            self.calcTable.setItem(i, 2, QTableWidgetItem(str(round(pairlist[i][0],1))))
            # print (pairlist[i])
        self.calcTable.setSortingEnabled(True)
        self.raise_()
        # self.activateWindow()
            
    def v1Solver(self):
        # Sanity check.
        shotstring=""

        # Earth:
        gc = 9.529745042492918
        wf = 0.08173443651742651    # wind
        # hover:
        if(self.radHover.isChecked()):
            hc = 3.660218073939021
        else:
            hc = 7.313616408030493*int(self.radBigHover.isChecked())
        if(hc!=0):
            shotstring = "(HOVER)"
        # boomer:
        bc = 0.07690605021520115*int(self.radBoom.isChecked())
        if(bc!=0):
            shotstring = "(BOOMERANG)"
        
        v_0 = None
        

        dx = self.wbox.value()
        dy = self.hbox.value()
        theta = self.anglebox.value()
        if self.radDig.isChecked():
            theta = -theta+360
            dy = -dy
            shotstring="(TUNNELER)"
        theta = rad(theta)
        w = self.windbox.value()
        
        # Solve these equations:
        # x=v_0*cos(theta)*t
        # Other x terms:
        #   Hover:     hc*v_0*cos(theta)
        #   Wind:      .5*wf*w*(t**2)
        #   Boomer:    -.5*bc*v_0*cos(theta)*(t**2)
        
        # y=v_0*sin(theta)*t-1/2*gc*(t**2)
        if v_0 is None:
            diff = 20
            vat = -1
            for n in range(1,111):
                t = quadform(gc/2, -n*sin(theta), dy)[0]
                # if t<0:
                #     continue
                x = n*cos(theta)*t + .5*wf*w*t**2 + hc*n*cos(theta) - .5*bc*n*cos(theta)*t**2
                # print(fabs(x-dx))
                if fabs(x-dx) < fabs(diff):
                    # Debug:
                    # print(str(n)+":\t", round(x), round(dx), round(fabs(dx-x)))
                    diff = dx-x
                    vat = n
            catstr = ""
            if(vat > 100):
                catstr = "!"
            self.vbox.setText(str(round(vat,0))+catstr+","+str(round(diff,1))+"px")
            if vat<0:
                call(["notify-send", "Error:", "Bad Value"])
            else:
                call(["notify-send", "Power:", str(round(vat,0))+catstr+" "+shotstring])
                
        else:
            print("Error. Broken.")
            self.vbox.setText(str(-1.0))
            
    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape or e.key() == Qt.Key_Q:
            self.close()

if __name__ == '__main__':
    # call(["gameconqueror"])
    app = QApplication(sys.argv)
    Mainwin = MW()
    Mainwin.show()
    
    sys.exit(app.exec_())
