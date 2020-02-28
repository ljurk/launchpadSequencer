from mido import Message
from colors import Colors
from step import Step


class Sequencer():
    """
    class with all informations of a sequence
    """
    sequence = []
    #ports
    launchpad = {}
    interface = {}
    started = False
    channel = 3
    activeStep = 0
    note = None
    name = None
    silent = True
    outgoingCC = []

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
                print("CCCCCC")
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
            self.sequence[self.activeStep].litup(Colors.GREEN_LOW)

    def prevStep(self, activeStep):
        self.sequence[activeStep].litup()
        if activeStep != 0:
            activeStep -= 1
        else:
            activeStep = 7
        self.sequence[activeStep].litup(Colors.GREEN_LOW)
        return activeStep

    def __init__(self, note, name, launchpadPorts, interfacePorts, outgoingCC, silent, new=False):
        print("init")
        self.launchpad = launchpadPorts
        self.interface = interfacePorts
        self.note = note
        self.name = name
        self.outgoingCC = outgoingCC
        self.silent = silent
        self.sequence = []
        if not new:
            return
        self.sequence.append(Step(9, 0, [21, 41], self.launchpad['out']))
        self.sequence.append(Step(10, 1, [22, 42], self.launchpad['out']))
        self.sequence.append(Step(11, 2, [23, 43], self.launchpad['out']))
        self.sequence.append(Step(12, 3, [24, 44], self.launchpad['out']))
        self.sequence.append(Step(25, 4, [25, 45], self.launchpad['out']))
        self.sequence.append(Step(26, 5, [26, 46], self.launchpad['out']))
        self.sequence.append(Step(27, 6, [27, 47], self.launchpad['out']))
        self.sequence.append(Step(28, 7, [28, 48], self.launchpad['out']))


    def run(self, silent=False):
        self.silent = silent
        #self.checkClock()
        #self.checkControls()

