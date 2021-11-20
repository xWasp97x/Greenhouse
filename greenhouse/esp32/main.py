import network
import uasyncio
from controller import *
from logic import Logic
from logger import Logger
import RTCmanager
import ujson as json
from mqtt_logger import MQTTLogger

hardware = []
controllers = []
readers = []

led = Pin(2, Pin.OUT)
led(0)

with open('config.json') as file:
	config = json.load(file)

with open('wifi.json') as file:
	wifi_config = json.load(file)


wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(wifi_config['ssid'], wifi_config['pwd'])

# SENSORS
'''
close_endstop = EndStopReader(26)
open_endstop = EndStopReader(27)
light_reader = LightReader(33)
temperature_reader = TemperatureReader(14)

readers.extend([moisture_reader, close_endstop, open_endstop, light_reader, temperature_reader])
'''

sub_configs = config['SENSORS']['light']
light_reader = LightReader(sub_configs['pin'], sub_configs['history_length'], sub_configs['max_voltage'], sub_configs['decimals'])

sub_configs = config['SENSORS']['moisture']
moisture_reader = MoistureReader(sub_configs['pin'], sub_configs['history_length'], sub_configs['max_voltage'], sub_configs['decimals'])

readers.extend((light_reader, moisture_reader))

# ACTUATORS
'''
roof_opener = RoofOpener(brake_pin=3, sleep_pin=19, dir_pin=18, step_pin=23, close_switch=close_endstop, open_switch=open_endstop)

hardware.extend([pump, roof_opener, led])
'''
led = LED(16)
pump = Pump(1)
hardware.extend((led, pump))

# CONTROLLERS
'''
temperature_controller = TemperatureController(temperature_reader, 20, 25, 2, None, roof_opener, 10, 5)

controllers.extend([moisture_controller, light_controller, temperature_controller])
'''
sub_configs = config['CONTROLLERS']['light']
light_controller = LightController(light_reader, led, sub_configs['threshold'])

sub_configs = config['CONTROLLERS']['moisture']
moisture_controller = MoistureController(moisture_reader, pump, sub_configs['low_threshold'],
										 sub_configs['high_threshold'], sub_configs['keep_on_secs'],
										 sub_configs['irrigation_delay'])
controllers.extend((light_controller, moisture_controller))
# controllers.append(light_controller)


# EVENT LOOP
event_loop = uasyncio.get_event_loop()

event_loop.create_task(RTCmanager.update_RTC(wlan))

[event_loop.create_task(reader.loop(0.5)) for reader in readers]

# [event_loop.create_task(controller.loop()) for controller in controllers]

logic = Logic(hardware, controllers)
event_loop.create_task(logic.loop(1))

logger = Logger(hardware, readers, controllers)
event_loop.create_task(logger.loop(config['LOGGER']['loop_delay']))

sub_configs = config['MQTT_LOGGER']
mqtt_logger = MQTTLogger(wlan, wifi_config['ssid'], wifi_config['pwd'], sub_configs['broker'], sub_configs['port'], sub_configs['topic'], sub_configs['qos'], readers, hardware, controllers)
event_loop.create_task(mqtt_logger.loop(sub_configs['delay']))

event_loop.run_forever()
