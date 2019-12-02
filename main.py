#!/usr/bin/env python
"""
Send random notes to the output port.
"""

from __future__ import print_function
import sys
import time
import random
import mido
from mido import Message

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
    note = None
    led = None
    value = YELLOW
    cc = None
    outputNote = 60

    launchOut = None
    def __init__(self, note, led, cc, outport):
        self.launchOut = outport
        self.note = note
        self.led = led
        self.cc=cc

    def litup(self, value=None) :
        if not value:
            value = self.value
        template = 8
        #led = 5
        #value = GREEN_LOW
        msg = Message(type='sysex',
                      data=[0, 32, 41, 2, 10, 120,
                      template, self.led , value])
        self.launchOut.send(msg)

class sequencer():
    sequence = []
    inputPort = None
    clockIn = None
    outputPort = None
    launchOut= None
    started = False
    channel = 15
    #print()
    def nextStep(self, activeStep):
        print("next")
        if self.sequence[activeStep].value == RED_LOW:
            print("off"+str(activeStep))
            msg = Message('note_off', note=self.sequence[activeStep].outputNote, channel=self.channel)
            self.outputPort.send(msg)
        self.sequence[activeStep].litup()
        if activeStep != 7:
            activeStep += 1
        else:
            activeStep = 0
        if self.sequence[activeStep].value == RED_LOW:
            print("on"+str(activeStep))
            msg = Message('note_on', note=self.sequence[activeStep].outputNote, channel=self.channel)
            self.outputPort.send(msg)
    
        self.sequence[activeStep].litup(GREEN_LOW)
        return activeStep
    def prevStep(self, activeStep):
        self.sequence[activeStep].litup()
        if activeStep != 0:
            activeStep -= 1
        else:
            activeStep = 7
        self.sequence[activeStep].litup(GREEN_LOW)
        return activeStep
    
    def __init__(self):
        print("init")
        portname = "Launch Control:Launch Control MIDI 1"
        self.launchOut = mido.open_output(portname) 
        self.inputPort = mido.open_input(portname) 
        self.clockIn = mido.open_input("USB MIDI Interface:USB MIDI Interface MIDI 1") 
        self.outputPort = mido.open_output("USB MIDI Interface:USB MIDI Interface MIDI 1")
        self.sequence.append(step(9, 0, 41, self.launchOut))
        self.sequence.append(step(10, 1, 42, self.launchOut))
        self.sequence.append(step(11, 2, 43, self.launchOut))
        self.sequence.append(step(12, 3, 44, self.launchOut))
        self.sequence.append(step(25, 4, 45, self.launchOut))
        self.sequence.append(step(26, 5, 46, self.launchOut))
        self.sequence.append(step(27, 6, 47, self.launchOut))
        self.sequence.append(step(28, 7, 48, self.launchOut))
    
    
    def run(self):
        activeStep = 0
        clockDivider = 8
        clockCount = 0
        while True:
            for msg in self.clockIn.iter_pending():
                if msg.type == "start":
                    print('START')
                    self.started = True
                if msg.type == "stop":
                    print('STOP')
                    self.started = False
                    self.outputPort.reset()
                if msg.type == "clock" and self.started:
                    if clockCount == clockDivider:
                        activeStep = self.nextStep(activeStep)
                        clockCount = 0
                    else:
                        clockCount += 1

            for msg in self.inputPort.iter_pending(): 
                if msg.type == "control_change":
                    if msg.value == 0:
                        continue
                    if msg.control == 117:
                        activeStep = self.nextStep(activeStep)
                    if msg.control == 116:
                        activeStep = self.prevStep(activeStep)
                    for s in self.sequence:
                        if s.cc == msg.control:
                            s.outputNote = msg.value


                if msg.type == "note_on":
                    for s in self.sequence:
                        if msg.note == s.note:
                            if s.value != RED_LOW:
                                s.value = RED_LOW
                                s.litup()
                            else:
                                s.value = YELLOW
                                s.litup()
                    #self.outputPort.send(msg)          
                    print(msg.note)
                    #sequence[0].litup(launchOut, msg.note - 8)
                #if msg.type == "note_off":
                    #self.outputPort.send(msg)          
                print(msg)
    
if __name__ == "__main__":
    temp = sequencer()
    temp.run()
