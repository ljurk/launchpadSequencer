from __future__ import print_function
import os
import time
import json
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
    def __init__(self, midiController, midiInput, midiOutput debug):
        serial = spi(port=0, device=0, gpio=noop())
        self.device = max7219(serial,
                              cascaded=2,
                              rotate=1)
        print("Created device")
        self.printMsg("ESID", font=TINY_FONT)
        self.launchpad['in'] = mido.open_input(midiController)
        self.launchpad['out'] = mido.open_output(midiController)
        if debug:
            self.interface['in'] = mido.open_input()
            self.interface['out'] = mido.open_output()
        else:
            self.interface['in'] = mido.open_input(midiInput)
            self.interface['out'] = mido.open_output(midiOutput)
        self.sequences = []

        new = False
        if new:
            self.sequences.append(Sequencer(36,
                                            "KK",
                                            self.launchpad,
                                            self.interface,
                                            outgoingCC=[10,12],
                                            silent=False,
                                            new=True))
            self.sequences.append(Sequencer(38,
                                            "SD",
                                            self.launchpad,
                                            self.interface,
                                            outgoingCC=[18,19],
                                            silent=True,
                                            new=True))
            self.sequences.append(Sequencer(39,
                                            "OH",
                                            self.launchpad,
                                            self.interface,
                                            outgoingCC=[58,59],
                                            silent=True,
                                            new=True))
            self.sequences.append(Sequencer(46,
                                            "CY",
                                            self.launchpad,
                                            self.interface,
                                            outgoingCC=[50,51],
                                            silent=True,
                                            new=True))
            for seq in self.sequences:
                self.saveSequence(seq)
        else:
            self.loadSequences()

    def printMsg(self, txt, font=LCD_FONT, moving=False, pos=None):
        virtual = viewport(self.device, width=self.device.width, height=self.device.height*2)
        margins = []
        if pos and len(txt) == 1:
            with canvas(virtual) as draw:
                text(draw,
                     pos,
                     txt,
                     fill="white",
                     font=proportional(font))
            virtual.set_position((0, 0))
            return

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
            for i in range(virtual.height - self.device.height):
                virtual.set_position((0, i))
        else:
            virtual.set_position((0, 0))

    def saveSequence(self, sequence):
        sequencerData = {}
        sequencerData['note'] = sequence.note
        sequencerData['channel'] = sequence.channel
        sequencerData['name'] = sequence.name
        sequencerData['silent'] = sequence.silent
        sequencerData['outgoingCC'] = sequence.outgoingCC
        sequencerData['sequence'] = []
        for step in sequence.sequence:
            temp = {}
            temp['cc'] = step.cc
            temp['note'] = step.note
            temp['active'] = step.active
            temp['led'] = step.led
            temp['incommingCC'] = step.incommingCC
            temp['cc'] = step.cc
            temp['value'] = step.value
            sequencerData['sequence'].append(temp)
        with open(self.sequenceDir + sequence.name + '.json', 'w', encoding='utf-8') as fp:
            json.dump(sequencerData, fp, indent=4, ensure_ascii=False)

    def loadSequences(self):
        fileCount = 0
        for seqfile in sorted(os.listdir(self.sequenceDir)):
            print(seqfile)
            if fileCount == 4:
                return
            fileCount += 1

            with open(os.path.join(self.sequenceDir, seqfile), 'r', encoding='utf-8') as fp:
                data = json.load(fp)
            sequence = []
            for step in data['sequence']:
                sequence.append(Step(step['note'],
                                     step['led'],
                                     step['incommingCC'],
                                     self.launchpad['out'],
                                     step['active']))
                for cc in step['cc']:
                    sequence[-1].addCc(cc["cc"], cc["value"])
                temp = {}

            self.sequences.append(Sequencer(data['note'],
                                            data['name'],
                                            self.launchpad,
                                            self.interface,
                                            outgoingCC=data['outgoingCC'],
                                            silent=data['silent']))
            self.sequences[-1].sequence = sequence

    def showIndicator(self):
        for i in range(0, 4):
            self.litup(i + 8, Colors.OFF)
        self.litup(self.active + 8, Colors.RED_LOW)

    def showInfo(self, seqName):
        virtual = viewport(self.device, width=self.device.width, height=self.device.height*2)
        with canvas(virtual) as draw:
            text(draw,
                 (0,0),
                 seqName,
                 fill="white",
                 font=proportional(TINY_FONT))
            # print sequences
            for y, seq in enumerate(self.sequences):
                for x, step in enumerate(seq.sequence):
                    if step.active:
                            draw.point((x,y+8), fill="white")
            # show active step

            draw.point((self.sequences[0].activeStep,13), fill="white")

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
        for seq in self.sequences:
            seq.nextStep()
            self.showInfo(self.sequences[self.active].name)

    def clockCallback(self, msg):
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

    def reloadSequence(self):
        for step in self.sequences[self.active].sequence:
            step.litup()

    def checkControls(self):
        msg= self.launchpad['in'].poll()
        if msg:
            if msg.type == "control_change":
                #navigation buttons

                if msg.value == 0:
                    # ignore off message
                    return
                if msg.control in (114, 115):
                    # hide previous sequence
                    self.sequences[self.active].silent = True

                    if msg.control == 114:
                        # up
                        self.active += 1
                        if self.active == len(self.sequences):
                            self.active = 0
                    else:
                        # down
                        self.active -= 1
                        if self.active == -1:
                            self.active = len(self.sequences) -1

                    print("active:" + str(self.active))
                    self.sequences[self.active].silent = False
                    self.showIndicator()
                    self.showInfo(self.sequences[self.active].name)
                    self.reloadSequence()

                # per sequence buttons
                if msg.control == 117:
                    self.sequences[self.active].nextStep()
                if msg.control == 116:
                    #self.sequences[self.active].prevStep()
                    self.printMsg("save", font=TINY_FONT)
                    self.saveSequence(self.sequences[self.active])

                for stepNumber , step in enumerate(self.sequences[self.active].sequence):
                    # upper row
                    if step.incommingCC[0] == msg.control:
                        print(f"cc:{stepNumber}")
                        step.addCc(self.sequences[self.active].outgoingCC[0], msg.value)


                        self.printMsg(".",
                                      font=TINY_FONT,
                                      pos=(stepNumber,2))
                        self.printMsg("'" + str(msg.value),
                                      font=TINY_FONT)
                    # lower row
                    if step.incommingCC[1] == msg.control:
                        print(f"velo:{stepNumber}")
                        step.addCc(self.sequences[self.active].outgoingCC[1], msg.value)
                        self.printMsg(".",
                                      font=TINY_FONT,
                                      pos=(stepNumber,1))
                        self.printMsg("." + str(msg.value),
                                      font=TINY_FONT)
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
        while True:
            try:
                self.checkClock()
                self.checkControls()
                #for seq in self.sequences:
                    #seq.run()
            except KeyboardInterrupt:
                return
            #self.sequences[self.active].run()
