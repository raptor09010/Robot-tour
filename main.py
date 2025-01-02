import coreV6
from time import sleep
from machine import Pin, freq, PWM
import machine

start_pin = Pin(8, Pin.IN, Pin.PULL_DOWN)
servo = PWM(machine.Pin(10))

servo.freq (50)
freq(200_000_000)
# 2_464 ticks per rev
#73.025mm * pi  = C(229.4148)
#141.3717 mm 90 deg
def servo_forward():
    servo.duty_u16(4770)
    sleep(0.5)
    
def servo_turn():
    servo.duty_u16(10000)
    sleep(0.5)

def mm(val):
    return int(val*2_464/229.4148)

def cm(val):
    return int(val*2_464/229.4148*10)

def m(val):
    return int(val*2_464/229.4148*100)

def wait(cm):
    travel_time = cm / 20
    sleep(travel_time)
    
x = 0
y = 0
def turn_right():
    global y
    global x
    servo_turn()
    y += cm(14.13717)
    x -= cm(14.13717)
    coreV6.m1set_pos(x)
    coreV6.m2set_pos(y)
    wait(14.13717)

def turn_left():
    global y
    global x
    servo_turn()
    y -= cm(14.13717)
    x += cm(14.13717)
    coreV6.m1set_pos(x)
    coreV6.m2set_pos(y)
    wait(14.13717)
    
def forward(dist):
    global y
    global x
    servo_forward()
    y += cm(dist)
    x += cm(dist)
    coreV6.m1set_pos(x)
    coreV6.m2set_pos(y)
    wait(dist)
    
def backwards(dist):
    global y
    global x
    servo_forward()
    y -= cm(dist)
    x -= cm(dist)
    coreV6.m1set_pos(x)
    coreV6.m2set_pos(y)
    wait(dist)
    
while True:
    
    if start_pin.value():
        coreV6.start()
        forward(100)
        turn_left()
        turn_left()
        forward(100)
        turn_left()
        turn_left()
    else:
        pass
