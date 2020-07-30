import irsdk
import time
import winsound
import pystray
import signal
import sys
import _thread
from PIL import Image
import win32api
import configparser
from pprint import pprint

PROGRAM_NAME = 'iracing-audio-cue'

program_active = True

def systray_menu_exit():
	program_active = False
	icon.stop()

icon = pystray.Icon( PROGRAM_NAME
					, Image.open('icon.png')
					, menu=pystray.Menu(
						pystray.MenuItem("Exit", systray_menu_exit)))

def play(sound):
	winsound.PlaySound('sounds\\' + sound + '.wav', winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)

def iracing_update_connection_state(ir, ir_running):
	if ir_running and not (ir.is_initialized and ir.is_connected):
		ir_running = False
		ir.shutdown()
		print('iRacing disconnected')
	elif not ir_running and ir.startup() and ir.is_initialized and ir.is_connected:
		ir_running = True
		print('iRacing connected')
	return ir_running

def driver_brief(ir, caridx):
	return ir['DriverInfo']['Drivers'][caridx]['UserName'] + ' #' + str(ir['DriverInfo']['Drivers'][caridx]['CarNumber'])


class LeftRightState:
	lastplay = 0

def leftright_handler(ir, config, state):
	current_time = time.time()
	if (current_time - state.lastplay) < float(config['repeat_interval']):
		return
	if ir['CarLeftRight'] == irsdk.CarLeftRight.car_left or ir['CarLeftRight'] == irsdk.CarLeftRight.two_cars_left:
		print('leftright left')
		play('leftright_left')
		state.lastplay = current_time
	elif ir['CarLeftRight'] == irsdk.CarLeftRight.car_right or ir['CarLeftRight'] == irsdk.CarLeftRight.two_cars_right:
		print('leftright right')
		play('leftright_right')
		state.lastplay = current_time
	elif ir['CarLeftRight'] == irsdk.CarLeftRight.car_left_right:
		print('leftright both')
		play('leftright_both')
		state.lastplay = current_time

class FastClassBehindState:
	pcts = {}
	lastplay = 0

def fastclassbehind_delta(current_pct, pct):
	delta = current_pct - pct
	if abs(delta) > 0.5:
		delta = 1.0 - abs(delta)
	return delta * 100.0

def fastclassbehind_handler(ir, config, state):
	average_lap_duration = ir['DriverInfo']['DriverCarEstLapTime']
	warn_threshold = float(config['warn_threshold'])
	warn_threshold_min = float(config['warn_threshold_min'])
	warn_repeat_after = float(config['warn_repeat_after'])
	pct_delta = warn_threshold * 100.0 / average_lap_duration
	pct_delta_min = warn_threshold_min * 100.0 / average_lap_duration
	current_caridx = ir['CamCarIdx']
	current_pct = ir['LapDistPct']
	current_classspeed = ir['DriverInfo']['Drivers'][current_caridx]['CarClassRelSpeed']
	for caridx in range(len(ir['DriverInfo']['Drivers']) - 1): # - 1 to avoid beeping for the pace car
		if caridx != current_caridx: # different driver
			classspeed = ir['DriverInfo']['Drivers'][caridx]['CarClassRelSpeed']
			if classspeed > current_classspeed: # upper classes
				pct = ir['CarIdxLapDistPct'][caridx]
				if state.pcts.get(caridx,-1) != pct: #ignore still/pitted cars
					state.pcts[caridx] = pct
					delta = fastclassbehind_delta(current_pct, pct)
					if delta > pct_delta_min and delta < pct_delta:
						current_time = time.time()
						if state.lastplay + warn_repeat_after < current_time:
							print("fast car behind " + driver_brief(ir, caridx) + " delta = " + str(delta) + " me=" + str(current_pct) + " other=" + str(pct))
							play('fastclassbehind')
							state.lastplay = current_time
							return

def main_thread():
	config = configparser.ConfigParser()
	config.read('config.ini')
	ir = irsdk.IRSDK()
	ir_running = False
	leftright_state = LeftRightState()
	fastclassbehind_state = FastClassBehindState()
	while program_active:
		ir_running = iracing_update_connection_state(ir, ir_running)
		if ir_running:
			ir.freeze_var_buffer_latest()
			if config['leftright']['enabled'] == 'true':
				leftright_handler(ir, config['leftright'], leftright_state)
			if config['fastclassbehind']['enabled'] == 'true':
				fastclassbehind_handler(ir, config['fastclassbehind'], fastclassbehind_state)
		time.sleep(float(config['general']['update_interval'])) # iracing updates at 60hz, but 20hz will be enough, 0.05s between updates

if __name__ == '__main__':
	print(PROGRAM_NAME)
	_thread.start_new_thread(main_thread,())
	icon.run()