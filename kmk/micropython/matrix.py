import machine

from kmk.common.abstract.matrix_scanner import AbstractMatrixScanner
from kmk.common.consts import DiodeOrientation
from kmk.common.event_defs import matrix_changed


class MatrixScanner(AbstractMatrixScanner):
    def __init__(self, cols, rows, active_layers, diode_orientation=DiodeOrientation.COLUMNS):
        # A pin cannot be both a row and column, detect this by combining the
        # two tuples into a set and validating that the length did not drop
        #
        # repr() hackery is because MicroPython Pin objects are not hashable.
        # Technically we support passing either a string (hashable) or the
        # Pin object directly here, so the hackaround is necessary.
        unique_pins = {repr(c) for c in cols} | {repr(r) for r in rows}
        if len(unique_pins) != len(cols) + len(rows):
            raise ValueError('Cannot use a pin as both a column and row')

        self.cols = [machine.Pin(pin) for pin in cols]
        self.rows = [machine.Pin(pin) for pin in rows]
        self.diode_orientation = diode_orientation
        self.active_layers = active_layers
        self.last_pressed_len = 0

        if self.diode_orientation == DiodeOrientation.COLUMNS:
            self.outputs = self.cols
            self.inputs = self.rows
        elif self.diode_orientation == DiodeOrientation.ROWS:
            self.outputs = self.rows
            self.inputs = self.cols
        else:
            raise ValueError('Invalid DiodeOrientation: {}'.format(
                self.diode_orientation,
            ))

        for pin in self.outputs:
            pin.init(machine.Pin.OUT)
            pin.off()

        for pin in self.inputs:
            pin.init(machine.Pin.IN, machine.Pin.PULL_DOWN)
            pin.off()

    def scan_for_pressed(self):
        pressed = []

        for oidx, opin in enumerate(self.outputs):
            opin.value(1)

            for iidx, ipin in enumerate(self.inputs):
                if ipin.value():
                    pressed.append(
                        (oidx, iidx) if self.diode_orientation == DiodeOrientation.ROWS else (iidx, oidx)  # noqa
                    )

            opin.value(0)

        if len(pressed) != self.last_pressed_len:
            self.last_pressed_len = len(pressed)
            return matrix_changed(pressed)

        return None  # The default, but for explicitness
