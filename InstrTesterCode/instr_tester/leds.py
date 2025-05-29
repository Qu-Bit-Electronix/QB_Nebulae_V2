import ui

interface = ui.UserInterface()

interface.brightness = 4095

while True:
	interface.brightness += 64
	if interface.brightness > 4095 :
		interface.brightness = 0
	interface.update()

