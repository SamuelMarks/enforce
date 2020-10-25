import typing
import unittest
import numbers
import re

from enforce import runtime_validation, config
from enforce.types import EnhancedTypeVar
from enforce.exceptions import RuntimeTypeError


class GeneralTests(unittest.TestCase):
    """
    A container for general tests
    """

    def setUp(self):
        config(reset=True)

    def tearDown(self):
        config(reset=True)

    def test_argument_validation(self):
        self.assertEqual(self.sample_function("11", 1), 12)

        result = 0
        with self.assertRaises(RuntimeTypeError):
            result += self.sample_function(1, 2)

        self.assertEqual(result, 0)

    def test_returns_output_if_no_return_annotation(self):
        """
        Verifies that the wrapped function's output is returned even if there
        is no 'return' annotation
        """

        @runtime_validation
        def example(x: int):
            return x

        self.assertEqual(example(1), 1)

    def test_return_value_validation(self):
        self.assertIsNone(self.sample_function("", None))

        result = 0
        with self.assertRaises(RuntimeTypeError):
            result += self.sample_function("", 1)

        self.assertEqual(result, 0)

    def test_no_type_check(self):
        """
        Verifies that no_type_check is respected
        """

        def get_sample_func():
            def sample(data: int):
                pass

            return sample

        sample_d1 = typing.no_type_check(runtime_validation(get_sample_func()))
        sample_d2 = runtime_validation(typing.no_type_check(get_sample_func()))

        sample_d3 = runtime_validation(get_sample_func())

        sample_d4 = typing.no_type_check_decorator(
            runtime_validation(get_sample_func())
        )
        sample_d5 = runtime_validation(
            typing.no_type_check_decorator(get_sample_func())
        )

        get_sample_func()("str")
        sample_d1("str")
        sample_d2("str")
        with self.assertRaises(RuntimeTypeError):
            sample_d3("str")

    def test_any_code_works_with_modes(self):
        config({"mode": "covariant"})

        @runtime_validation
        def example() -> typing.Optional[str]:
            return None

        example()

    @runtime_validation
    def sample_function(
        self, text: str, data: typing.Union[int, None]
    ) -> typing.Optional[int]:
        try:
            return int(text) + data
        except ValueError:
            if data is None:
                return None
            # Deliberate return type error
            return str(data)


class SimpleTypesTests(unittest.TestCase):
    """
    Tests for the simple types which do not require special processing
    """

    def setUp(self):
        config(reset=True)

    def tearDown(self):
        config(reset=True)

    def test_any(self):
        @runtime_validation
        def sample(data: typing.Any) -> typing.Any:
            return data

        self.assertEqual(sample(100.3), 100.3)
        self.assertIsNone(sample(None))

        @runtime_validation
        def foo(a: typing.Any) -> typing.Any:
            return 10

        foo([10, 20])

        self.assertEqual(foo([10, 20]), 10)

    def test_none(self):
        @runtime_validation
        def sample(data: None) -> None:
            return data

        @runtime_validation
        def sample_bad(data: typing.Any) -> None:
            return data

        self.assertIsNone(sample(None))

        with self.assertRaises(RuntimeTypeError):
            sample_bad(1)

    def test_bool(self):
        @runtime_validation
        def sample(data: bool) -> bool:
            return not data

        @runtime_validation
        def sample_bad(data: typing.Any) -> bool:
            return data

        self.assertFalse(sample(True))

        with self.assertRaises(RuntimeTypeError):
            sample(1)

        with self.assertRaises(RuntimeTypeError):
            sample_bad("string")

    def test_int(self):
        @runtime_validation
        def sample(data: int) -> int:
            return data

        @runtime_validation
        def sample_bad(data: typing.Any) -> int:
            return data

        self.assertEqual(sample(1), 1)
        with self.assertRaises(RuntimeTypeError):
            sample(1.0)

        with self.assertRaises(RuntimeTypeError):
            sample_bad("")

    def test_float(self):
        """
        Floats should accept only floats in invariant mode
        """

        @runtime_validation
        def sample(data: float) -> float:
            return data

        @runtime_validation
        def sample_bad(data: typing.Any) -> float:
            return data

        self.assertEqual(sample(1.0), 1.0)
        with self.assertRaises(RuntimeTypeError):
            sample(1)
        with self.assertRaises(RuntimeTypeError):
            sample("")

        with self.assertRaises(RuntimeTypeError):
            sample_bad("")

        config({"mode": "covariant"})
        sample(1)

    def test_complex(self):
        """
        Complex numbers should accept complex, integers and floats
        """

        @runtime_validation
        def sample(data: complex) -> complex:
            return data

        @runtime_validation
        def sample_bad(data: typing.Any) -> complex:
            return data

        self.assertEqual(sample(1 + 1j), 1 + 1j)
        self.assertEqual(sample(1), 1)
        self.assertEqual(sample(1.0), 1.0)
        with self.assertRaises(RuntimeTypeError):
            sample("")

        with self.assertRaises(RuntimeTypeError):
            sample_bad("")

    def test_string(self):
        @runtime_validation
        def sample(data: str) -> str:
            return data

        @runtime_validation
        def sample_bad(data: typing.Any) -> str:
            return data

        self.assertEqual(sample(""), "")
        with self.assertRaises(RuntimeTypeError):
            sample(1)

        with self.assertRaises(RuntimeTypeError):
            sample_bad(1)

    def test_bytes(self):
        """
        Bytes should accept bytes as well bytearray and memorieview
        """

        @runtime_validation
        def sample(data: bytes) -> bytes:
            return data

        @runtime_validation
        def sample_bad(data: typing.Any) -> bytes:
            return data

        self.assertEqual(sample(b""), b"")
        self.assertEqual(sample(bytearray(2)), bytearray(2))
        self.assertEqual(sample(memoryview(b"")), memoryview(b""))
        with self.assertRaises(RuntimeTypeError):
            sample("")

        with self.assertRaises(RuntimeTypeError):
            sample_bad(1)

    def test_bytearray(self):
        @runtime_validation
        def sample(data: bytearray) -> bytearray:
            return data

        @runtime_validation
        def sample_bad(data: typing.Any) -> bytearray:
            return data

        self.assertEqual(sample(bytearray(2)), bytearray(2))
        with self.assertRaises(RuntimeTypeError):
            sample(b"")

        with self.assertRaises(RuntimeTypeError):
            sample_bad(1)

    def test_memoryview(self):
        @runtime_validation
        def sample(data: memoryview) -> memoryview:
            return data

        @runtime_validation
        def sample_bad(data: typing.Any) -> memoryview:
            return data

        self.assertEqual(sample(memoryview(b"")), memoryview(b""))
        with self.assertRaises(RuntimeTypeError):
            sample(b"")

        with self.assertRaises(RuntimeTypeError):
            sample_bad(1)


