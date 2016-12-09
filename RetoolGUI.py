#!/usr/bin/python3
# -*- coding: utf-8 -*-
from macromanx import Mouse, Keyboard, Winman, Aux

import sys
from subprocess import call, Popen, PIPE
from math import *
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (QWidget, QApplication,
        QGridLayout, QMainWindow, QStatusBar,
        QLabel, QButtonGroup, QPushButton, QRadioButton, QLineEdit, QSpinBox)

import GUIv2

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

'''
Bonus to Gameconquerors:
See PowerAngleCircle.as for reference. Allow first turn shot display:
::push bunch of properties; pushbyte 0; ifne ofs0056;
07 28 90 24 00 14 10 00 00
turn -1?
07 28 90 24 ff 14 10 00 00
'''
class MW(QMainWindow, GUIv2.Ui_MainWindow):
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

        self.recalc_btn.clicked.connect(self.solve_tank)
        self.flipwind_btn.clicked.connect(self.invert)
        self.self_btn.clicked.connect(self.findself)
        self.target_btn.clicked.connect(self.findtarget)

    def findself(self):
        mouseno = Aux.getdevicelist("Logitech")[0][0]
        if not mouseno:
            print("Device error:")
            sys.exit(-1)

        Mouse.clickwait(mouseno, 1)
        x, y = Mouse.getmousepos()
        self.selfxbox.setValue(x)
        self.selfybox.setValue(y)
        self.changeACK()

    def findtarget(self):
        mouseno = Aux.getdevicelist("Logitech")[0][0]
        if not mouseno:
            print("Device error:")
            sys.exit(-1)

        Mouse.clickwait(mouseno, 1)
        x, y = Mouse.getmousepos()
        self.targetxbox.setValue(x)
        self.targetybox.setValue(y)
        self.changeACK()

    def changeACK(self):
        Winman.focuson("Aim Assistant v2")
        self.wbox.setValue(self.targetxbox.value() - self.selfxbox.value())
        self.hbox.setValue(self.selfybox.value() - self.targetybox.value())
        self.solve_tank()

    def getclickloc(self):
        pass

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
            if(vat > 100 or diff > 5):
                catstr = "!"
            self.vbox.setText(catstr + str(round(vat,0))+","+str(round(diff,1))+"px" + catstr)
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
    app = QApplication(sys.argv)
    Mainwin = MW()
    Mainwin.show()
    sys.exit(app.exec_())
