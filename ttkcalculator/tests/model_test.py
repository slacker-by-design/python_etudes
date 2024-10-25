""" Tests covering ttkcalculator.model module """

from decimal import Decimal

import pytest

import ttkcalculator.model as model
from ttkcalculator.model import Calculator, Operator, Error


# helper factory function
def _calculator(
        first_: str,
        operator_: str,
        second_: str = '') -> Calculator:
    calculator_ = Calculator()
    calculator_.replace_operand(first_)
    calculator_.add_operator(operator_)
    if second_:
        calculator_.replace_operand(second_)
    return calculator_


class TestCalculator:
    """ Trivial "Calculator" functionality checks """

    def test_empty_operator(self):
        calculator_ = Calculator()
        assert calculator_.operator is None

    @pytest.mark.parametrize('operator_', list(Operator))
    def test_add_operator(self, operator_):
        # setup
        calculator_ = Calculator()
        # run
        calculator_.add_digit('1')
        calculator_.add_operator(operator_)
        calculator_.add_digit('2')
        # evaluate
        first, second = calculator_.operands
        assert (first, second, calculator_.operator) == ('1', '2', operator_)

    def test_add_invalid_operator(self):
        # setup
        calculator_ = Calculator()
        # run
        calculator_.add_digit('1')
        success = calculator_.add_operator('#')
        calculator_.add_digit('2')
        # evaluate
        first, second = calculator_.operands
        new_op = calculator_.operator
        assert (first, second, new_op, success) == ('12', '', None, False)

    def test_clear(self):
        # setup
        calculator_ = _calculator('123', '-', '2')
        # run
        calculator_.clear()
        # evaluate
        first, second = calculator_.operands
        operator = calculator_.operator
        assert (first, second, operator) == ('', '', None)

    def test_precision(self):
        calculator_ = Calculator(precision=5)
        assert calculator_.precision == 5

    @pytest.mark.parametrize(
        ('given', 'expected', 'status'),
        [('1234', '123', True), ('1', '', True), ('', '', False)]
    )
    def test_delete_last_entry(self, given, expected, status):
        # setup
        calculator_ = Calculator()
        for digit in given:
            calculator_.add_digit(digit)
        # run
        success = calculator_.delete_last_entry()
        # evaluate
        assert (calculator_.operand, success) == (expected, status)

    def test_delete_decimal_point(self):
        # setup
        calculator_ = Calculator()
        calculator_.add_digit('2')
        calculator_.add_decimal_point()
        calculator_.add_digit('5')
        # run
        calculator_.delete_last_entry()
        success = calculator_.delete_last_entry()
        # evaluate
        assert (calculator_.operand, success) == ('2', True)


class TestCalculatorOperand:
    """ Trivial "Calculator" tests of operand logic """

    def test_empty_operands(self):
        calculator_ = Calculator()
        first, second = calculator_.operands
        assert (first, second) == ('', '')

    def test_implicit_operand_is_zero(self):
        calculator_ = Calculator()
        calculator_.add_operator(Operator.ADD)
        assert calculator_.operands == ('0', '')

    def test_replace_operand(self):
        # setup
        calculator_ = Calculator()
        calculator_.add_digit('2')
        calculator_.add_decimal_point()
        calculator_.add_digit('2')
        # run
        success = calculator_.replace_operand('321.123')
        # evaluate
        assert (calculator_.operand, success) == ('321.123', True)

    def test_replace_operand_failed(self):
        # setup
        calculator_ = Calculator()
        calculator_.add_digit('2')
        calculator_.add_decimal_point()
        calculator_.add_digit('2')
        # run
        success = calculator_.replace_operand('O.1') # note O != 0
        # evaluate
        assert (calculator_.operand, success) == ('2.2', False)

    def test_replace_operands(self):
        # setup
        calculator_ = Calculator()
        # run
        calculator_.add_digit('9')
        calculator_.replace_operand('123.45')
        calculator_.add_operator(Operator.ADD)
        calculator_.add_digit('8')
        calculator_.replace_operand('321.45')
        # evaluate
        first, second = calculator_.operands
        assert (first, second) == ('123.45', '321.45')


