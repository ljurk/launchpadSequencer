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
    velocity = 16
    cc = {}
    ccPitch = None
    ccVelo = None
    outputNote = 36

    launchOut = None
    def __init__(self, note, led, ccPitch, ccVelo, outport, value=YELLOW):
        self.launchOut = outport
        self.note = note
        self.led = led
        self.ccVelo = ccVelo
        self.ccPitch = ccPitch
        self.value = value

    def litup(self, value=None):
        if not value:
            value = self.value
        template = 8
        msg = Message(type='sysex',
                      data=[0, 32, 41, 2, 10, 120,
                            template, self.led, value])
        self.launchOut.send(msg)

class sequencer():
    sequence = []
    inputPort = None
    clockIn = None
    outputPort = None
    launchOut = None
    started = False
    channel = 15
    #print()
    activeStep = 0
    clockDivider = 11
    clockCount = 0

    def nextStep(self):
        print("next" + str(self.activeStep))
        if self.sequence[self.activeStep].value == RED_LOW:
            print("off" +
                  str(self.activeStep) +
                  "[" +
                  str(self.sequence[self.activeStep].velocity) +
                  "]")
            msg = Message('note_off',
                          note=self.sequence[self.activeStep].outputNote,
                          channel=self.channel)#,
                          #velocity=self.sequence[activeStep].velocity)
            self.outputPort.send(msg)
        self.sequence[self.activeStep].litup()
        if self.activeStep != 7:
            self.activeStep += 1
        else:
            self.activeStep = 0
        if self.sequence[self.activeStep].value == RED_LOW:
            print("on"+str(self.activeStep) + "[" + str(self.sequence[self.activeStep].velocity) + "]")
            msg = Message('note_on',
                          note=self.sequence[self.activeStep].outputNote,
                          channel=self.channel,
                          velocity=self.sequence[self.activeStep].velocity)
            self.outputPort.send(msg)

        self.sequence[self.activeStep].litup(GREEN_LOW)

    def prevStep(self, activeStep):
        self.sequence[activeStep].litup()
        if activeStep != 0:
            activeStep -= 1
        else:
            activeStep = 7
        self.sequence[activeStep].litup(GREEN_LOW)
        return activeStep

    def __init__(self, inputPort, outputPort, clockPort=None):
        print("init")
        if not clockPort:
            clockPort = outputPort
        self.launchOut = mido.open_output(inputPort)
        self.inputPort = mido.open_input(inputPort)
        self.clockIn = mido.open_input(clockPort)
        self.outputPort = mido.open_output(outputPort)
        self.sequence.append(step(9, 0, 41, 21, self.launchOut, RED_LOW))
        self.sequence.append(step(10, 1, 42, 22, self.launchOut))
        self.sequence.append(step(11, 2, 43, 23, self.launchOut, RED_LOW))
        self.sequence.append(step(12, 3, 44, 24, self.launchOut))
        self.sequence.append(step(25, 4, 45, 25, self.launchOut, RED_LOW))
        self.sequence.append(step(26, 5, 46, 26, self.launchOut))
        self.sequence.append(step(27, 6, 47, 27, self.launchOut, RED_LOW))
        self.sequence.append(step(28, 7, 48, 28, self.launchOut))

    def checkClock(self):
        for msg in self.clockIn.iter_pending():
            if "clock" not in msg.type:
                print(msg)
            if msg.type == "start":
                print('START')
                self.started = True
            if msg.type == "stop":
                print('STOP')
                self.started = False
                self.outputPort.reset()
                self.sequence[self.activeStep].litup(YELLOW)
                self.activeStep = 0
                self.sequence[0].litup(GREEN_LOW)

            if msg.type == "clock" and self.started:
                if self.clockCount == self.clockDivider:
                    self.nextStep()
                    self.clockCount = 0
                else:
                    self.clockCount += 1

    def checkControls(self):
        for msg in self.inputPort.iter_pending():
            if msg.type == "control_change":
                if msg.value == 0:
                    continue
                if msg.control == 117:
                    self.nextStep()
                if msg.control == 116:
                    self.activeStep = self.prevStep(self.activeStep)
                for s in self.sequence:
                    if s.ccPitch == msg.control:
                        #s.outputNote = msg.value
                        print("NOOOOOOOOOOOOOOW")
                    if s.ccVelo  == msg.control:
                        print("NOOOOOOOOOOOOOOW")
                        s.velocity  = msg.value


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

    def run(self):
        while True:
            self.checkClock()
            self.checkControls()


if __name__ == "__main__":
    inputPort = "Launch Control:Launch Control MIDI 1"
    clockPort = "Elektron Digitakt MIDI 1"
    outputPort = "USB MIDI Interface:USB MIDI Interface MIDI 1"
    temp = sequencer(inputPort, outputPort, clockPort)
    temp.run()
