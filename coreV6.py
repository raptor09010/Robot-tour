from machine import Pin
from array import array
import rp2
import time
import machine
import _thread

m1pos = 0
m1pos_lock = _thread.allocate_lock()

m2pos = 0
m2pos_lock = _thread.allocate_lock()

def m1set_pos(value):
    global m1pos
    with m1pos_lock:
        m1pos = value

def m1get_pos():
    global m1pos
    with m1pos_lock:
        return m1pos
    
def m2set_pos(value):
    global m2pos
    with m2pos_lock:
        m2pos = value

def m2get_pos():
    global m2pos
    with m2pos_lock:
        return m2pos

def make_isr(pos):
    old_x = array("i", (0,))
    @micropython.viper
    def isr(sm):
        i = ptr32(pos)
        p = ptr32(old_x)
        while sm.rx_fifo():
            v: int = int(sm.get()) & 3
            x: int = v & 1
            y: int = v >> 1
            s: int = 1 if (x ^ y) else -1
            i[0] = i[0] + (s if (x ^ p[0]) else (0 - s))
            p[0] = x

    return isr

class Encoder:
    def __init__(self, sm_no, base_pin, scale=1):
        self.scale = scale
        self._pos = array("i", (0,))  # [pos]
        self.sm = rp2.StateMachine(sm_no, self.pio_quadrature, in_base=base_pin)
        self.sm.irq(make_isr(self._pos))  # Instantiate the closure
        self.sm.exec("set(y, 99)")  # Initialise y: guarantee different to the input
        self.sm.active(1)

    @rp2.asm_pio()
    def pio_quadrature(in_init=rp2.PIO.IN_LOW):
        wrap_target()
        label("again")
        in_(pins, 2)
        mov(x, isr)
        jmp(x_not_y, "push_data")
        mov(isr, null)
        jmp("again")
        label("push_data")
        push()
        irq(block, rel(0))
        mov(y, x)
        wrap()

    def position(self, value=None):
        if value is not None:
            self._pos[0] = round(value / self.scale)
        return self._pos[0] * self.scale

    def value(self, value=None):
        if value is not None:
            self._pos[0] = value
        return self._pos[0]
    

@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
def step():
    wrap_target()
    pull()                  
    set(pins, 1)         
    set(x, 31)          
    label("d")
    nop() [31]
    nop() [31]
    nop() [31]
    nop() [31]
    nop() [31]
    nop() [31]
    nop() [31]
    nop() [31]
    nop() [31]
    nop() [31]
    nop() [31]
    nop() [31]
    nop() [31]
    nop() [31]
    nop() [31]
    jmp(x_dec, "d")
    set(pins, 0)           
    wrap()

m1_f = rp2.StateMachine(0, step, set_base=Pin(20))
m1_b = rp2.StateMachine(1, step, set_base=Pin(19))

m2_f = rp2.StateMachine(2, step, set_base=Pin(21))
m2_b = rp2.StateMachine(3, step, set_base=Pin(26))

m1_f.active(1)
m1_b.active(1)
m2_f.active(1)
m2_b.active(1)

M1_Encoder = Encoder(4, Pin(11))
M2_Encoder = Encoder(5, Pin(4))
# 2464 ticks per rev
M1_Enc = M1_Encoder.value() 
M2_Enc = M2_Encoder.value() 

def motor_pos():
    while True:
        global m1pos
        global m2pos
        global M1_Enc
        global M2_Enc
        m1_diff = abs(M1_Enc - m1pos)
        m2_diff = abs(M2_Enc - m2pos)
        M1_Enc = M1_Encoder.value()
        M2_Enc = M2_Encoder.value()
        if m1_diff >= m2_diff:
            if M1_Enc < m1pos:
                m1_f.put(1)
            
            elif M1_Enc > m1pos:
                m1_b.put(1)
                
        if m2_diff >= m1_diff:
            if M2_Enc < m2pos:
                m2_f.put(1)
            
            elif M2_Enc > m2pos:
                m2_b.put(1)
                
        time.sleep_us(1)
def start():
    _thread.start_new_thread(motor_pos, ())
    
