import logging
import sys

import rpi.GPIO as GPIO
import yaml
from homekit import AccessoryServer
from homekit.model import Accessory

from gpio.light import Light
from gpio.motor import Direction, Motor
from gpio.power import Power

if __name__ == '__main__':
    # setup logger
    logger = logging.getLogger('auto-home')
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.info('starting')

    GPIO.setmode(GPIO.BOARD)
    with open('/etc/auto-home/config.yaml') as data:
        config = yaml.load(data)

    light = Light(config['relay']['light'])
    power = Power(config['relay']['power'])
    motors = dict()
    blinds = Accessory('Blinds', 'davidesba', 'Blinds', '0001', '0.1')
    for name, values in config.get('motors', {}).items():
        motors[name] = Motor(
            name, values['dir_pin'], values['step_pin'],
            values.get('max_position', 2200), power, blinds.aid
        )

    for motor in motors.values():
        blinds.services.append(motor.service)

    # create a server and an accessory an run it unless ctrl+c was hit
    try:
        httpd = AccessoryServer('/etc/auto-home/config.json', logger)

        httpd.add_accessory(light.accessory)
        httpd.add_accessory(blinds)
        Motor.server = httpd

        httpd.publish_device()
        logger.info('published device and start serving')
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        for motor in motors.values():
            motor.store()
        GPIO.cleanup()

    # unpublish the device and shut down
    logger.info('unpublish device')
    httpd.unpublish_device()
    httpd.shutdown()