class ComplexTypesTests(unittest.TestCase):
    """
    Tests for the simple types which require special processing
    """

    def setUp(self):
        config(reset=True)

    def tearDown(self):
        config(reset=True)

    def get_type_var_func(self, configurable=False, type_var=None):
        if type_var is None:
            A = typing.TypeVar("A")
        else:
            A = type_var

        def type_var_func(data: A) -> A:
            return data

        def configurable_type_var_func(data: typing.Any, type_option: A) -> A:
            return data

        if configurable:
            return runtime_validation(configurable_type_var_func)
        else:
            return runtime_validation(type_var_func)

    def test_checking_mode(self):
        """
        Verifies that settings affect the selected type checking mode - covariant/contravariant
        """

        @runtime_validation
        def func(data: numbers.Integral):
            pass

        @runtime_validation
        def func2(data: typing.Union[float, str]):
            pass

        with self.assertRaises(RuntimeTypeError):
            func(1)

        with self.assertRaises(RuntimeTypeError):
            func(1.0)

        with self.assertRaises(RuntimeTypeError):
            func(True)

        func2("hello")
        func2(1.0)
        with self.assertRaises(RuntimeTypeError):
            func2(1)

        config({"mode": "covariant"})

        func(1)
        func(True)
        with self.assertRaises(RuntimeTypeError):
            func(1.0)

        func2("hello")
        func2(1.0)
        func2(1)

        config({"mode": "contravariant"})

        with self.assertRaises(RuntimeTypeError):
            func(1)

        func(1.0)

        with self.assertRaises(RuntimeTypeError):
            func(True)

        func2("hello")
        func2(1.0)
        with self.assertRaises(RuntimeTypeError):
            func2(1)

        config({"mode": "bivariant"})

        func(1)
        func(1.0)
        func(True)

        func2("hello")
        func2(1.0)
        func2(1)

        config({"mode": "invariant"})

        with self.assertRaises(RuntimeTypeError):
            func(1)

        with self.assertRaises(RuntimeTypeError):
            func(1.0)

        with self.assertRaises(RuntimeTypeError):
            func(True)

        func2("hello")
        func2(1.0)
        with self.assertRaises(RuntimeTypeError):
            func2(1)

    def test_optional(self):
        @runtime_validation
        def sample(data: typing.Optional[int]) -> typing.Optional[int]:
            return data

        @runtime_validation
        def sample_bad(data: typing.Any) -> typing.Union[int]:
            return data

        self.assertEqual(sample(1), 1)
        self.assertIsNone(sample(None))
        with self.assertRaises(RuntimeTypeError):
            sample("")

        with self.assertRaises(RuntimeTypeError):
            sample_bad("")

    def test_tuple(self):
        @runtime_validation
        def sample(data: typing.Tuple[int, str]) -> typing.Tuple[int, str]:
            return data

        @runtime_validation
        def sample_bad(data: typing.Any) -> typing.Tuple[int, str]:
            return data

        @runtime_validation
        def sample_any_in(data: typing.Tuple) -> typing.Tuple:
            return data

        @runtime_validation
        def sample_any_out(data: typing.Any) -> typing.Tuple:
            return data

        self.assertEqual(sample((1, "")), (1, ""))
        with self.assertRaises(RuntimeTypeError):
            sample((1, 1))

        with self.assertRaises(RuntimeTypeError):
            sample(())

        with self.assertRaises(RuntimeTypeError):
            sample([])

        with self.assertRaises(RuntimeTypeError):
            sample_bad((""))

        self.assertEqual(sample_any_in((1, "")), (1, ""))
        with self.assertRaises(RuntimeTypeError):
            sample_any_in(1)

        self.assertEqual(sample_any_out((1,)), (1,))
        with self.assertRaises(RuntimeTypeError):
            sample_any_out(1)

    def test_named_tuple(self):
        from collections import namedtuple

        MyNamedTuple = typing.NamedTuple("MyNamedTuple", [("my_int", int)])

        t = MyNamedTuple(5)
        t1 = namedtuple("MyNamedTuple", "my_int")(5)
        t2 = namedtuple("MyNamedTuple", "my_int")("string")
        t3 = runtime_validation(MyNamedTuple)(5)
        t4 = (5,)
        t5 = "5"

        @runtime_validation
        def sample(data: MyNamedTuple) -> MyNamedTuple:
            return data

        # invariant cases
        sample(t)
        with self.assertRaises(RuntimeTypeError):
            sample(t1)
        with self.assertRaises(RuntimeTypeError):
            sample(t2)
        sample(t3)
        with self.assertRaises(RuntimeTypeError):
            sample(t4)
        with self.assertRaises(RuntimeTypeError):
            sample(t5)

        # Covariant case
        config({"mode": "covariant"})

    def test_typed_named_tuple(self):
        MyNamedTuple = typing.NamedTuple("MyNamedTuple", [("my_int", int)])
        MyNamedTuple = runtime_validation(MyNamedTuple)

        mt = MyNamedTuple(5)
        mt2 = MyNamedTuple(my_int=5)

        self.assertEqual(mt[0], 5)
        self.assertEqual(mt.my_int, 5)

        self.assertEqual(mt2[0], 5)
        self.assertEqual(mt2.my_int, 5)

        with self.assertRaises(RuntimeTypeError):
            MyNamedTuple("string")

        with self.assertRaises(RuntimeTypeError):
            MyNamedTuple(my_int="string")

        with self.assertRaises(AttributeError):
            mt2.my_int = "hello world"

        with self.assertRaises(TypeError):
            MyNamedTuple(2, my_int="string")

    def test_variable_length_tuple(self):
        # TODO: What if tuple is empty?
        @runtime_validation
        def sample_in(data: typing.Tuple[int, ...]) -> typing.Any:
            return data

        @runtime_validation
        def sample_out(data: typing.Any) -> typing.Tuple[int, ...]:
            return data

        good = (1, 3, 4)
        bad = (1, "a", 2)
        empty = ()

        self.assertEqual(sample_in(good), good)
        self.assertEqual(sample_out(good), good)
        self.assertEqual(sample_in(empty), empty)
        self.assertEqual(sample_out(empty), empty)

        with self.assertRaises(RuntimeTypeError):
            sample_in(bad)

        with self.assertRaises(RuntimeTypeError):
            sample_out(bad)

    def test_simple_unbounded_type_var(self):
        type_var_func = self.get_type_var_func()
        bad_type_var_func = self.get_type_var_func(configurable=True)

        self.assertEqual(type_var_func(1), 1)
        self.assertEqual(bad_type_var_func("", "hello world"), "")

        with self.assertRaises(RuntimeTypeError):
            bad_type_var_func("", 1)

    def test_simple_bounded_type_var(self):
        # Invariant case
        A = typing.TypeVar("A", int, str)

        type_var_func = self.get_type_var_func(type_var=A)
        bad_type_var_func = self.get_type_var_func(configurable=True, type_var=A)

        self.assertEqual(type_var_func(1), 1)
        self.assertEqual(type_var_func(""), "")
        self.assertEqual(bad_type_var_func(1, 1), 1)
        self.assertEqual(bad_type_var_func("", ""), "")

        with self.assertRaises(RuntimeTypeError):
            type_var_func(1.0)

        with self.assertRaises(RuntimeTypeError):
            bad_type_var_func(1.0, 1)

    def test_covariant_type_var(self):
        A = typing.TypeVar("A", bound=numbers.Number, covariant=True)

        type_var_func = self.get_type_var_func(type_var=A)

        self.assertEqual(type_var_func(1), 1)
        self.assertEqual(type_var_func(1.0), 1.0)
        self.assertEqual(type_var_func(1 + 1j), 1 + 1j)

        with self.assertRaises(RuntimeTypeError):
            type_var_func("bad")

    def test_contravariant_type_var(self):
        class B:
            pass

        class C(B):
            pass

        class D(C):
            pass

        A = typing.TypeVar("A", bound=C, contravariant=True)

        b = B()
        c = C()
        d = D()

        type_var_func = self.get_type_var_func(type_var=A)

        self.assertIs(type_var_func(c), c)
        self.assertIs(type_var_func(b), b)

        with self.assertRaises(RuntimeTypeError):
            type_var_func(d)

    def test_bivariant_type_var(self):
        class B:
            pass

        class C(B):
            pass

        class D(C):
            pass

        A = EnhancedTypeVar("A", bound=C, covariant=True, contravariant=True)

        b = B()
        c = C()
        d = D()

        type_var_func = self.get_type_var_func(type_var=A)

        self.assertIs(type_var_func(c), c)
        self.assertIs(type_var_func(b), b)
        self.assertIs(type_var_func(d), d)

        with self.assertRaises(RuntimeTypeError):
            type_var_func("bad")


