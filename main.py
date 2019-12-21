from __future__ import print_function
from luma.led_matrix.device import max7219
from luma.core.interface.serial import spi, noop
from luma.core.render import canvas
from luma.core.virtual import viewport
from luma.core.legacy import text, show_message
from luma.core.legacy.font import proportional, CP437_FONT, TINY_FONT, SINCLAIR_FONT, LCD_FONT
import mido
from mido import Message
import re
import time
import argparse

OFF = 0
RED_LOW = 13
RED_MEDIUM = 14
RED_HIGH = 15
AMBER_LOW = 29
AMBER_HIGH = 63
YELLOW = 62
GREEN_LOW = 28
GREEN_HIGH = 60


class step():
    """
    class with all informations of a step
    """
    note = None
    led = None
    value = YELLOW
    velocity = 16
    cc = []
    ccPitch = None
    ccVelo = None
    launchOut = None
    colors = {}
    colors['on'] = RED_LOW
    colors['off'] = YELLOW
    active = False

    def __init__(self, note, led, ccPitch, ccVelo, outport, cc, val, value=YELLOW):
        self.launchOut = outport
        self.note = note
        self.led = led
        self.ccVelo = ccVelo
        self.ccPitch = ccPitch
        self.value = value
        if value == RED_LOW:
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

class sequencer():
    """
    class with all informations of a sequence
    """
    sequence = []
    #ports
    launchpad = {}
    interface = {}
    started = False
    channel = 0
    activeStep = 0
    note = None
    name = None
    silent = True

    def nextStep(self):
        print("next" + str(self.sequence[self.activeStep].active))
        if self.sequence[self.activeStep].active: # on
            print("off" +
                  str(self.activeStep) +
                  "[" +
                  str(self.sequence[self.activeStep].velocity) +
                  "]")
            msg = Message('note_off',
                          note=self.note,
                          channel=self.channel)#,
                          #velocity=self.sequence[activeStep].velocity)
            self.interface['out'].send(msg)
        if not self.silent:
            self.sequence[self.activeStep].litup()
        if self.activeStep != 7:
            self.activeStep += 1
        else:
            self.activeStep = 0

        if self.sequence[self.activeStep].active:
            for cc in self.sequence[self.activeStep].cc:
                print("send" + str(cc['value']))
                ccMsg = Message('control_change',
                                channel=self.channel,
                                control=cc['cc'],
                                value=cc['value'])
                self.interface['out'].send(ccMsg)

            print("on" +
                  str(self.activeStep) +
                  "[" +
                  str(self.note) +
                  "]")
            msg = Message('note_on',
                          note=self.note,
                          channel=self.channel,
                          velocity=self.sequence[self.activeStep].velocity)
            self.interface['out'].send(msg)

        if not self.silent:
            self.sequence[self.activeStep].litup(GREEN_LOW)

    def prevStep(self, activeStep):
        self.sequence[activeStep].litup()
        if activeStep != 0:
            activeStep -= 1
        else:
            activeStep = 7
        self.sequence[activeStep].litup(GREEN_LOW)
        return activeStep

    def __init__(self, note, name, launchpadPorts, interfacePorts, silent):
        print("init")
        self.launchpad = launchpadPorts
        self.interface = interfacePorts
        self.note = note
        self.name = name
        self.silent = silent
        self.sequence = []
        cc = 102
        val = 60
        if note == 36:
            self.sequence.append(step(9, 0, 41, 21, self.launchpad['out'], cc, val, RED_LOW))
            self.sequence.append(step(10, 1, 42, 22, self.launchpad['out'], cc, val))
            self.sequence.append(step(11, 2, 43, 23, self.launchpad['out'], cc, val, RED_LOW))
            cc = 103
            self.sequence.append(step(12, 3, 44, 24, self.launchpad['out'], cc, val))
            self.sequence.append(step(25, 4, 45, 25, self.launchpad['out'], cc, val, RED_LOW))
            self.sequence.append(step(26, 5, 46, 26, self.launchpad['out'], cc, val))
            self.sequence.append(step(27, 6, 47, 27, self.launchpad['out'], cc, val, RED_LOW))
            self.sequence.append(step(28, 7, 48, 28, self.launchpad['out'], cc, val))
            self.sequence[7].addCc(33,55)
        else:
            self.sequence.append(step(9, 0, 41, 21, self.launchpad['out'], cc, val))
            self.sequence.append(step(10, 1, 42, 22, self.launchpad['out'], cc, val))
            self.sequence.append(step(11, 2, 43, 23, self.launchpad['out'], cc, val))
            self.sequence.append(step(12, 3, 44, 24, self.launchpad['out'], cc, val))
            self.sequence.append(step(25, 4, 45, 25, self.launchpad['out'], cc, val))
            self.sequence.append(step(26, 5, 46, 26, self.launchpad['out'], cc, val))
            self.sequence.append(step(27, 6, 47, 27, self.launchpad['out'], cc, val))
            self.sequence.append(step(28, 7, 48, 28, self.launchpad['out'], cc, val))


    def run(self, silent=False):
        self.silent = silent
        #self.checkClock()
        #self.checkControls()

