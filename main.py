from ui import Ui

if __name__ == "__main__":
    temp = Ui(debug=False,
              midiController = "Launch Control MIDI 1",
              midiInput = "Elektron Digitakt MIDI 1",
              midiOutput = "USB MIDI Interface")
    temp.run()