class ListTypesTests(unittest.TestCase):
    def setUp(self):
        @runtime_validation
        def str_func(x: typing.List[str]) -> str:
            return x[0]

        self.str_func = str_func

        @runtime_validation
        def int_func(x: typing.List[int]) -> int:
            return x[0]

        self.int_func = int_func

        def int_str_func(x: typing.List[typing.Union[str, int]]) -> int:
            return int(x[0])

        self.union_func = int_str_func

    def test_str_list(self):
        self.str_func(["a"])
        self.str_func(["a", "b", "c"])

        with self.assertRaises(RuntimeTypeError):
            self.str_func(3)

        with self.assertRaises(RuntimeTypeError):
            self.str_func("3")

        with self.assertRaises(RuntimeTypeError):
            self.str_func([1, 2, 3])

        with self.assertRaises(RuntimeTypeError):
            self.str_func([1, "b", 5.0])

        with self.assertRaises(RuntimeTypeError):
            self.str_func(["a", 1, "b", 5.0])

    def test_int_list(self):
        self.int_func([1])
        self.int_func([1, 2, 3])

        with self.assertRaises(RuntimeTypeError):
            self.int_func(5)

        with self.assertRaises(RuntimeTypeError):
            self.int_func("5")

        with self.assertRaises(RuntimeTypeError):
            self.int_func(["1", "2", "a"])

        with self.assertRaises(RuntimeTypeError):
            self.int_func(["a", 1, "b", 5.0])

    def test_union_func(self):
        self.union_func([1])
        self.union_func([1, 2, 3])
        self.union_func(["1"])
        self.union_func(["1", "2", "3"])
        self.union_func([1, "2", 3, "4"])
        self.union_func(["1", 2, "3", 4])

        with self.assertRaises(RuntimeTypeError):
            self.int_func(1)

        with self.assertRaises(RuntimeTypeError):
            self.int_func("a")

        with self.assertRaises(RuntimeTypeError):
            self.int_func([[1, 2, 3], "4"])

        with self.assertRaises(RuntimeTypeError):
            self.int_func(["a", "b", {3, 4, 5}])

    def test_list_of_lists(self):
        @runtime_validation
        def func(param: typing.List[typing.List[str]]) -> typing.List[typing.List[str]]:
            return param

        func([["s", "aaa"], ["a", "b"]])
        func([[]])

        with self.assertRaises(RuntimeTypeError):
            func([[12]])


