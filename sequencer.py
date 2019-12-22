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
            self.sequence[self.activeStep].litup(Colors.GREEN_LOW)

    def prevStep(self, activeStep):
        self.sequence[activeStep].litup()
        if activeStep != 0:
            activeStep -= 1
        else:
            activeStep = 7
        self.sequence[activeStep].litup(Colors.GREEN_LOW)
        return activeStep

    def __init__(self, note, name, launchpadPorts, interfacePorts, silent, new=False):
        print("init")
        self.launchpad = launchpadPorts
        self.interface = interfacePorts
        self.note = note
        self.name = name
        self.silent = silent
        self.sequence = []
        cc = 102
        val = 60
        if new:
            self.sequence.append(Step(9, 0, 41, 21, self.launchpad['out'], cc, val))
            self.sequence.append(Step(10, 1, 42, 22, self.launchpad['out'], cc, val))
            self.sequence.append(Step(11, 2, 43, 23, self.launchpad['out'], cc, val))
            self.sequence.append(Step(12, 3, 44, 24, self.launchpad['out'], cc, val))
            self.sequence.append(Step(25, 4, 45, 25, self.launchpad['out'], cc, val))
            self.sequence.append(Step(26, 5, 46, 26, self.launchpad['out'], cc, val))
            self.sequence.append(Step(27, 6, 47, 27, self.launchpad['out'], cc, val))
            self.sequence.append(Step(28, 7, 48, 28, self.launchpad['out'], cc, val))


    def run(self, silent=False):
        self.silent = silent
        #self.checkClock()
        #self.checkControls()

