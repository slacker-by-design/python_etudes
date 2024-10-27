"""
This module contains items dealing with visualisation of the calculator.
Mostly it's custom widgets representing parts of the calculator GUI, but
also "adapter" classes to bind widgets with controller(s).
"""
import tkinter as tk
from enum import StrEnum
from tkinter import ttk
from typing import Callable, Protocol, Any

from ttkcalculator import _SYSTEM

# Indicate what's relevant for other modules to import
__all__ = ['KeyCode', 'Key', 'DisplayView', 'KeypadView']

# 15 digits + decimal separator + minus sign
_MAX_DISPLAY_ITEMS = 17
""" Number of items / characters that fits on the display """

_DEFAULT_FONTS = {'Windows': 'Consolas', 'Darwin': 'Courier', 'Linux': 'Courier'}
_DEFAULT_FONT = _DEFAULT_FONTS.get(_SYSTEM, 'Courier')


class KeyCode(StrEnum):
    """ IDs and labels of all calculator keypad keys """
    ONE = '1'
    TWO = '2'
    THREE = '3'
    FOUR = '4'
    FIVE = '5'
    SIX = '6'
    SEVEN = '7'
    EIGHT = '8'
    NINE = '9'
    ZERO = '0'
    DECIMAL_POINT = '.'
    NEGATE = '±'
    CLEAR = 'C'
    BACKSPACE = '←'
    EQUALS = '='
    PLUS = '+'
    MINUS = '-'
    MULTIPLY = '×'
    DIVIDE = '÷'


class DisplayView(Protocol):
    """
    Interface / protocol to decouple from TKInter dependencies.
    See TkDisplayView for an actual implementation
    """
    @property
    def tk_variable(self) -> Any:
        """ Property used as adapter between controller and display widget """

    def update(self, text: str) -> None:
        """ Property used as adapter between controller and display widget """

    @property
    def max_items(self) -> int:
        """ Property holding maximal number of items a display can show """


class Key(Protocol):
    """
    Interface / protocol to decouple from TKInter dependencies.
    See TkKeyButton for an actual implementation
    """

    @property
    def code(self) -> KeyCode:
        """ Property with ID of the actual Key """

    def press(self):
        """ Switches button visualization to 'pressed' state """

    def release(self):
        """ Deactivates the 'pressed' state of a button """


class KeypadView(Protocol):
    """
    Interface / protocol to decouple from TKInter dependencies
    See TkKeypadView for an actual implementation
    """
    def register(self, key: Key) -> None:
        """ Adds new button widget to this view """

    def press(self, code: KeyCode) -> None:
        """ Switches button identified by its pad_key value into 'pressed' visual state """

    def release_all(self) -> None:
        """ Switches all registered buttons into 'not pressed' visual state """


class TkDisplayView:
    """
    View class serving as an interface between a calculator
    controller and a display tkk widget.

    This class implements the DisplayView protocol.
    """
    def __init__(self):
        self._display_contents = tk.StringVar(value='0')

    @property
    def tk_variable(self) -> tk.StringVar:
        """
        Returns a tk.StringVar object which should
        be used to couple DisplayView to a widget.
        """
        return self._display_contents

    def update(self, text: str) -> None:
        """
        Converts given text into 'suitable format' and
        sends it to the display widget.
        """
        display_value = text.strip()[:_MAX_DISPLAY_ITEMS]
        self._display_contents.set(display_value if display_value else '0')

    @property
    def max_items(self) -> int:
        return _MAX_DISPLAY_ITEMS


class TkKeypadView:
    """
    View class serving as an interface between the calculator controller
    and the ttk widget buttons grouped into the calculator keypad.

    This class implements the DisplayView protocol.
    """
    def __init__(self):
        self._buttons: dict[KeyCode, Key] = dict()

    def register(self, key: Key) -> None:
        """ Adds new button widget to this view """
        self._buttons[key.code] = key

    def press(self, code: KeyCode) -> None:
        """ Switches button identified by its pad_key value into 'pressed' visual state """
        if code in self._buttons:
            self._buttons[code].press()

    def release_all(self) -> None:
        """ Switches all registered buttons into 'not pressed' visual state """
        for button in self._buttons.values():
            button.release()


class TkDisplay(ttk.Frame):
    """ Custom Display TTK Widget. """
    def __init__(self, master: tk.Tk, contents: tk.StringVar):
        super().__init__(master=master)
        font_ = (_DEFAULT_FONT, 24)
        width_ = _MAX_DISPLAY_ITEMS
        display = ttk.Label(master=self, width=width_, font=font_,
                            padding=(5, 1), background='gray85',
                            anchor='e', textvariable=contents)
        display.pack(expand=True, fill='both')
        self.pack(padx=10, pady=(10, 0), fill='x')