class UnionTypesTests(unittest.TestCase):
    """
    Test case for Union Types
    """

    def setUp(self):
        @runtime_validation
        def test_func(x: typing.Union[float, typing.List[str]]) -> int:
            return 5

        @runtime_validation
        def nest_func(
            x: typing.Union[float, typing.List[typing.Union[str, int]]]
        ) -> int:
            return 5

        self.test_func = test_func
        self.nest_func = nest_func

    def test_basic_union(self):
        @runtime_validation
        def sample(data: typing.Union[int, str]) -> typing.Union[int, str]:
            return data

        @runtime_validation
        def sample_bad(data: typing.Any) -> typing.Union[int, str]:
            return data

        self.assertEqual(sample(1), 1)
        self.assertEqual(sample(""), "")
        with self.assertRaises(RuntimeTypeError):
            sample(b"")

        with self.assertRaises(RuntimeTypeError):
            sample_bad(1.0)

    def test_good_nested_union(self):
        self.test_func(5.0)
        self.test_func(["1", "2", "a"])

    def test_bad_nested_union(self):
        with self.assertRaises(RuntimeTypeError):
            self.test_func("a")

        with self.assertRaises(RuntimeTypeError):
            self.test_func([1, 2, 3, 4])

        with self.assertRaises(RuntimeTypeError):
            self.test_func(["a", 4, 5])

    def test_nested_func_good(self):
        self.nest_func(5.0)
        self.nest_func(["a", "b", "c"])
        self.nest_func([1, 2, 3])
        self.nest_func([1, "a", 2, "b"])

    def test_nested_func_bad(self):
        with self.assertRaises(RuntimeTypeError):
            self.nest_func("a")
        with self.assertRaises(RuntimeTypeError):
            self.nest_func({"a": 5, "b": 6})
        with self.assertRaises(RuntimeTypeError):
            self.nest_func({1, 2, 3, 4})

    def test_union_of_nested_lists(self):
        ManyMessageType = typing.List[str]
        MessagesType = typing.Union[str, typing.List[ManyMessageType]]

        @runtime_validation
        def test(msgs: MessagesType):
            return msgs

        test([["a", "b"], ["x", "y"]])


class ContainerTypesTests(unittest.TestCase):
    """
    Tests for the container types - types of unbounded size
    """

    pass


