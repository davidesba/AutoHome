import logging
from threading import Lock
from time import sleep

import attr
import rpi.GPIO as GPIO

logger = logging.getLogger('auto-home')


@attr.s
class Power:
    pin = attr.ib(type=int)
    _lock = Lock()
    _in_use = 0

    def __attrs_post_init__(self):
        GPIO.setup(self.pin, GPIO.OUT)
        self.turn_off()
        logger.info(f'Initialized power on pin {self.pin}')

    @property
    def is_on(self) -> bool:
        return self.on
        #return GPIO.input(self.pin)

    def turn_on(self):
        self.on = True
        GPIO.output(self.pin, True)
        logger.info('Turning power on')
        sleep(0.5)

    def turn_off(self):
        self.on = False
        GPIO.output(self.pin, False)
        logger.info('Turning power off')

    def use(self):
        with self._lock:
            self._in_use += 1
            if not self.is_on:
                self.turn_on()

    def release(self):
        with self._lock:
            if self._in_use > 0:
                self._in_use -= 1
                if self.is_on and self._in_use == 0:
                    self.turn_off()
