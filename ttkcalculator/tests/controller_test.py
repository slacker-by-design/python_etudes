""" Tests covering ttkcalculator.controller module """

import pytest

from ttkcalculator.controller import KeypadController, Error
from ttkcalculator.model import Calculator
from ttkcalculator.view import KeyCode
from view_mocks import DummyDisplay, DummyKeypad


@pytest.fixture
def calculator():
    return Calculator()

@pytest.fixture
def display():
    return DummyDisplay(17) # same as real display

@pytest.fixture
def keypad():
    return DummyKeypad()

@pytest.fixture
def controller(display, keypad, calculator):
    return KeypadController(display_view=display, keypad_view=keypad, calculator=calculator)


def test_init_validation(keypad):
    # setup
    display_ = DummyDisplay(5)
    calculator_ = Calculator(precision=display_.max_items)
    # run & evaluate
    with pytest.raises(ValueError, match='.*DisplayView.*Calculator.*precision'):
        KeypadController(
            display_view=display_,
            keypad_view=keypad,
            calculator=calculator_)

@pytest.mark.parametrize(
    ('user_input', 'expected'),
    [
        ('1+1=', '2'),
        ('3-4=', '-1'),
        ('5×6=', '30'),
        ('0.5÷0.2=', '2.5'),
        ('3±×5.0±=', '15'),
        ('.5+=', '1'),
        ('.5-=', '0'),
        ('7.×=', '49'),
        ('8.0±÷=', '1'),
        ('1.5+=+2.5=+=-1=', '10'),
        ('.5=+=÷0.5=', '2')
    ]
)
def test_calculations(display, controller, user_input, expected):
    # setup & run
    for key in user_input:
        controller.key_pressed(KeyCode(key))
    # evaluate
    assert display.update_history[-1] == expected

@pytest.mark.parametrize(
    ('user_input', 'expected'),
    [
        ('2÷0=', Error.DIVISION_BY_ZERO),
        ('999999999999999+1=', Error.RESULT_TOO_LARGE)
    ]
)
def test_calculation_errors(display, controller, user_input, expected):
    # setup & run
    for key in user_input:
        controller.key_pressed(KeyCode(key))
    # evaluate
    assert display.update_history[-1] == expected

def test_calculation_display_history(display, controller):
    # setup & run
    expected = ['3', '3.', '3.2', '3.2', '0.', '0.2', '3']
    for key in '3.2-.2=':
        controller.key_pressed(KeyCode(key))
    # evaluate
    assert display.update_history == expected

@pytest.mark.parametrize(
    'key',
    [KeyCode.PLUS, KeyCode.MINUS, KeyCode.DIVIDE, KeyCode.MULTIPLY]
)
def test_operator_key_stays_pressed(keypad, controller, key):
    controller.key_pressed(key)
    assert keypad.press_history == [key]

@pytest.mark.parametrize(
    'key',
    [KeyCode.ONE, KeyCode.TWO, KeyCode.THREE,
     KeyCode.FOUR, KeyCode.FIVE, KeyCode.SIX,
     KeyCode.SEVEN, KeyCode.EIGHT, KeyCode.NINE,
     KeyCode.ZERO, KeyCode.DECIMAL_POINT,
     KeyCode.NEGATE, KeyCode.CLEAR,
     KeyCode.BACKSPACE, KeyCode.EQUALS
    ]
)
def test_non_operator_keys_not_pressed(keypad, controller, key):
    controller.key_pressed(key)
    assert not keypad.press_history

@pytest.mark.parametrize(
    ('user_input', 'expected'),
    [
        ('7×=', 1), ('7÷=', 1), ('7+=', 1), ('7-=', 1),
        ('7×=+7=', 2), ('7+7=+7=+7=-7=', 4), ('7+C', 1),
        ('2-C3×C4÷C', 3), ('7+←', 0), ('7-←', 0),
        ('7×←', 0), ('7÷←', 0), ('7+1234567890', 0),
        ('7-0.987654321', 0), ('7+7±±', 0)
     ]
)
def test_operator_key_release(keypad, controller, user_input, expected):
    # setup & run
    for key in user_input:
        controller.key_pressed(KeyCode(key))
    # evaluate
    assert keypad.release_history == expected

def test_only_one_operator_key_stays_pressed(keypad, controller):
    # setup
    controller.key_pressed(KeyCode.FIVE)
    controller.key_pressed(KeyCode.DIVIDE)
    # run
    controller.key_pressed(KeyCode.DIVIDE)
    controller.key_pressed(KeyCode.MULTIPLY)
    controller.key_pressed(KeyCode.DIVIDE)
    controller.key_pressed(KeyCode.MINUS)
    controller.key_pressed(KeyCode.PLUS)
    # verify
    assert keypad.press_history == [KeyCode.DIVIDE]

@pytest.mark.parametrize(
    ('user_input', 'expected'),
    [
        ('543210←', '54321'), ('543210←←←', '543'),
        ('54321.←', '54321'), ('5432.10←←←', '5432'),
        ('3±210←', '-321'), ('32±2←10←', '-321'),
        ('3←', ''), ('3±←', '')
    ]
)
def test_backspace(display, controller, user_input, expected):
    # setup & run
    for key in user_input:
        controller.key_pressed(KeyCode(key))
    # evaluate
    assert display.update_history[-1] == expected

@pytest.mark.parametrize(
    ('user_input', 'error'),
    [
        ('2÷0=', Error.DIVISION_BY_ZERO),
        ('999999999999999+1=', Error.RESULT_TOO_LARGE)
    ]
)
def test_clear_drops_errors(display, controller, user_input, error):
    # setup
    for key in user_input:
        controller.key_pressed(KeyCode(key))
    # run
    controller.key_pressed(KeyCode.CLEAR)
    # evaluate
    assert display.update_history[-2:] == [str(error), '']

@pytest.mark.parametrize(
    'user_input',
    ['5+15', '2÷0=', '999999999999999+1=']
)
def test_clear_resets_calculator_state(calculator, controller, user_input):
    # setup
    for key in user_input:
        controller.key_pressed(KeyCode(key))
    # run
    controller.key_pressed(KeyCode.CLEAR)
    # evaluate
    first, second = calculator.operands
    operator = calculator.operator
    assert (first, second, operator) == ('', '', None)