class SetTypesTests(unittest.TestCase):
    def test_basic_set(self):
        @runtime_validation
        def sample_func(data: typing.Set[str]) -> typing.Set[int]:
            return set(int(item) for item in data)

        sample_func({"1", "2"})

        with self.assertRaises(RuntimeTypeError):
            sample_func(["1", "2"])

        with self.assertRaises(RuntimeTypeError):
            sample_func({"1", 1})


class IterableTypesTests(unittest.TestCase):
    """
    Tests for iterator and generator support
    """

    pass


class CallableTypesTests(unittest.TestCase):
    """
    Tests for the callable types such as functions
    """

    def setUp(self):
        @runtime_validation
        def test(func: typing.Callable[[int, int], int], x: int) -> int:
            return func(x, x)

        @runtime_validation
        def test_list(
            func: typing.Callable[[typing.Union[typing.List[typing.Any], int]], int]
        ) -> int:
            return func(5)

        @runtime_validation
        def union(
            func: typing.Callable[[typing.Union[float, int], typing.Optional[str]], int]
        ) -> int:
            return func(5)

        @runtime_validation
        def any_func_args(func: typing.Callable):
            return func

        @runtime_validation
        def any_func_return(func) -> typing.Callable:
            return func

        self.test = test
        self.test_list = test_list
        self.union = union
        self.any_func_args = any_func_args
        self.any_func_return = any_func_return

    # TODO: rename this test
    def test_unrestrained_callable_arguments(self):
        """
        Verifies that a function which expects any Callable as an argument,
        would fail if an object of different type is passed
        """
        callable = lambda x: x
        self.any_func_args(callable)

        with self.assertRaises(RuntimeTypeError):
            self.any_func_args("bad_input")

    # TODO: rename this test
    def test_unrestrained_callable_returns(self):
        """
        Verifies that a function which expects any Callable as an output,
        would fail if an object of different type is returned
        """
        callable = lambda x: x
        self.any_func_return(callable), callable

        with self.assertRaises(RuntimeTypeError):
            self.any_func_return("bad_input")

    def test_good_callable_object(self):
        """ Test that a callable object works """

        class Good:
            def __call__(self, x: int, y: int) -> int:
                return int(x * y)

        self.test(Good(), 5)

    def test_good_func_arg(self):
        """ Test that good arguments pass """

        def good(x: int, y: int) -> int:
            return int(x * y)

        self.test(good, 5)

    def test_bad_func_return(self):
        """
        Test that a function being passed in with mismatching return raises
        """

        def bad_return(x: int, y: int) -> float:
            return float(x * y)

        with self.assertRaises(RuntimeTypeError):
            self.test(bad_return, 5)

    def test_bad_func_call(self):
        """
        Test that a function being passed in with mismatching callsig raises
        """

        def bad_callsig(x: str, y: str) -> int:
            return int(x + y)

        with self.assertRaises(RuntimeTypeError):
            self.test(bad_callsig, 5)

    def test_bad_func(self):
        """
        Test that passing in something that's not a function raises
        """
        with self.assertRaises(RuntimeTypeError):
            self.test(5, 5)

    def test_nested_func(self):
        """
        Test that a function with deeply nested types works
        """

        def nest_func(x: typing.Union[int, typing.List[typing.Any]]) -> int:
            return 5

        self.test_list(nest_func)

    def test_nested_bad_func(self):
        """
        Test that a function with bad deeply nested types fails
        """

        def nest_func(x: typing.List[typing.List[int]]) -> int:
            return 5

        with self.assertRaises(RuntimeTypeError):
            self.test_list(nest_func)

    def test_good_union_func(self):
        def good_union(
            x: typing.Union[float, int], a: typing.Optional[str] = None
        ) -> int:
            print(a)
            return int(x)

        self.union(good_union)

    def test_bad_union_func(self):
        def bad_union(x: float, a=None) -> int:
            return int(x)

        with self.assertRaises(RuntimeTypeError):
            self.union(bad_union)

    def test_good_optional_parameter_func(self):
        def good_param(
            x: typing.Union[float, int], y: typing.Optional[str] = "a"
        ) -> int:
            return x

        self.union(good_param)

    def test_bad_optional_parameter_func(self):
        def bad_param(x: typing.Union[float, int], y: str = "b") -> int:
            return x

        with self.assertRaises(RuntimeTypeError):
            self.union(bad_param)


