"""
This module contains items which serve as the model layer of the calculator
application. Namely, the Calculator holds the operands and operators and can
calculate the resulting new value.
"""
from enum import StrEnum, IntEnum, auto
from decimal import Decimal, Context, Overflow

# Indicate what's relevant for other modules to import
__all__ = ['Operator', 'Error', 'Calculator']


class Operator(StrEnum):
    """ Operators supported by the calculator engine """
    ADD = '+'
    SUBTRACT = '-'
    MULTIPLY = '*'
    DIVIDE = '/'


class Error(IntEnum):
    """ IDs of different calculator errors """
    DIVISION_BY_ZERO = auto()
    RESULT_TOO_LARGE = auto()
    INVALID_NUMBER = auto()
    INVALID_STATE = auto()


_DEFAULT_PRECISION = 15
""" Default max number of digits for calculator engine """

_DIGIT_CHARS = set('0123456789.')
_DECIMAL_SEPARATOR = '.'
_MINUS_SIGN = '-'
_NO_SIGN = ''


class Operand:
    """
    Custom implementation of a decimal number with behaviour
    tailored for the specific GUI calculator workflows.

    Main features
    - Number is composed digit by digit
    - It's possible to remove the last (least significant) digit
    - It's possible to invert sign
    - Precision (maximal number of digits) is strictly limited

    Please note that methods of this class *intentionally* don't
    raise exceptions to handle invalid states. They rely on return
    values instead.
    """
    def __init__(self, precision = _DEFAULT_PRECISION):
        """
        Initializes Operand instance.

        The precision represents the maximal number of digits this
        instance is allowed to work with (not counting sign and
        decimal point).
        """
        self._sign: str = _NO_SIGN
        self._digits: list[str] = []
        self._decimal_idx: int = 0
        self._precision: int = precision

    def invert_sign(self) -> bool:
        """
        Inverts operand's sign.

        A positive sign (i.e. '') becomes negative (i.e. '-') and vice versa.
        A sign is not changes in case the operand is empty (i.e. no digits).
        Returns True when sign has been changed, False otherwise.
        """
        if not self._digits:
            return False
        self._sign = _NO_SIGN if self._sign else _MINUS_SIGN
        return True

    def append(self, digit: str) -> bool:
        """
        Adds a digit or a decimal separator to the operand.

        Method ensures few rules when adding a digit / decimal separator:
         - Maximal number of digits that can be accepted is given by the
           precision given during the Operand instance creation
         - Leading zeroes are not accepted (i.e. cannot have '00', '00', '01',
           etc., but '0', '0.0', '0.00', etc. are OK)
         - When a '.' is added to a blank operand, it's automatically prefixed
           by '0' (i.e. adding '.' will change operand's contents to '0.')

        Returns True in case a digit has been added successfully, False otherwise.
        """
        if digit not in _DIGIT_CHARS:
            return False
        if digit == _DECIMAL_SEPARATOR:
            # ignore consequent '.' if operator already has one
            if self._decimal_idx:
                return False
            # avoid operand value '.' by turning it into '0.'
            if not self._digits:
                self._digits.append('0')
            self._decimal_idx = len(self._digits)
            return True
        # guard the precision (no. of digits)
        if len(self._digits) >= self._precision:
            return False
        if not self._decimal_idx and self._digits == ['0']:
            # avoid operand values like '00' or '000'
            if digit == '0':
                return False
            # avoid operand values like '01'
            del self._digits[0]
        self._digits.append(digit)
        return True

    def delete_last(self) -> bool:
        """
        Removes last digit (or decimal separator).
        Returns True in case a digit has been removed, False otherwise.
        """
        if not self._digits:
            return False
        # is the decimal point at the very end of operand?
        if len(self._digits) == self._decimal_idx:
            self._decimal_idx = 0
        else:
            del self._digits[-1]
        if not self._digits:
            self._sign = _NO_SIGN
        return True

    def to_decimal(self) -> Decimal | None:
        """
        Returns a Decimal representation of the operand or None,
        in case the operand doesn't contain anything yet.
        """
        return Decimal(str(self)) if self._digits else None

    def copy(self):
        """ Returns a deep copy of the operand. """
        copy_ = Operand()
        copy_._sign = self._sign
        copy_._digits =  self._digits.copy()
        copy_._decimal_idx = self._decimal_idx
        copy_._precision = self._precision
        return copy_

    def __len__(self) -> int:
        """
        Returns number of digits operand currently holds.

        It was only implemented as a convenient way of determining
        the emptiness of an operand.
        """
        return len(self._digits)

    def __str__(self) -> str:
        """ Returns a string representation of the operand. """
        if self._decimal_idx:
            num_int = self._digits[:self._decimal_idx]
            num_dec = self._digits[self._decimal_idx:]
            num_str = f'{''.join(num_int)}.{''.join(num_dec)}'
        else:
            num_str = ''.join(self._digits)
        return f'{self._sign}{num_str}'


