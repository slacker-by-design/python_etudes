"""
This module contains a controller responsible interpreting 'events'
from the view (calculator keypad), instructing the model (calculator
engine) and passing the results from the model back to the view
(calculator display).
"""
from enum import StrEnum

import ttkcalculator.model as model
from ttkcalculator.model import Calculator, Operator
from ttkcalculator.view import KeyCode, DisplayView, KeypadView

# Indicate what's relevant for other modules to import
__all__ = ['KeypadController']


# It's important values are short enough
# for the DisplayView to show them.
class Error(StrEnum):
    """ Errors reported to user """
    DIVISION_BY_ZERO = 'Division by 0'
    RESULT_TOO_LARGE = 'Result too long'
    GENERAL_PURPOSE = 'Error'


_KEY_TO_OPERATOR_MAP = {
    KeyCode.PLUS: Operator.ADD,
    KeyCode.MINUS: Operator.SUBTRACT,
    KeyCode.MULTIPLY: Operator.MULTIPLY,
    KeyCode.DIVIDE: Operator.DIVIDE
}
_KEYS_OPERATORS = tuple(_KEY_TO_OPERATOR_MAP.keys())
_KEYS_ALL = tuple(KeyCode(key) for key in KeyCode)
_KEYS_DIGITS = tuple(_KEYS_ALL[0:10])
_KEYS_CLEAR_ON_UPDATE = (KeyCode.DECIMAL_POINT, KeyCode.BACKSPACE) + _KEYS_DIGITS
_KEYS_ALL_BUT_CLEAR = tuple(key for key in _KEYS_ALL if key != KeyCode.CLEAR)

class KeypadController:
    """
    Orchestration of calculator app components.

    Class with logic responsible for
      - handling KeyCode messages from Keypad
      - translating KeyCode messages to a format suitable for Calculator engine
      - ensuring GUI status updates (DisplayView) with values from Calculator engine
    """
    def __init__(
            self,
            display_view: DisplayView,
            keypad_view: KeypadView,
            calculator: Calculator,
    ):
        # subtract 2 for decimal separator and minus sign
        if (display_view.max_items - 2) < calculator.precision:
            raise ValueError('DisplayView is incapable of showing full Calculator precision.')
        self._display: DisplayView = display_view
        self._keypad: KeypadView = keypad_view
        self._calculator: Calculator = calculator
        self._error: Error | None = None
        self._clear_on_update = False       #TODO: think of a better name for this one!
        self._blocked: set[KeyCode]  = set()

    def _clear_calculator(self):
        self._calculator.clear()
        self._error = None
        self._clear_on_update = False
        self._blocked.clear()
        self._keypad.release_all()

    def _calculate_result(self):
        result = self._calculator.result
        self._calculator.clear()
        if isinstance(result, model.Error):
            match result:
                case model.Error.DIVISION_BY_ZERO:
                    self._error = Error.DIVISION_BY_ZERO
                case model.Error.RESULT_TOO_LARGE:
                    self._error = Error.RESULT_TOO_LARGE
                case _:
                    self._error = Error.GENERAL_PURPOSE
            self._blocked = set(_KEYS_ALL_BUT_CLEAR)
        else:
            self._calculator.replace_operand(result)
            self._clear_on_update = True
            self._blocked.difference_update(_KEYS_OPERATORS)
        self._keypad.release_all()

    def _add_operator(self, operator_key: KeyCode):
        operator_ = Operator(_KEY_TO_OPERATOR_MAP[operator_key])
        self._calculator.add_operator(operator_)
        self._clear_on_update = False
        self._blocked.update(_KEYS_OPERATORS)
        self._keypad.press(operator_key)

    def _update_display_view(self):
        """ Decides, which of the calculator's operands should be displayed """
        if self._error:
            text = str(self._error)
        else:
            first, second = self._calculator.operands
            text = second if second else first
        self._display.update(text)

    def key_pressed(self, key_code: KeyCode):
        """
        Handler of the events (keys) emitted by a view (calculator keypad).

        Translates PadKey values to CalculatorEngine actions and then updates
        the DisplayView (and occasionally also KeyPadView) with the latest
        state of the CalculatorEngine.
        """
        # don't dispatch blocked keys
        if key_code in self._blocked:
            return

        # clean calculator state if the current number is a result
        # of previous calculation and the user started to type-in
        # new number without specifying the arithmetical operation
        if self._clear_on_update and key_code in _KEYS_CLEAR_ON_UPDATE:
            self._calculator.clear()
            self._clear_on_update = False

        match key_code:
            case KeyCode.CLEAR:
                self._clear_calculator()
            case KeyCode.BACKSPACE:
                self._calculator.delete_last_entry()
            case KeyCode.EQUALS if self._calculator.operator:
                self._calculate_result()
            case KeyCode.NEGATE:
                self._calculator.invert_sign()
            case operator_key if operator_key in _KEYS_OPERATORS:
                self._add_operator(operator_key)
            case KeyCode.DECIMAL_POINT:
                self._calculator.add_decimal_point()
            case digit if digit in _KEYS_DIGITS:
                self._calculator.add_digit(digit)

        self._update_display_view()

    def __repr__(self):
        return f'KeypadController(_error={repr(self._error)}, '\
               f'_blocked={self._blocked}, '\
               f'_clear_on_update={self._clear_on_update})'