class DictTypesTests(unittest.TestCase):
    """
    Tests for the dictionary types
    """

    def test_simple_dict(self):
        """
        Verifies that unrestricted Dictionary type is correctly checked
        """
        d = {"a": 12, "b": "b"}

        @runtime_validation
        def foo(a: typing.Dict, b: typing.Any = None) -> typing.Dict:
            return b

        foo(d, d)

        with self.assertRaises(RuntimeTypeError):
            foo(3)

        with self.assertRaises(RuntimeTypeError):
            foo(d, 2)

    def test_restricted_dict(self):
        """
        Verifies that restricted dictionaries are type checked correctly
        """
        TypeAlias = typing.Dict[str, typing.Union[int, str, None]]

        @runtime_validation
        def foo(a: TypeAlias, b: typing.Any = None) -> TypeAlias:
            return b

        good_dict = {"hello": "world", "name": None, "id": 1234}

        bad_dict = {"hello": 123.5}

        foo(good_dict, good_dict)

        with self.assertRaises(RuntimeTypeError):
            foo(bad_dict)

        with self.assertRaises(RuntimeTypeError):
            foo(good_dict, bad_dict)

        foo({}, {})

    def test_nested_dicts(self):
        """
        Verifies that the type containing nested dictionaries can be successfully verified
        """
        TypeAlias = typing.Dict[str, typing.Dict[str, typing.Optional[int]]]

        @runtime_validation
        def foo(a: TypeAlias, b: typing.Any = None) -> TypeAlias:
            return b

        good_dict = {"hello": {"world": 12, "me": None}}

        bad_dict = {12: None}

        bad_dict_2 = {
            "hello": {"world": 12, "everyone": None, "me": {1, 3}, 2: {"a": "a"}}
        }

        foo(good_dict, good_dict)

        with self.assertRaises(RuntimeTypeError):
            foo(bad_dict)

        with self.assertRaises(RuntimeTypeError):
            foo(good_dict, bad_dict)

        with self.assertRaises(RuntimeTypeError):
            foo(bad_dict_2)

        with self.assertRaises(RuntimeTypeError):
            foo(good_dict, bad_dict_2)


class GenericTypesTests(unittest.TestCase):
    """
    Tests for the generic types
    """

    def test_custom_generic_initialisation(self):
        """
        Verifies that user defined generics can be initialised
        """
        T = typing.TypeVar("T")

        class Sample(typing.Generic[T]):
            pass

        SD = runtime_validation(Sample)

        ST = Sample[int]
        SDT = SD[int]

        s = Sample()
        sd = SD()
        st = ST()
        sdt = SDT()

        self.assertFalse(hasattr(s, "__enforcer__"))
        self.assertFalse(hasattr(st, "__enforcer__"))
        self.assertTrue(hasattr(sd, "__enforcer__"))
        self.assertTrue(hasattr(sdt, "__enforcer__"))

        self.assertEqual(sd.__enforcer__.signature, Sample)
        self.assertEqual(sdt.__enforcer__.signature, Sample)

        self.assertEqual(sd.__enforcer__.generic, SD.__enforcer__.generic)
        self.assertEqual(sdt.__enforcer__.generic, SDT.__enforcer__.generic)

        self.assertEqual(sd.__enforcer__.bound, SD.__enforcer__.bound)
        self.assertEqual(sdt.__enforcer__.bound, SDT.__enforcer__.bound)

        for hint_name, hint_value in sdt.__enforcer__.hints.items():
            self.assertEqual(hint_value, SDT.__enforcer__.hints[hint_name])

        self.assertEqual(len(sdt.__enforcer__.hints), len(SDT.__enforcer__.hints))

    def test_custom_generic_validation(self):
        """
        Verifies that user defined generic can be used as a type hint
        """
        T = typing.TypeVar("T")

        @runtime_validation
        class Sample(typing.Generic[T]):
            def get(self, data: T) -> T:
                return data

        @runtime_validation
        def return_int(data: Sample[int], arg: int) -> int:
            return data.get(arg)

        @runtime_validation
        def return_any(data: Sample) -> typing.Any:
            return data

        good = Sample[int]()
        bad = Sample[str]()
        other = Sample()
        strange = Sample[T]()

        self.assertEqual(return_int(good, 1), 1)
        self.assertIs(return_any(other), other)

        # TODO: Find out exactly what should be be happening in this case
        # self.assertIs(return_any(strange), strange)

        with self.assertRaises(RuntimeTypeError):
            return_int(bad, 1)

        with self.assertRaises(RuntimeTypeError):
            return_int(other, 1)

        with self.assertRaises(RuntimeTypeError):
            return_int(strange, 1)

        with self.assertRaises(RuntimeTypeError):
            return_any(good)

        with self.assertRaises(RuntimeTypeError):
            return_any(bad)


class NestedTypesTests(unittest.TestCase):
    """
    Tests for special and corner cases when types are deeply nested
    """

    pass