class TkKey(ttk.Button):
    """ Custom TTK Widget representing Key (button). """
    def __init__(
            self,
            master: ttk.Widget,
            style: str,
            code: KeyCode,
            command: Callable[[KeyCode], None],
            *bind_values: str
    ):
        super().__init__(master=master, style=style, text=code, command=lambda: command(code))
        self._code = code
        bind_keys = list(str(code)) if len(bind_values) == 0 else bind_values
        for bind_key in bind_keys:
            master.bind_all(sequence=bind_key, func=self._simulate_click, add='+')

    @property
    def code(self) -> KeyCode:
        """ Property with ID of the actual Key """
        return self._code

    def press(self):
        """ Switches button visualization to 'pressed' state """
        if 'pressed' in self.state():
            return
        self.state(statespec=('pressed',))

    def release(self):
        """ Deactivates the 'pressed' state of a button """
        self.state(statespec=('!pressed',))

    def _simulate_click(self, _):
        self.press()
        # why 80ms? 'cause it feels "just right"
        self.after(ms=80, func=self._simulate_invoke)

    def _simulate_invoke(self):
        self.release()
        self.invoke()


class TkKeypad(ttk.Frame):
    """ Custom TTK Widget representing whole calculator keypad. """
    def __init__(
            self,
            master: tk.Tk,
            register: Callable[[Key], None],
            command: Callable[[KeyCode], None]
    ):
        super().__init__(master, padding=4, borderwidth=4)
        self._command = command
        self._font = (_DEFAULT_FONT, 14, 'bold')
        # padding of buttons was 'fine-tuned' so that keypad aligns with display
        self._padding = (35, 20)
        self._register = register

        for col in range(4):
            self.columnconfigure(col)
        for row in range(5):
            self.rowconfigure(row)

        self._build_numeric_buttons()
        self._build_operator_buttons()
        self._build_control_buttons()
        self.pack(expand=True, fill='both')

    def _build_numeric_buttons(self):
        """
        Hardcoded key-bindings:
        'S' and 's' to '±' (invert sign / negate) button
        '.' and ',' to '.' (decimal point) button
        """
        # TKInter requires specific style suffix based on the component!
        style_id = 'Num.Toolbutton'
        style = ttk.Style()
        style.configure(
            style=style_id, font=self._font, padding=self._padding,
            background='gray85'
        )
        TkKey(self, style_id, KeyCode.NEGATE, self._command, 'S', 's').grid(row=0, column=2)
        TkKey(self, style_id, KeyCode.SEVEN, self._command).grid(row=1, column=0)
        TkKey(self, style_id, KeyCode.EIGHT, self._command).grid(row=1, column=1)
        TkKey(self, style_id, KeyCode.NINE, self._command).grid(row=1, column=2)
        TkKey(self, style_id, KeyCode.FOUR, self._command).grid(row=2, column=0)
        TkKey(self, style_id, KeyCode.FIVE, self._command).grid(row=2, column=1)
        TkKey(self, style_id, KeyCode.SIX, self._command).grid(row=2, column=2)
        TkKey(self, style_id, KeyCode.ONE, self._command).grid(row=3, column=0)
        TkKey(self, style_id, KeyCode.TWO, self._command).grid(row=3, column=1)
        TkKey(self, style_id, KeyCode.THREE, self._command).grid(row=3, column=2)
        TkKey(self, style_id, KeyCode.ZERO, self._command).grid(row=4, column=0)
        TkKey(self, style_id, KeyCode.DECIMAL_POINT, self._command, '.', ',').grid(row=4, column=1)

    def _build_operator_buttons(self):
        """
        Hardcoded key-bindings:
        '/' to '÷' (division) button
        '*' to  '×' (multiplication) button
        """
        # TKInter requires specific style suffix based on the component!
        style_id = 'Op.Toolbutton'
        style = ttk.Style()
        style.configure(
            style=style_id, font=self._font, padding=self._padding,
            background='lightsteelblue4'
        )
        btn = TkKey(self, style_id, KeyCode.DIVIDE, self._command, '/')
        btn.grid(row=0, column=3)
        self._register(btn)
        btn = TkKey(self, style_id, KeyCode.MULTIPLY, self._command, '*')
        btn.grid(row=1, column=3)
        self._register(btn)
        btn = TkKey(self, style_id, KeyCode.MINUS, self._command)
        btn.grid(row=2, column=3)
        self._register(btn)
        btn = TkKey(self, style_id, KeyCode.PLUS, self._command)
        btn.grid(row=3, column=3)
        self._register(btn)

    def _build_control_buttons(self):
        """
        Hardcoded key-bindings:
        'C', 'c' and '<Delete>' to 'C' (clear calculator state) button
        '<BackSpace>' and <Left> to  '←' (delete last digit) button
        '=' and '<Return>' to '=' (calculate result) button
        """
        # TKInter requires specific style suffix based on the component!
        style_id = 'Ctrl.Toolbutton'
        style = ttk.Style()
        style.configure(
            style=style_id, font=self._font, padding=self._padding,
            background="gray85", foreground='orange2'
        )
        TkKey(self, style_id, KeyCode.CLEAR, self._command, 'C', 'c', '<Delete>').grid(row=0, column=0)
        TkKey(self, style_id, KeyCode.BACKSPACE, self._command, '<BackSpace>', '<Left>').grid(row=0, column=1)

        style_id = 'Eq.Toolbutton'
        style.configure(
            style=style_id, font=self._font, padding=self._padding,
            background='lightsteelblue3', anchor='center'
        )
        btn = TkKey(self, style_id, KeyCode.EQUALS, self._command, '=', '<Return>')
        btn.grid(row=4, column=2, columnspan=2, sticky="nsew")