class ui():
    sequences = None
    active = 0
    #ports
    launchpad = {}
    interface = {}
    started = False
    clockDivider = 11
    clockCount = 0
    device = None
    def __init__(self, debug):
        serial = spi(port=0, device=0, gpio=noop())
        self.device = max7219(serial,
                              cascaded=2,
                              rotate=1)
        print("Created device")
        self.printMsg("ESID", font=TINY_FONT)
        if debug:
            self.interface['in'] = mido.open_input()
            self.interface['out'] = mido.open_output()
            inputPort = "Launch Control MIDI 1"
            self.launchpad['in'] = mido.open_input(inputPort)
            self.launchpad['out'] = mido.open_output(inputPort)
        else:
            inputPort = "Launch Control MIDI 1"
            clockPort = "Elektron Digitakt MIDI 1"
            #clockPort = None
            #outputPort = None
            outputPort = "USB MIDI Interface:USB MIDI Interface MIDI 1"
            self.launchpad['in'] = mido.open_input(inputPort)
            self.launchpad['out'] = mido.open_output(inputPort)
            self.interface['in'] = mido.open_input(clockPort)
            self.interface['out'] = mido.open_output(outputPort)
        self.sequences = []
        self.sequences.append(sequencer(36,
                                        "KK",
                                        self.launchpad,
                                        self.interface,
                                        silent=False))
        self.sequences.append(sequencer(46,
                                        "SD",
                                        self.launchpad,
                                        self.interface,
                                        silent=True))
        self.sequences.append(sequencer(44,
                                        "OH",
                                        self.launchpad,
                                        self.interface,
                                        silent=True))
        self.sequences.append(sequencer(39,
                                        "CP",
                                        self.launchpad,
                                        self.interface,
                                        silent=True))

    def printMsg(self, txt, font=LCD_FONT, moving=False):
        virtual = viewport(self.device, width=self.device.width, height=self.device.height*2)
        print(len(txt))
        margin = 8
        marginY = 0
        margins = []
        if font == TINY_FONT:
            margins.append([0,0])
            margins.append([4,0])
            margins.append([0,8])
            margins.append([4,8])
        else:
            margins.append([0,0])
            margins.append([0,8])
        if font == TINY_FONT:
            marginY =4
            margin = 0
        with canvas(virtual) as draw:
            for i, word in enumerate(txt):
                text(draw, (margins[i][0], margins[i][1]), word, fill="white", font=proportional(font))
        if moving:
            print("move")
            for i in range(virtual.height - self.device.height):
                print(i)
                virtual.set_position((0, i))
                time.sleep(0.5)
        else:
            virtual.set_position((0, 0))



    def showIndicator(self):
        for i in range(0,4):
            self.litup(i + 8, OFF)
        self.litup(self.active + 8, RED_LOW)

    def printSilent(self):
        i = 0
        for seq in self.sequences:
            print(i)
            print(seq.silent)
            i += 1
        print("_________________")

    def stopHandler(self):
        self.interface['out'].reset()
        self.started = False
        for seq in self.sequences:
            seq.started = False
            if not seq.silent:
                #set color of last active step
                seq.sequence[seq.activeStep].litup(YELLOW)
            seq.activeStep = 0
            if not seq.silent:
                seq.sequence[0].litup(GREEN_LOW)

    def clockHandler(self):
        self.printSilent()
        for seq in self.sequences:
            seq.nextStep()

    def checkClock(self):
        for msg in self.interface['in'].iter_pending():
            if msg.type == "start":
                print('START')
                self.started = True
            if msg.type == "stop":
                print('STOP')
                self.stopHandler()

            if msg.type == "clock" and self.started:
                if self.clockCount == self.clockDivider:
                    self.clockHandler()
                    self.clockCount = 0
                else:
                    self.clockCount += 1
    def printSeq(self):
        for seq in self.sequences:
            print(seq.note)
            for step in seq.sequence:
                print("[" + str(step.value) + "]", end='')
            print("S")

    def reloadSequence(self):
        for step in self.sequences[self.active].sequence:
            step.litup()

    def checkControls(self):
        for msg in self.launchpad['in'].iter_pending():
            if msg.type == "control_change":
                #main buttons
                if msg.value == 0:
                    continue
                if msg.control == 114:
                    #up
                    self.sequences[self.active].silent = True
                    if self.active == len(self.sequences) - 1:
                        self.active = 0
                    else:
                        self.active += 1
                    print("active:" + str(self.active))
                    self.printMsg(self.sequences[self.active].name,
                                  font=TINY_FONT)
                    self.sequences[self.active].silent = False
                    self.showIndicator()
                    self.reloadSequence()
                if msg.control == 115:
                    # down
                    if self.active == 0:
                        self.active = len(self.sequences) - 1
                    else:
                        self.active -= 1
                    print("active:" + str(self.active))
                    self.showIndicator()

                # per sequence buttons
                if msg.control == 117:
                    self.sequences[self.active].nextStep()
                if msg.control == 116:
                    #self.sequences[self.active].prevStep()
                    print("soon")
                for step in self.sequences[self.active].sequence:
                    if step.ccPitch == msg.control:
                        step.addCc(102, msg.value)
                        self.printMsg("p" + str(msg.value), font=TINY_FONT)
                        print("ccNOOOOOOOOOOOOOOW")
                    if step.ccVelo == msg.control:
                        self.printMsg("v" + str(msg.value), font=TINY_FONT)
                        print("veloNOOOOOOOOOOOOOOW")
                        step.velocity = msg.value

            if msg.type == "note_on":
                for s in self.sequences[self.active].sequence:
                    if msg.note == s.note:
                        s.active = not s.active
                        if s.value != RED_LOW:
                            s.value = RED_LOW
                            s.litup()
                        else:
                            s.value = YELLOW
                            s.litup()
    def litup(self, led, value=None):
        template = 8
        msg = Message(type='sysex',
                      data=[0, 32, 41, 2, 10, 120,
                            template, led, value])
        self.launchpad['out'].send(msg)

    def run(self):
        print(self.active)
        self.printSeq()
        while True:
            try:
                self.checkControls()
                self.checkClock()
                #for seq in self.sequences:
                    #seq.run()
            except KeyboardInterrupt:
                return
            #self.sequences[self.active].run()

if __name__ == "__main__":
    debug = True
    temp = ui(debug)
    temp.run()
