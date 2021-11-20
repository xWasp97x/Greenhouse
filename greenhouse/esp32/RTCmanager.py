import ntptime
import uasyncio
from machine import RTC
from network import WLAN

ntptime.host = '0.it.pool.ntp.org'
timezone = 2


async def update_RTC(wlan: WLAN):
	while True:
		while not wlan.isconnected():
			await uasyncio.sleep(10)

		try:
			ntptime.settime()
			utc = list(RTC().datetime())
			utc[4] += timezone
			RTC().datetime(tuple(utc))
			print('RTC synced: {}'.format(RTC().datetime()))
			await uasyncio.sleep(60 * 10)
		except OSError as ose:
			print('Error synchronizing time: {}'.format(ose))
			await uasyncio.sleep(10)