class ExceptionMessageTests(unittest.TestCase):
    """
    Tests for validating a correct exception messages are returned
    """

    def setUp(self):
        self.prefix_message = "\n  The following runtime type errors were encountered:"
        self.input_error_message = (
            "Argument '{0}' was not of type {1}. Actual type was {2}."
        )
        self.return_error_message = (
            "Return value was not of type {0}. Actual type was {1}."
        )

    def generateStrictFunction(
        self,
        inputs: typing.List[typing.Tuple[str, str]],
        returns: typing.Optional[str],
        result,
    ) -> typing.Callable:
        template = """
@runtime_validation
def func({inputs}) {returns}:
    return data
"""
        inputs = tuple(": ".join(input_pair) for input_pair in inputs)
        inputs = ", ".join(inputs)
        returns = "" if returns is None else "-> " + returns
        formatted_template = template.format(inputs=inputs, returns=returns)

        scope_data = {
            "data": result,
            "typing": typing,
            "runtime_validation": runtime_validation,
        }

        exec(formatted_template, scope_data)

        return scope_data["func"]

    def generateExceptionPattern(self, messages, is_return=False):
        if is_return:
            expected_message = self.return_error_message.format(*messages)
            expected_message = ".*" + re.escape(expected_message) + ".*"
        else:
            expected_message = self.input_error_message.format(*messages)
            expected_message = ".*" + re.escape(expected_message) + ".*"

        pattern = re.compile(expected_message)

        return pattern

    def test_simple_exceptions(self):
        sample_function = self.generateStrictFunction([("a", "int")], "str", 12)

        pattern = self.generateExceptionPattern(("a", str(int), "str"))

        with self.assertRaisesRegex(RuntimeTypeError, pattern):
            sample_function("12")

        pattern = self.generateExceptionPattern((str(str), "int"), True)

        with self.assertRaisesRegex(RuntimeTypeError, pattern):
            sample_function(12)

    def test_list_exceptions(self):
        sample_function = self.generateStrictFunction(
            [("a", "typing.List[int]")], "str", 12
        )

        pattern = self.generateExceptionPattern(("a", str(typing.List[int]), "int"))

        with self.assertRaisesRegex(RuntimeTypeError, pattern):
            sample_function(12)

        pattern = self.generateExceptionPattern(
            ("a", str(typing.List[int]), "typing.List[str]")
        )

        with self.assertRaisesRegex(RuntimeTypeError, pattern):
            sample_function(["12"])

        pattern = self.generateExceptionPattern((str(str), "int"), True)

        with self.assertRaisesRegex(RuntimeTypeError, pattern):
            sample_function([12])

    def test_set_exceptions(self):
        sample_function = self.generateStrictFunction(
            [("a", "typing.Set[int]")], "str", 12
        )

        pattern = self.generateExceptionPattern(("a", str(typing.Set[int]), "int"))

        with self.assertRaisesRegex(RuntimeTypeError, pattern):
            sample_function(12)

        pattern = self.generateExceptionPattern(
            ("a", str(typing.Set[int]), "typing.Set[str]")
        )

        with self.assertRaisesRegex(RuntimeTypeError, pattern):
            sample_function({"12"})

        pattern = self.generateExceptionPattern((str(str), "int"), True)

        with self.assertRaisesRegex(RuntimeTypeError, pattern):
            sample_function({12})

    def test_dict_exceptions(self):
        scope = {"data": None, "type_alias": typing.Dict[str, int]}

        @runtime_validation
        def sample_function(a: scope["type_alias"]) -> scope["type_alias"]:
            return scope["data"]

        pattern = self.generateExceptionPattern(("a", scope["type_alias"], "int"))

        with self.assertRaisesRegex(RuntimeTypeError, pattern):
            sample_function(12)

        pattern = self.generateExceptionPattern(
            ("a", scope["type_alias"], "typing.Set")
        )

        with self.assertRaisesRegex(RuntimeTypeError, pattern):
            sample_function({"12"})

        pattern = self.generateExceptionPattern(
            ("a", scope["type_alias"], "typing.Dict[str, float]")
        )

        with self.assertRaisesRegex(RuntimeTypeError, pattern):
            sample_function({"s": 12.0})

        scope["data"] = 12
        pattern = self.generateExceptionPattern(
            (scope["type_alias"], "int"), is_return=True
        )

        with self.assertRaisesRegex(RuntimeTypeError, pattern):
            sample_function({"s": 12})

        scope["data"] = {"12"}
        pattern = self.generateExceptionPattern(
            (scope["type_alias"], "typing.Set"), is_return=True
        )

        with self.assertRaisesRegex(RuntimeTypeError, pattern):
            sample_function({"s": 12})

        scope["data"] = {"s": 12.0}
        pattern = self.generateExceptionPattern(
            (scope["type_alias"], "typing.Dict[str, float]"), is_return=True
        )

        with self.assertRaisesRegex(RuntimeTypeError, pattern):
            sample_function({"s": 12})

        scope = {
            "data": None,
            "type_alias": typing.Dict[str, typing.Dict[str, typing.Optional[int]]],
        }

        @runtime_validation
        def sample_function(a: scope["type_alias"]) -> scope["type_alias"]:
            return scope["data"]

        pattern = self.generateExceptionPattern(
            (
                "a",
                scope["type_alias"],
                "typing.Dict[str, typing.Dict[str, typing.Union[NoneType, float, int]]]",
            )
        )

        with self.assertRaisesRegex(RuntimeTypeError, pattern):
            sample_function({"hello": {"world": 12, "w": None, "r": 12.0}})

    def test_union_exceptions(self):
        parameter_type_str = str(typing.Union[int, str])

        sample_function = self.generateStrictFunction(
            [("a", "typing.Union[int, str]")],
            "typing.List[typing.Union[int, str]]",
            [None],
        )

        pattern = self.generateExceptionPattern(("a", parameter_type_str, "NoneType"))

        with self.assertRaisesRegex(RuntimeTypeError, pattern):
            sample_function(None)

        pattern = self.generateExceptionPattern(
            ("a", parameter_type_str, "typing.List")
        )

        with self.assertRaisesRegex(RuntimeTypeError, pattern):
            sample_function([None])

        pattern = self.generateExceptionPattern(
            (str(typing.List[typing.Union[int, str]]), "typing.List[NoneType]"), True
        )

        with self.assertRaisesRegex(RuntimeTypeError, pattern):
            sample_function(12)

    def test_tuple_exception(self):
        parameter_type_str = str(typing.Tuple[int, typing.Union[int, str]])
        sample_function = self.generateStrictFunction(
            [("a", "typing.Tuple[int, typing.Union[int, str]]")], "int", 12
        )

        pattern = self.generateExceptionPattern(
            ("a", parameter_type_str, "typing.Tuple[str, int]")
        )

        with self.assertRaisesRegex(RuntimeTypeError, pattern):
            sample_function(("1", 2))

        parameter_type_str = str(typing.Tuple[int, int, int])
        sample_function = self.generateStrictFunction(
            [("a", "typing.Tuple[int, int, int]")], "None", None
        )

        pattern = self.generateExceptionPattern(
            ("a", parameter_type_str, "typing.Tuple[int, int]")
        )

        with self.assertRaisesRegex(RuntimeTypeError, pattern):
            sample_function((1, 2))

        parameter_type_str = str(typing.Tuple[int, int])
        sample_function = self.generateStrictFunction(
            [("a", "typing.Tuple[int, int]")], "None", None
        )

        pattern = self.generateExceptionPattern(
            ("a", parameter_type_str, "typing.Tuple[int, int, str]")
        )

        with self.assertRaisesRegex(RuntimeTypeError, pattern):
            sample_function((1, 2, "abc"))

    def test_named_tuple_exception(self):
        from collections import namedtuple

        MyNamedTuple = typing.NamedTuple("MyNamedTuple", [("a", int), ("b", str)])
        parameter_type_str = str(MyNamedTuple)

        @runtime_validation
        def foo(data: MyNamedTuple):
            return str(data.b) + str(data.a)

        argument_a = MyNamedTuple(10, 10)
        argument_b = (10, "ten")
        argument_c = 12
        argument_d = namedtuple("MyNamedTuple", ["a", "b"])(10, "ten")
        argument_e = None

        pattern_a = self.generateExceptionPattern(
            (
                "data",
                parameter_type_str,
                parameter_type_str
                + " with incorrect arguments: a -> <class 'int'>, b -> <class 'int'>",
            )
        )
        pattern_b = self.generateExceptionPattern(
            ("data", parameter_type_str, "typing.Tuple")
        )
        pattern_c = self.generateExceptionPattern(("data", parameter_type_str, "int"))
        pattern_d = self.generateExceptionPattern(
            ("data", parameter_type_str, "untyped MyNamedTuple")
        )
        pattern_e = self.generateExceptionPattern(
            ("data", parameter_type_str, "NoneType")
        )

        with self.assertRaisesRegex(RuntimeTypeError, pattern_a):
            foo(argument_a)

        with self.assertRaisesRegex(RuntimeTypeError, pattern_b):
            foo(argument_b)

        with self.assertRaisesRegex(RuntimeTypeError, pattern_c):
            foo(argument_c)

        with self.assertRaisesRegex(RuntimeTypeError, pattern_d):
            foo(argument_d)

        with self.assertRaisesRegex(RuntimeTypeError, pattern_e):
            foo(argument_e)


