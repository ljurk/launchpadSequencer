from __future__ import print_function
import os
import time
import json
import codecs
import mido
from luma.led_matrix.device import max7219
from luma.core.interface.serial import spi, noop
from luma.core.render import canvas
from luma.core.virtual import viewport
from luma.core.legacy import text
from luma.core.legacy.font import proportional, TINY_FONT, LCD_FONT
from mido import Message
from sequencer import Sequencer
from step import Step
from colors import Colors

class Ui():
    sequences = None
    active = 0
    #ports
    launchpad = {}
    interface = {}
    started = False
    clockDivider = 11
    clockCount = 0
    device = None
    sequenceDir = "sequences/"
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

        new = False
        if new:
            self.sequences.append(Sequencer(36,
                                            "KK",
                                            self.launchpad,
                                            self.interface,
                                            silent=False,
                                            new=True))
            self.sequences.append(Sequencer(46,
                                            "SD",
                                            self.launchpad,
                                            self.interface,
                                            silent=True,
                                            new=True))
            self.sequences.append(Sequencer(44,
                                            "OH",
                                            self.launchpad,
                                            self.interface,
                                            silent=True,
                                            new=True))
            self.sequences.append(Sequencer(39,
                                            "CP",
                                            self.launchpad,
                                            self.interface,
                                            silent=True,
                                            new=True))
            for seq in self.sequences:
                self.saveSequence(seq)
        else:
            self.loadSequences()

    def printMsg(self, txt, font=LCD_FONT, moving=False):
        virtual = viewport(self.device, width=self.device.width, height=self.device.height*2)
        margins = []
        if font == TINY_FONT:
            margins.append([0, 0])
            margins.append([4, 0])
            margins.append([0, 8])
            margins.append([4, 8])
        else:
            margins.append([0, 0])
            margins.append([0, 8])

        with canvas(virtual) as draw:
            for i, word in enumerate(txt):
                text(draw,
                     (margins[i][0], margins[i][1]),
                     word,
                     fill="white",
                     font=proportional(font))
        if moving:
            print("move")
            for i in range(virtual.height - self.device.height):
                print(i)
                virtual.set_position((0, i))
                time.sleep(0.5)
        else:
            virtual.set_position((0, 0))

    def saveSequence(self, sequence):
        sequencerData = {}
        sequencerData['note'] = sequence.note
        sequencerData['channel'] = sequence.channel
        sequencerData['name'] = sequence.name
        sequencerData['silent'] = 'true' if sequence.silent else 'false'
        sequencerData['sequence'] = []
        for step in sequence.sequence:
            temp = {}
            temp['cc'] = step.cc
            temp['note'] = step.note
            temp['active'] = 'true' if step.active else 'false'
            temp['led'] = step.led
            temp['ccPitch'] = step.ccPitch
            temp['ccVelo'] = step.ccVelo
            temp['cc'] = step.cc
            temp['value'] = step.value
            sequencerData['sequence'].append(temp)
        print(sequencerData)
        with open(self.sequenceDir + sequence.name + '.json', 'wb') as fp:
            json.dump(sequencerData, codecs.getwriter('utf-8')(fp), indent=4, ensure_ascii=False)

    def loadSequences(self):
        for seqfile in os.listdir(self.sequenceDir):
            with codecs.open(os.path.join(self.sequenceDir, seqfile), 'r', encoding='utf-8') as fp:
                data = json.load(fp)
            #print(data)
            sequence = []
            for step in data['sequence']:
                print(step)
                sequence.append(Step(step['note'],
                                     step['led'],
                                     step['ccPitch'],
                                     step['ccVelo'],
                                     self.launchpad['out'],
                                     step['cc'][0]['cc'],
                                     step['cc'][0]['value'],
                                     step['value']))
                temp = {}

            self.sequences.append(Sequencer(data['note'],
                                            data['name'],
                                            self.launchpad,
                                            self.interface,
                                            silent=False))
            self.sequences[-1].sequence = sequence

    def showIndicator(self):
        for i in range(0, 4):
            self.litup(i + 8, Colors.OFF)
        self.litup(self.active + 8, Colors.RED_LOW)

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
                seq.sequence[seq.activeStep].litup(Colors.YELLOW)
            seq.activeStep = 0
            if not seq.silent:
                seq.sequence[0].litup(Colors.GREEN_LOW)

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
                    self.printMsg("save", font=TINY_FONT)
                    self.saveSequence(self.sequences[self.active])

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
                for step in self.sequences[self.active].sequence:
                    if msg.note == step.note:
                        step.active = not step.active
                        if step.value != Colors.RED_LOW:
                            step.value = Colors.RED_LOW
                            step.litup()
                        else:
                            step.value = Colors.YELLOW
                            step.litup()

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
