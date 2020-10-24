import logging

import attr
import rpi.GPIO as GPIO
from homekit.model import Accessory
from homekit.model.services import LightBulbService

logger = logging.getLogger('auto-home')

@attr.s
class Light:
    pin = attr.ib(type=int)
    accessory = attr.ib(
        factory=lambda : Accessory(
            'Light', 'davidesba', 'Light', '0001', '0.1'
        )
    )
    service = attr.ib(factory=LightBulbService)

    def __attrs_post_init__(self):
        self.accessory.services.append(self.service)
        self.service.set_on_set_callback(self.change_value)
        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, False)
        logger.info(f'Initialized light on pin {self.pin}')

    def change_value(self, value):
        logger.info(f'Light value set to {value}')
        GPIO.output(self.pin, bool(value))