def operand(number: str | None = None, precision: int = _DEFAULT_PRECISION) -> Operand|Error:
    """
    Convenience factory method for Operand class.

    The number parameter can be a blank string or None (representing blank
    new Operand) or a string containing well-formed decimal number (see
    Operand for more details). The precision represents a maximal number
    of digits the Operand will be able to hold (not counting sign and decimal
    point).

    Returns new Operand instance or an Error, in case the number parameter
    didn't contain a well-formed decimal or integer number.
    """
    operand_ = Operand(precision=precision)
    if not number or not number.strip():
        return operand_
    digits = list(number.strip())
    if digits[0] == '-':
        add_sign = True
        del digits[0]
    else:
        add_sign = False
    if not digits:
        return Error.INVALID_NUMBER
    for d in digits:
        if not operand_.append(d):
            return Error.INVALID_NUMBER
    if add_sign:
        operand_.invert_sign()
    return operand_


class Calculator:
    """
    The Calculator holds operands and operator and provides
    the means of updating and reading their values. Moreover, it's
    able to calculate a result of '<operand1> <operator> <operand2>'
    or '<operand1> <operator>' expressions.

    Please note that methods of this class *intentionally* don't
    raise exceptions to handle invalid states. They rely on return
    values instead.
    """
    def __init__(self, precision: int = _DEFAULT_PRECISION):
        self._precision = precision
        first_ = Operand(precision=self._precision)
        second_ = Operand(precision=self._precision)
        self._operands: tuple[Operand, Operand] = (first_, second_)
        self._current_operand: Operand = self._operands[0]
        self._operator: Operator | None = None
        self._decimal_point = '.'

    @property
    def precision(self) -> int:
        """
        Returns the precision value which represents the maximal
        number of digits a calculator operand or result can have.
        """
        return self._precision

    def clear(self) -> None:
        """ Performs a complete reset of the calculator state """
        self._operands = (Operand(precision=self._precision), Operand(precision=self._precision))
        self._current_operand = self._operands[0]
        self._operator = None

    @property
    def operator(self) -> str | None:
        """
        Provides a string representation of the operator.

        Returns None when operator hasn't been set.
        """
        return str(self._operator) if self._operator else None

    def add_operator(self, operator: Operator|str) -> bool:
        """
        Adds an operator to the calculator expression and
        switches the calculator's state to expect an entry
        of the next operand.

        Returns True in case an operator has been added
        (and the operands switched), False otherwise
        (e.g. there's already an operator present, value
        passed through operator parameter didn't contain
        a valid operator).
        """
        try:
            valid_operator = Operator(operator)
        except ValueError:
            return False
        if self._operator is None:
            operand_ = self._current_operand
            if not operand_:
                operand_.append('0')
            self._operator = valid_operator
            self._current_operand = self._operands[1]
        return True

    def add_digit(self, digit: str|int) -> bool:
        """
        Adds a digit to the end of the current operand.

        Returns True in case everything went OK, False
        in case the digit value wasn't an actual digit
        or if the calculator's operand capacity has been
        reached (i.e. cannot accommodate more digits).
        """
        return self._current_operand.append(str(digit))

    def add_decimal_point(self) -> bool:
        """
        Adds a decimal point to the current operand. If the operand
        already contains a decimal point, the current request is ignored
        and the method returns False. A True is returned upon a success.
        """
        return self._current_operand.append(self._decimal_point)

    @property
    def operand(self) -> str:
        """ Provides current operand's value converted to a string """
        return str(self._current_operand)

    def replace_operand(self, new_value: str) -> bool:
        """
        Sets the current operand to a new value. Previous
        contents of the current operand is lost.

        Returns false in case the new_value parameter didn't
        contain a proper number (decimal or integer) or if
        it was too long. True is only returned when the contents
        of the current operand has been replaced with the new value.
        """
        new_operand = operand(new_value, self._precision)
        if isinstance(new_operand, Error):
            return False
        if self._current_operand == self._operands[1]:
            self._operands = (self._operands[0], new_operand)
        else:
            self._operands = (new_operand, self._operands[1])
        self._current_operand = new_operand
        return True

    def delete_last_entry(self) -> bool:
        """
        Deletes the last (i.e. of lowest order) digit or a decimal point
        from the current operand.

        Returns False in case there was nothing left to delete, True otherwise.
        """
        return self._current_operand.delete_last()

    def invert_sign(self) -> None:
        """
        Changes the sign of current operand.
        Change no sign (i.e. +) to - and vice versa
        """
        self._current_operand.invert_sign()

    @property
    def operands(self) -> tuple[str, str]:
        """ Returns a tuple with string representation of the operands. """
        return str(self._operands[0]), str(self._operands[1])

    @property
    def decimal_result(self) -> Decimal | Error:
        """
        Evaluates the '<operand> <operator>' or '<operand> <operator> <operand>'
        expression and returns the result as a Decimal.

        An Error instance is returned in case of an error (e.g. division by zero,
        missing operator or operand, unknown operator)
        """
        if not self._operands[0] or not self._operator:
            return Error.INVALID_STATE
        first_num = self._operands[0].to_decimal()
        second_num = self._operands[1].to_decimal() if self._operands[1] else first_num
        match self._operator:
            case Operator.ADD: result_ = first_num + second_num
            case Operator.SUBTRACT: result_ = first_num - second_num
            case Operator.MULTIPLY: result_ = first_num * second_num
            case Operator.DIVIDE if second_num.is_zero(): result_ = Error.DIVISION_BY_ZERO
            case Operator.DIVIDE: result_ = first_num / second_num
            case _: result_ = Error.INVALID_STATE
        return self._ensure_precision_boundaries(result_)

    def _ensure_precision_boundaries(self, number: Decimal | Error) -> Decimal | Error:
        """ Makes sure given number fits the calculator's digit capacity. """
        if isinstance(number, Error):
            return number
        # check the digits of the integral part of the result to ensure
        # they can be displayed.
        digits = number.to_integral_value().as_tuple().digits
        if len(digits) > self._precision:
            return Error.RESULT_TOO_LARGE
        try:
            # shrink the result number's precision and round decimal part
            # if necessary.
            ctx = Context(
                prec=self._precision, Emin=-self._precision,
                Emax=self._precision, traps=[Overflow]
            )
            result = ctx.create_decimal(number)
        except Overflow:
            result = Error.RESULT_TOO_LARGE
        return result

    @property
    def result(self) -> str | Error:
        """
        Evaluates the '<operand> <operator>' or '<operand> <operator> <operand>'
        expression and returns the result as a string.

        A None is returned in case of an error (e.g. division by zero,
        missing operator or operand, unknown operator)
        """
        value = self.decimal_result
        if isinstance(value, Error):
            return value
        int_value = value.to_integral_value()
        beautified = int_value if value == int_value else value.normalize()
        return str(beautified)

