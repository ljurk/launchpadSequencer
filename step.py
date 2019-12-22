from colors import Colors
from mido import Message



class Step():
    """
    class with all informations of a step
    """
    note = None
    led = None
    value = Colors.YELLOW
    velocity = 16
    cc = []
    ccPitch = None
    ccVelo = None
    launchOut = None
    colors = {}
    colors['on'] = Colors.RED_LOW
    colors['off'] = Colors.YELLOW
    active = False

    def __init__(self, note, led, ccPitch, ccVelo, outport, cc, val, value=Colors.YELLOW):
        self.launchOut = outport
        self.note = note
        self.led = led
        self.ccVelo = ccVelo
        self.ccPitch = ccPitch
        self.value = value
        if value == Colors.RED_LOW:
            self.active = True

        self.cc = []
        ccs = {}
        ccs['cc'] = cc
        ccs['value'] = val
        self.cc.append(ccs)

    def addCc(self, cc, value):
        ccs = {}
        ccs['cc'] = cc
        ccs['value'] = value
        self.cc.append(ccs)

    def litup(self, value=None):
        if not value:
            value = self.value
        template = 8
        msg = Message(type='sysex',
                      data=[0, 32, 41, 2, 10, 120,
                            template, self.led, value])
        self.launchOut.send(msg)
