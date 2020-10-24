import logging
import pickle
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from enum import Enum
from pathlib import Path
from queue import Empty, Queue

import attr
import rpi.GPIO as GPIO

from gpio.extensions import (CurrentPositionCharacteristic,
                             PositionStateCharacteristic,
                             TargetPositionCharacteristic,
                             WindowCoveringService)
from gpio.power import Power

PAUSE = 0.005
TURN = 200
logger = logging.getLogger('auto-home')


class Direction(Enum):
    left = 0
    right = 1


@attr.s
class Motor:
    name = attr.ib()
    dir_pin = attr.ib(type=int)
    step_pin = attr.ib(type=int)
    max_steps = attr.ib(type=int)
    power = attr.ib(type=Power)
    aid = attr.ib(type=str)
    service = attr.ib(default=None)
    position = attr.ib(default=0)
    status = attr.ib(default=2)
    target = attr.ib(default=0)
    server = None

    @property
    def cache_file(self) -> Path:
        return Path(f'.motor_{self.name}_cache.pickle')

    def set_chars(self):
        chars = list()
        for characteristic in self.service.characteristics:
            if isinstance(characteristic, PositionStateCharacteristic):
                characteristic.value = self.status
                chars.append((self.aid, characteristic.iid))
            if isinstance(characteristic, CurrentPositionCharacteristic):
                characteristic.value = self.get_percentage_position()
                chars.append((self.aid, characteristic.iid))
            if isinstance(characteristic, TargetPositionCharacteristic):
                characteristic.value = self.get_target()
                chars.append((self.aid, characteristic.iid))
        try:
            self.server.write_event(chars)
        except Exception:
            logger.exception('Error setting chars:')

    def get_percentage_position(self) -> int:
        result = int((self.position / self.max_steps) * 100)
        logger.debug(f'Motor {self.name} in {result}')
        return 100 - result

    def get_target(self) -> int:
        result = int((self.target / self.max_steps) * 100)
        logger.debug(f'Motor {self.name} target in {result}')
        return 100 - result

    def get_status(self) -> int:
        logger.debug(f'Motor {self.name} in state {self.status}')
        return self.status

    def __attrs_post_init__(self):
        GPIO.setup(self.dir_pin, GPIO.OUT)
        GPIO.setup(self.step_pin, GPIO.OUT)
        logger.info(
            f'Initialized motor {self.name} with '
            f'[step: {self.step_pin} dir: {self.dir_pin}]'
        )
        self._pool = ThreadPoolExecutor(max_workers=1)
        self.load()
        self.service = WindowCoveringService(self.name)
        self.service.set_target_position_set_callback(self.advance)
        self.service.set_current_position_get_callback(
            self.get_percentage_position
        )
        self.service.set_position_state_get_callback(self.get_status)
        self.service.set_target_position_get_callback(self.get_target)

    def _advance(self, value: int, direction: Direction):
        logger.info(
            f'Advance {value} steps {direction.name} in {self.name}'
        )
        GPIO.output(self.dir_pin, direction.value)
        time.sleep(PAUSE)

        self.status = direction.value
        for i in range(0, value):
            GPIO.output(self.step_pin, True)
            time.sleep(PAUSE)
            GPIO.output(self.step_pin, False)
            time.sleep(PAUSE)
            if direction == Direction.right:
                self.position += 1
            else:
                self.position -= 1
            if i % TURN == 0:
                logger.debug(
                    f'Motor {self.name} rotated {(i / TURN) + 1} turn'
                )
                self.set_chars()

        self.status = 2
        self.power.release()
        self.set_chars()

    def advance(self, value: int):
        value = 100 - value
        self.power.use()
        current_target_per = int((self.target / self.max_steps) * 100)
        if current_target_per == value:
            return
        elif current_target_per < value:
            direction = Direction.right
            steps = int((self.max_steps / 100) * value) - self.target
        else:
            direction = Direction.left
            steps = self.target - int((self.max_steps / 100) * value)
        self.target = int((self.max_steps / 100) * value)

        self._pool.submit(self._advance, steps, direction)

    def load(self):
        if self.cache_file.is_file():
            with self.cache_file.open('rb') as data:
                self.position = pickle.load(data)
        self.target = self.position

    def store(self):
        with self.cache_file.open('wb') as data:
            pickle.dump(self.position, data)
