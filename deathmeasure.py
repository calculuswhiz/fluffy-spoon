from math import *
import sys, subprocess

def quadform(a, b, c):
    # Quadratic formula
    sqf = sqrt(b*b-4*a*c)
    return [(-b+sqf)/(2*a),(-b-sqf)/(2*a)]

def rad(angleD):
    return angleD*pi/180

def deg(angleR):
    return angleR*180/pi
    
def cot(theta):
    return 1/tan(theta)

def solve_tank(dx, dy, theta=None, v_0=None, w=0):
    # Earth:
    # gc = 8.865248226950355
    gc = 9.529745042492918
    wf = 0.08173443651742651
    if v_0 is None:
        theta=rad(theta)
        try:
            t = sqrt(2*(dx-dy*cot(theta))/(gc*cot(theta)+w*wf))
        except ValueError:
            theta=pi-theta
            print("Error found, reversing directions.", theta)
            t = sqrt(2*(dx-dy*cot(theta))/(gc*cot(theta)+w*wf))
        v_0 = (dy + gc*t*t/2)/(sin(theta)*t)
        return round(v_0,0)
    else:
        # Broken.
        # Non-algebraic solution. Guess to nearest 1/10th.
        # x,y
        mindiff = 999999
        holding = 0
        theta = 0
        errcheck = 0
        while theta<=90:
            t = quadform(gc/2, -v_0*sin(theta), dy)[0]
            diff_x = w*t**2/2 - (dx - v_0*cos(theta)*t)
            if diff_x**2 < mindiff**2:
                mindiff = diff_x
                holding = theta
                errcheck = t*v_0*sin(theta) - gc*t**2/2
            theta += .1
        print("Y-diff:", round(dy-errcheck, 3))
        return holding

# Input
wind = 0
theta = int(sys.argv[1])
v_0 = None

# Target:
params = sys.stdin.readline().split()
dx=int(params[0])
dy=int(params[1])

# print(solve_tank(dx, dy, theta, v_0, wind))
v_0 = solve_tank(dx, dy, theta, v_0, wind)
subprocess.call(["notify-send", str(v_0)])
