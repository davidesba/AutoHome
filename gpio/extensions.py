from homekit.model import get_id
from homekit.model.characteristics import (AbstractCharacteristic,
                                           CharacteristicFormats,
                                           CharacteristicPermissions,
                                           CharacteristicsTypes,
                                           CharacteristicUnits,
                                           NameCharacteristic)
from homekit.model.services import AbstractService, ServicesTypes


class TargetPositionCharacteristic(AbstractCharacteristic):
    """
    Defined on page 157
    """

    def __init__(self, iid):
        AbstractCharacteristic.__init__(
            self, iid, CharacteristicsTypes.POSITION_TARGET,
            CharacteristicFormats.uint8
        )
        self.perms = [
            CharacteristicPermissions.paired_write,
            CharacteristicPermissions.paired_read,
            CharacteristicPermissions.events
        ]
        self.description = 'the desired position'
        self.minValue = 0
        self.maxValue = 100
        self.minStep = 1
        self.unit = CharacteristicUnits.percentage
        self.value = 0


class TargetPositionCharacteristicMixin(object):
    def __init__(self, iid):
        self._targetPosition = TargetPositionCharacteristic(iid)
        self.characteristics.append(self._targetPosition)

    def set_target_position_set_callback(self, callback):
        self._targetPosition.set_set_value_callback(callback)

    def set_target_position_get_callback(self, callback):
        self._targetPosition.set_get_value_callback(callback)


class CurrentPositionCharacteristic(AbstractCharacteristic):
    """
    Defined on page 170
    """

    def __init__(self, iid):
        AbstractCharacteristic.__init__(
            self, iid, CharacteristicsTypes.POSITION_CURRENT,
            CharacteristicFormats.uint8
        )
        self.perms = [
            CharacteristicPermissions.paired_read,
            CharacteristicPermissions.events
        ]
        self.description = 'the current position'
        self.minValue = 0
        self.maxValue = 100
        self.minStep = 1
        self.unit = CharacteristicUnits.percentage
        self.value = 0


class CurrentPositionCharacteristicMixin(object):
    def __init__(self, iid):
        self._currentPosition = CurrentPositionCharacteristic(iid)
        self.characteristics.append(self._currentPosition)

    def set_current_position_get_callback(self, callback):
        self._currentPosition.set_get_value_callback(callback)


class PositionStateCharacteristic(AbstractCharacteristic):
    """
    Defined on page 161, valid values:
        0:     ”Going to the minimum value specified in metadata”
        1:     ”Going to the maximum value specified in metadata”
        2:     ”Stopped”
        3-255: ”Reserved”
    """

    def __init__(self, iid):
        AbstractCharacteristic.__init__(
            self, iid, CharacteristicsTypes.POSITION_STATE,
            CharacteristicFormats.uint8
        )
        self.perms = [
            CharacteristicPermissions.paired_read,
            CharacteristicPermissions.events
        ]
        self.description = 'Desired mode of operation'
        self.minValue = 0
        self.maxValue = 2
        self.minStep = 1
        self.value = 2


class PositionStateCharacteristicMixin(object):
    def __init__(self, iid):
        self._positionState = PositionStateCharacteristic(iid)
        if self.characteristics is None:
            self.characteristics = []
        self.characteristics.append(self._positionState)

    def set_position_state_get_callback(self, callback):
        self._positionState.set_get_value_callback(callback)


class WindowCoveringService(
    AbstractService, TargetPositionCharacteristicMixin,
    CurrentPositionCharacteristicMixin, PositionStateCharacteristicMixin,
):
    """
    Defined on page 157
    """

    def __init__(self, name):
        AbstractService.__init__(
            self, ServicesTypes.get_uuid('public.hap.service.window-covering'),
            get_id()
        )
        TargetPositionCharacteristicMixin.__init__(self, get_id())
        CurrentPositionCharacteristicMixin.__init__(self, get_id())
        PositionStateCharacteristicMixin.__init__(self, get_id())
        self.append_characteristic(NameCharacteristic(get_id(), name))

    def get_name(self):
        for characteristic in self.characteristics:
            if isinstance(characteristic, NameCharacteristic):
                return characteristic.value
        return None
