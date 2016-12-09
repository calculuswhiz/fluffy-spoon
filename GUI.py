#!/usr/bin/python3
# -*- coding: utf-8 -*-
from macromanx import Mouse

import sys
from subprocess import call, Popen, PIPE
from math import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (QWidget, QApplication,
        QGridLayout, QMainWindow, QStatusBar,
        QLabel, QButtonGroup, QPushButton, QRadioButton, QLineEdit, QSpinBox)

'''
Bonus to Gameconquerors:
See PowerAngleCircle.as for reference. Allow first turn shot display:
::push bunch of properties; pushbyte 0; ifne ofs0056;
07 28 90 24 00 14 10 00 00
turn -1?
07 28 90 24 ff 14 10 00 00
'''

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

class MW(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initwin()
        self.assistant = AimAssist()
        self.setCentralWidget(self.assistant)
        self.show()
        
    def initwin(self):
        # First turn estimator:
        ftemap = QPixmap("./estimator.png")
        ftelabel = QLabel()
        ftelabel.setPixmap(ftemap)
        self.statusBar().addWidget(ftelabel)
        ftelabel.setAlignment(Qt.AlignBottom)
        
        self.move(50, 50)
        # self.setWindowFlags(Qt.FramelessWindowHint)
        self.setWindowTitle('Aim Assistant')
        
    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape or e.key() == Qt.Key_Q:
            self.close()

class AimAssist(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):    
        # Buttons:
        BTN_H = 20
        BTN_W = 80
        BUTTON_COL = 0
        LABEL_COL1 = 1
        DATA_COL = 2
        RADIO_COL = 3
        
        grid = QGridLayout()
        self.setLayout(grid)
        
        # Buttons:
        acq = QPushButton("&ACK", self)
        acq.clicked.connect(self.drawRect)
        grid.addWidget(acq, 0, BUTTON_COL)
        calc = QPushButton("&Calc", self)
        calc.clicked.connect(self.solve_tank)
        grid.addWidget(calc, 1, BUTTON_COL)
        rstb = QPushButton("&Invert", self)
        rstb.clicked.connect(self.invert)
        grid.addWidget(rstb, 2, BUTTON_COL)
        
        # Radio buttons:
        settings = QLabel("Shot Type:")
        grid.addWidget(settings, 0, RADIO_COL)
        # settings.setAlignment(Qt.AlignBottom)
        self.radNorm = QRadioButton("&Normal")
        self.radNorm.setChecked(True)
        grid.addWidget(self.radNorm, 1, RADIO_COL)
        self.radHover = QRadioButton("&Hover (Post hang only)")
        grid.addWidget(self.radHover, 2, RADIO_COL)
        self.radDig = QRadioButton("&Tunneler")
        grid.addWidget(self.radDig, 3, RADIO_COL)
        self.radBoom = QRadioButton("&Boomerang")
        grid.addWidget(self.radBoom, 4, RADIO_COL)
        
        # Text areas (with labels):
        # Width
        self.wbox = QSpinBox(self)
        grid.addWidget(self.wbox, 0, DATA_COL)
        self.wbox.setMaximum(1000)
        self.wbox.setMinimum(-1000)
        wlabel = QLabel("Width:")
        grid.addWidget(wlabel, 0, LABEL_COL1)
        wlabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        # Height
        self.hbox = QSpinBox(self)
        grid.addWidget(self.hbox, 1, DATA_COL)
        self.hbox.setMaximum(1000)
        self.hbox.setMinimum(-1000)
        hlabel = QLabel("Height:")
        grid.addWidget(hlabel, 1, LABEL_COL1)
        hlabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        # Wind
        self.windbox = QSpinBox(self)
        grid.addWidget(self.windbox, 2, DATA_COL)
        self.windbox.setMaximum(30)
        self.windbox.setMinimum(-30)
        windlabel = QLabel("Wind:")
        grid.addWidget(windlabel, 2, LABEL_COL1)
        windlabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        # Angle
        self.anglebox = QSpinBox(self)
        grid.addWidget(self.anglebox, 3, DATA_COL)
        self.anglebox.setMaximum(359)
        self.anglebox.setMinimum(0)
        self.anglebox.setValue(45)
        self.anglebox.setSingleStep(1)
        self.anglebox.setWrapping(True)
        angleLabel = QLabel("<i>θ</i>(0-359):")
        grid.addWidget(angleLabel, 3, LABEL_COL1)
        angleLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        # Power out:
        self.vbox = QLineEdit("Power")
        self.vbox.setStyleSheet("color: #ff0000")
        grid.addWidget(self.vbox, 4, BUTTON_COL)
        self.vbox.setAlignment(Qt.AlignRight)
        self.vbox.setReadOnly(True)
        
        self.show()
        
    def setWH(self, rectw, recth):
        self.wbox.setValue(int(rectw))
        self.hbox.setValue(int(recth))
        self.solve_tank()
        
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

        # Earth:
        gc = 9.529745042492918
        wf = 0.08173443651742651    # wind
        # hover:
        hc = 3.660218073939021*int(self.radHover.isChecked())
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
        # hang = int(self.radHover.isChecked())
            
        flags = ""
        
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
        
        # self.radNorm.setChecked(True)
        
if __name__ == '__main__':
    # gcproc = Popen(["gameconqueror"])
    # call(["gameconqueror"])
    app = QApplication(sys.argv)
    Mainwin = MW()
    sys.exit(app.exec_())