class TestCalculatorResult:
    """ Essential Calculator flows """

    def test_missing_operands(self):
        calculator_ = Calculator()
        assert calculator_.result == Error.INVALID_STATE

    def test_missing_operator(self):
        calculator_ = Calculator()
        calculator_.replace_operand('12.3')
        assert calculator_.result == Error.INVALID_STATE

    @pytest.mark.parametrize(
        ('operand_', 'operator_', 'expected'),
            [
                ('10.0', Operator.ADD, '20'),
                ('10.0', Operator.SUBTRACT, '0'),
                ('10.0', Operator.MULTIPLY, '100'),
                ('10.0', Operator.DIVIDE, '1'),
                ('5.3', Operator.ADD, '10.6')
            ]
    )
    def test_only_first_operand(self, operand_, operator_, expected):
        # setup
        calculator_ = _calculator(operand_, operator_)
        # run & verify
        assert calculator_.result == expected

    @pytest.mark.parametrize(
        ('first', 'operator', 'second', 'expected'),
            [
                ('1', Operator.ADD, '2', '3'),
                ('1', Operator.SUBTRACT, '2.0', '-1'),
                ('2.0', Operator.MULTIPLY, '-2', '-4'),
                ('5', Operator.DIVIDE, '2', '2.5'),
                ('25', Operator.DIVIDE, '3', '8.33333333333333')
            ]
         )
    def test_both_operands(self, first, operator, second, expected):
        # setup
        calculator_ = _calculator(first, operator, second)
        # run & verify
        assert calculator_.result == expected

    def test_division_by_zero(self):
        # setup
        calculator_ = _calculator('20', Operator.DIVIDE, '0')
        # run & verify
        assert calculator_.result == Error.DIVISION_BY_ZERO

    def test_result_too_big(self):
        # setup
        calculator_ = Calculator(precision=15)
        calculator_.replace_operand('987651234567890')
        calculator_.add_operator(Operator.MULTIPLY)
        calculator_.replace_operand('2')
        # run & verify
        assert calculator_.result == Error.RESULT_TOO_LARGE


class TestOperand:
    """ Essential Operand tests """

    def test_invert_sign(self):
        # setup
        operand_ = model.operand(number='123')
        # run
        first = str(operand_)
        operand_.invert_sign()
        second = str(operand_)
        operand_.invert_sign()
        third = str(operand_)
        # evaluate
        assert (first, second, third) == ('123', '-123', '123')

    def test_empty_operand_ignores_invert_sign(self):
        operand_ = model.Operand()
        success = operand_.invert_sign()
        assert (str(operand_), success) == ('', False)

    @pytest.mark.parametrize(
        ('given', 'expected'),
        [('123', '12'), ('123.0', '123.'),
         ('123.45', '123.4'), ('9', ''), ('0.', '0')]
    )
    def test_delete_last(self, given, expected):
        # setup
        operand_ = model.operand(number=given)
        # run
        success = operand_.delete_last()
        value = str(operand_)
        # evaluate
        assert (value, success) == (expected, True)

    def test_delete_last_fail(self):
        # setup
        operand_ = model.operand()
        before = str(operand_)
        # run
        success = operand_.delete_last()
        # evaluate
        after = str(operand_)
        assert (after, success) == (before, False)

    @pytest.mark.parametrize(
        ('given', 'expected'),
        [('123',Decimal('123')),
         ('-123.0', Decimal('-123.0')),
         ('1234567890.12345', Decimal('1234567890.12345')),
         ('', None)]
    )
    def test_to_decimal(self, given, expected):
        operand_ = model.operand(number=given)
        actual = operand_.to_decimal()
        assert actual == expected

    @pytest.mark.parametrize(
        ('given', 'expected'),
        [('-1', 1), ('123', 3), ('123.45', 5), ('0.', 1), ('', 0)]
    )
    def test_len(self, given, expected):
        operand_ = model.operand(number=given)
        assert len(operand_) == expected

    @pytest.mark.parametrize(
        ('given', 'expected'),
        [('-123', '-123'), ('123.45', '123.45'), ('0.', '0.'), ('', '')]
    )
    def test_str(self, given, expected):
        operand_ = model.operand(number=given)
        assert str(operand_) == expected

    @pytest.mark.parametrize('character', list('abc/*-+ ,DEF'))
    def test_append_non_digits(self, character):
        operand_ = model.operand('321')
        success = operand_.append(character)
        assert (str(operand_), success) == ('321', False)

    def test_can_append_only_one_decimal_separator(self):
        operand_ = model.operand('0.5')
        success = operand_.append('.')
        assert (str(operand_), success) == ('0.5', False)

    def test_append_decimal_separator_adds_leading_zero(self):
        operand_ = model.operand('')
        success = operand_.append('.')
        assert (str(operand_), success) == ('0.', True)

    def test_append_prevents_leading_zero(self):
        operand_ = model.operand('0')
        success = operand_.append('0')
        assert (str(operand_), success) == ('0', False)

    def test_append_replaces_leading_zero(self):
        operand_ = model.operand('0')
        success = operand_.append('5')
        assert (str(operand_), success) == ('5', True)

    def test_append_precision_limit(self):
        # setup
        operand_ = model.operand(number='12', precision=2)
        # run
        success = operand_.append('3')
        value = str(operand_)
        # evaluate
        assert (value, success) == ('12', False)