class ConcurrentRunTests(unittest.TestCase):
    def test_threading(self):
        import concurrent.futures

        ASSERT_ENABLED = True

        def test_runner(widget_number):
            widgets = [x for x in range(widget_number)]
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                for score in executor.map(test_one_widget, widgets):
                    if ASSERT_ENABLED:
                        assert isinstance(score, int)

        @runtime_validation
        def test_one_widget(widget_id: int) -> int:
            # print('ID:', widget_id)
            score = widget_inspector(widget_id, a="foo", b=4, c="bar")
            return score

        @runtime_validation
        def widget_inspector(widget_id: int, a: str, b: int, c: str) -> int:
            if ASSERT_ENABLED:
                assert isinstance(widget_id, int)
                assert isinstance(a, str)
                assert isinstance(b, int)
                assert isinstance(c, str)
            return b

        for i in range(100):
            test_runner(100)
            print(".", end="", flush=True)
        print("test success")

    @unittest.skip("I do not even know how to debug this issue!")
    def test_processing(self):
        import concurrent.futures

        ASSERT_ENABLED = True

        def test_runner(widget_number):
            widgets = [x for x in range(widget_number)]
            with concurrent.futures.ProcessPoolExecutor(max_workers=10) as executor:
                for score in executor.map(test_one_widget, widgets):
                    if ASSERT_ENABLED:
                        assert isinstance(score, int)

        @runtime_validation
        def test_one_widget(widget_id: int) -> int:
            # print('ID:', widget_id)
            score = widget_inspector(widget_id, a="foo", b=4, c="bar")
            return score

        @runtime_validation
        def widget_inspector(widget_id: int, a: str, b: int, c: str) -> int:
            if ASSERT_ENABLED:
                assert isinstance(widget_id, int)
                assert isinstance(a, str)
                assert isinstance(b, int)
                assert isinstance(c, str)
            return b

        for i in range(100):
            test_runner(100)
            print(".", end="", flush=True)
        print("test success")


if __name__ == "__main__":
    unittest.main()
