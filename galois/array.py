import random

import numpy as np

from .meta_gf import GFMeta
from .linalg import dot, inner, outer, matrix_rank, solve, inv, det, row_reduce, lu_decompose, lup_decompose
from .overrides import set_module
from .poly_conversion import integer_to_poly, poly_to_str, str_to_integer

__all__ = ["GFArray"]


UNSUPPORTED_ONE_ARG_FUNCTIONS = [
    np.packbits, np.unpackbits,
    np.unwrap,
    np.around, np.round_, np.fix,
    np.gradient, np.trapz,
    np.i0, np.sinc,
    np.angle, np.real, np.imag, np.conj, np.conjugate,
]

UNSUPPORTED_TWO_ARG_FUNCTIONS = [
    np.lib.scimath.logn,
    np.cross,
]

UNSUPPORTED_FUNCTIONS = UNSUPPORTED_ONE_ARG_FUNCTIONS + UNSUPPORTED_TWO_ARG_FUNCTIONS

OVERRIDDEN_FUNCTIONS = {
    np.dot: dot,
    np.inner: inner,
    np.outer: outer,
    # np.tensordot: "tensordot",
    np.linalg.matrix_rank: matrix_rank,
    np.linalg.inv: inv,
    np.linalg.det: det,
    np.linalg.solve: solve
}

FUNCTIONS_REQUIRING_VIEW = [
    np.copy, np.concatenate,
    np.broadcast_to,
    np.trace,
]

UNSUPPORTED_ONE_ARG_UFUNCS = [
    np.invert, np.sqrt,
    np.log2, np.log10,
    np.exp, np.expm1, np.exp2,
    np.sin, np.cos, np.tan,
    np.sinh, np.cosh, np.tanh,
    np.arcsin, np.arccos, np.arctan,
    np.arcsinh, np.arccosh, np.arctanh,
    np.degrees, np.radians,
    np.deg2rad, np.rad2deg,
    np.floor, np.ceil, np.trunc, np.rint,
]

UNSUPPORTED_TWO_ARG_UFUNCS = [
    np.hypot, np.arctan2,
    np.logaddexp, np.logaddexp2,
    np.remainder,
    np.fmod, np.modf,
    np.fmin, np.fmax,
]

UNSUPPORTED_UFUNCS = UNSUPPORTED_ONE_ARG_UFUNCS + UNSUPPORTED_TWO_ARG_UFUNCS

OVERRIDDEN_UFUNCS = {
    np.add: "_ufunc_add",
    np.subtract: "_ufunc_subtract",
    np.multiply: "_ufunc_multiply",
    np.floor_divide: "_ufunc_divide",
    np.true_divide: "_ufunc_divide",
    np.negative: "_ufunc_negative",
    np.reciprocal: "_ufunc_reciprocal",
    np.power: "_ufunc_power",
    np.square: "_ufunc_square",
    np.log: "_ufunc_log",
    np.matmul: "_ufunc_matmul",
}

UFUNCS_REQUIRING_VIEW = [
    np.bitwise_and, np.bitwise_or, np.bitwise_xor,
    np.left_shift, np.right_shift,
]


@set_module("galois")
class GFArray(np.ndarray, metaclass=GFMeta):
    """
    Create an array over :math:`\\mathrm{GF}(p^m)`.

    The :obj:`galois.GFArray` class is a parent class for all Galois field array classes. Any Galois field :math:`\\mathrm{GF}(p^m)`
    with prime characteristic :math:`p` and positive integer :math:`m`, can be constructed by calling the class factory
    `galois.GF(p**m)`.

    Warning
    -------
        This is an abstract base class for all Galois field array classes. :obj:`galois.GFArray` cannot be instantiated
        directly. Instead, Galois field array classes are created using :obj:`galois.GF`.

        For example, one can create the :math:`\\mathrm{GF}(7)` field array class as follows:

        .. ipython:: python

            GF7 = galois.GF(7)
            print(GF7)

        This subclass can then be used to instantiate arrays over :math:`\\mathrm{GF}(7)`.

        .. ipython:: python

            GF7([3,5,0,2,1])
            GF7.Random((2,5))

    :obj:`galois.GFArray` is a subclass of :obj:`numpy.ndarray`. The :obj:`galois.GFArray` constructor has the same syntax as
    :obj:`numpy.array`. The returned :obj:`galois.GFArray` object is an array that can be acted upon like any other
    numpy array.

    Parameters
    ----------
    array : array_like
        The input array to be converted to a Galois field array. The input array is copied, so the original array
        is unmodified by changes to the Galois field array. Valid input array types are :obj:`numpy.ndarray`,
        :obj:`list` or :obj:`tuple` of ints or strs, :obj:`int`, or :obj:`str`.
    dtype : numpy.dtype, optional
        The :obj:`numpy.dtype` of the array elements. The default is `None` which represents the smallest valid
        dtype for this class, i.e. the first element in :obj:`galois.GFMeta.dtypes`.
    copy : bool, optional
        The `copy` keyword argument from :obj:`numpy.array`. The default is `True` which makes a copy of the input
        object is it's an array.
    order : str, optional
        The `order` keyword argument from :obj:`numpy.array`. Valid values are `"K"` (default), `"A"`, `"C"`, or `"F"`.
    ndmin : int, optional
        The `ndmin` keyword argument from :obj:`numpy.array`. The minimum number of dimensions of the output.
        The default is 0.

    Returns
    -------
    galois.GFArray
        The copied input array as a :math:`\\mathrm{GF}(p^m)` field array.

    Examples
    --------
    Construct various kinds of Galois fields using :obj:`galois.GF`.

    .. ipython:: python

        # Construct a GF(2^m) class
        GF256 = galois.GF(2**8); print(GF256)

        # Construct a GF(p) class
        GF571 = galois.GF(571); print(GF571)

        # Construct a very large GF(2^m) class
        GF2m = galois.GF(2**100); print(GF2m)

        # Construct a very large GF(p) class
        GFp = galois.GF(36893488147419103183); print(GFp)

    Depending on the field's order (size), only certain `dtype` values will be supported.

    .. ipython:: python

        GF256.dtypes
        GF571.dtypes

    Very large fields, which can't be represented using `np.int64`, can only be represented as `dtype=np.object_`.

    .. ipython:: python

        GF2m.dtypes
        GFp.dtypes

    Newly-created arrays will use the smallest, valid dtype.

    .. ipython:: python

        a = GF256.Random(10); a
        a.dtype

    This can be explicitly set by specifying the `dtype` keyword argument.

    .. ipython:: python

        a = GF256.Random(10, dtype=np.uint32); a
        a.dtype

    Arrays can also be created explicitly by converting an "array-like" object.

    .. ipython:: python

        # Construct a Galois field array from a list
        l = [142, 27, 92, 253, 103]; l
        GF256(l)

        # Construct a Galois field array from an existing numpy array
        x_np = np.array(l, dtype=np.int64); x_np
        GF256(l)

    Arrays can also be created by "view casting" from an existing numpy array. This avoids
    a copy operation, which is especially useful for large data already brought into memory.

    .. ipython:: python

        a = x_np.view(GF256); a

        # Changing `x_np` will change `a`
        x_np[0] = 0; x_np
        a
    """

    def __new__(cls, array, dtype=None, copy=True, order="K", ndmin=0):
        if cls is GFArray:
            raise NotImplementedError("GFArray is an abstract base class that cannot be directly instantiated. Instead, create a GFArray subclass using `galois.GF`.")
        return cls._array(array, dtype=dtype, copy=copy, order=order, ndmin=ndmin)

    @classmethod
    def _get_dtype(cls, dtype):
        if dtype is None:
            return cls.dtypes[0]

        # Convert "dtype" to a numpy dtype. This does platform specific conversion, if necessary.
        # For example, np.dtype(int) == np.int64 (on some systems).
        dtype = np.dtype(dtype)
        if dtype not in cls.dtypes:
            raise TypeError(f"{cls.name} arrays only support dtypes {[np.dtype(d).name for d in cls.dtypes]}, not '{dtype.name}'.")

        return dtype

    @classmethod
    def _array(cls, array_like, dtype=None, copy=True, order="K", ndmin=0):
        dtype = cls._get_dtype(dtype)
        array_like = cls._check_array_like_object(array_like)
        array = np.array(array_like, dtype=dtype, copy=copy, order=order, ndmin=ndmin)
        return array.view(cls)

    @classmethod
    def _check_array_like_object(cls, array_like):
        if isinstance(array_like, str):
            # Convert the string to an integer
            array_like = str_to_integer(array_like, cls.prime_subfield)

        if isinstance(array_like, (int, np.integer)):
            # Just check that the single int is in range
            cls._check_array_values(array_like)

        elif isinstance(array_like, (list, tuple)):
            # Recursively check the items in the iterable to ensure they're of the correct type
            # and that their values are in range
            array_like = cls._check_iterable_types_and_values(array_like)

        elif isinstance(array_like, np.ndarray):
            if array_like.dtype == np.object_:
                array_like = cls._check_array_types_dtype_object(array_like)
            elif not np.issubdtype(array_like.dtype, np.integer):
                raise TypeError(f"{cls.name} arrays must have integer dtypes, not {array_like.dtype}.")
            cls._check_array_values(array_like)

        else:
            raise TypeError(f"{cls.name} arrays can be created with scalars of type int, not {type(array_like)}.")

        return array_like

    @classmethod
    def _check_iterable_types_and_values(cls, iterable):
        new_iterable = []
        for item in iterable:
            if isinstance(item, (list, tuple)):
                item = cls._check_iterable_types_and_values(item)
                new_iterable.append(item)
                continue

            if isinstance(item, str):
                item = str_to_integer(item, cls.prime_subfield)
            elif not isinstance(item, (int, np.integer, cls)):
                raise TypeError(f"When {cls.name} arrays are created/assigned with an iterable, each element must be an integer. Found type {type(item)}.")

            if not 0 <= item < cls.order:
                raise ValueError(f"{cls.name} arrays must have elements in 0 <= x < {cls.order}, not {item}.")

            # Ensure the type is int so dtype=object classes don't get all mixed up
            new_iterable.append(int(item))

        return new_iterable

    @classmethod
    def _check_array_types_dtype_object(cls, array):
        if array.size == 0:
            return array
        if array.ndim == 0:
            if not isinstance(array[()], (int, np.integer, cls)):
                raise TypeError(f"When {cls.name} arrays are created/assigned with a numpy array with dtype=object, each element must be an integer. Found type {type(array[()])}.")
            return int(array)

        iterator = np.nditer(array, flags=["multi_index", "refs_ok"])
        for _ in iterator:
            a = array[iterator.multi_index]
            if not isinstance(a, (int, np.integer, cls)):
                raise TypeError(f"When {cls.name} arrays are created/assigned with a numpy array with dtype=object, each element must be an integer. Found type {type(a)}.")

            # Ensure the type is int so dtype=object classes don't get all mixed up
            array[iterator.multi_index] = int(a)

        return array

    @classmethod
    def _check_array_values(cls, array):
        if not isinstance(array, np.ndarray):
            # Convert single integer to array so next step doesn't fail
            array = np.array(array)

        # Check the value of the "field elements" and make sure they are valid
        if np.any(array < 0) or np.any(array >= cls.order):
            idxs = np.logical_or(array < 0, array >= cls.order)
            raise ValueError(f"{cls.name} arrays must have elements in 0 <= x < {cls.order}, not {array[idxs]}.")

    ###############################################################################
    # Alternate constructors
    ###############################################################################

    @classmethod
    def Zeros(cls, shape, dtype=None):
        """
        Creates a Galois field array with all zeros.

        Parameters
        ----------
        shape : tuple
            A numpy-compliant `shape` tuple, see :obj:`numpy.ndarray.shape`. An empty tuple `()` represents a scalar.
            A single integer or 1-tuple, e.g. `N` or `(N,)`, represents the size of a 1-dim array. An n-tuple, e.g.
            `(M,N)`, represents an n-dim array with each element indicating the size in each dimension.
        dtype : numpy.dtype, optional
            The :obj:`numpy.dtype` of the array elements. The default is `None` which represents the smallest valid
            dtype for this class, i.e. the first element in :obj:`galois.GFMeta.dtypes`.

        Returns
        -------
        galois.GFArray
            A Galois field array of zeros.

        Examples
        --------
        .. ipython:: python

            GF = galois.GF(31)
            GF.Zeros((2,5))
        """
        dtype = cls._get_dtype(dtype)
        array = np.zeros(shape, dtype=dtype)
        return array.view(cls)

    @classmethod
    def Ones(cls, shape, dtype=None):
        """
        Creates a Galois field array with all ones.

        Parameters
        ----------
        shape : tuple
            A numpy-compliant `shape` tuple, see :obj:`numpy.ndarray.shape`. An empty tuple `()` represents a scalar.
            A single integer or 1-tuple, e.g. `N` or `(N,)`, represents the size of a 1-dim array. An n-tuple, e.g.
            `(M,N)`, represents an n-dim array with each element indicating the size in each dimension.
        dtype : numpy.dtype, optional
            The :obj:`numpy.dtype` of the array elements. The default is `None` which represents the smallest valid
            dtype for this class, i.e. the first element in :obj:`galois.GFMeta.dtypes`.

        Returns
        -------
        galois.GFArray
            A Galois field array of ones.

        Examples
        --------
        .. ipython:: python

            GF = galois.GF(31)
            GF.Ones((2,5))
        """
        dtype = cls._get_dtype(dtype)
        array = np.ones(shape, dtype=dtype)
        return array.view(cls)

    @classmethod
    def Identity(cls, size, dtype=None):
        """
        Creates an :math:`n \\times n` identity matrix over :math:`\\mathrm{GF}(q)`.

        Parameters
        ----------
        size : int
            The size :math:`n` along one axis of the matrix. The resulting array has shape `(size,size)`.
        dtype : numpy.dtype, optional
            The :obj:`numpy.dtype` of the array elements. The default is `None` which represents the smallest valid
            dtype for this class, i.e. the first element in :obj:`galois.GFMeta.dtypes`.

        Returns
        -------
        galois.GFArray
            A Galois field identity matrix of shape `(size, size)`.

        Examples
        --------
        .. ipython:: python

            GF = galois.GF(31)
            GF.Identity(4)
        """
        dtype = cls._get_dtype(dtype)
        array = np.identity(size, dtype=dtype)
        return array.view(cls)

    @classmethod
    def Vandermonde(cls, a, m, n, dtype=None):
        """
        Creates a :math:`m \\times n` Vandermonde matrix of :math:`a \\in \\mathrm{GF}(q)`.

        Parameters
        ----------
        a : int, galois.GFArray
            An element of :math:`\\mathrm{GF}(q)`.
        m : int
            The number of rows in the Vandermonde matrix.
        n : int
            The number of columns in the Vandermonde matrix.
        dtype : numpy.dtype, optional
            The :obj:`numpy.dtype` of the array elements. The default is `None` which represents the smallest valid
            dtype for this class, i.e. the first element in :obj:`galois.GFMeta.dtypes`.

        Returns
        -------
        galois.GFArray
            The :math:`m \\times n` Vandermonde matrix.

        Examples
        --------
        .. ipython:: python

            GF = galois.GF(2**3)
            a = GF.primitive_element
            V = GF.Vandermonde(a, 7, 7)
            with GF.display("power"):
                print(V)
        """
        if not isinstance(a, (int, np.integer,cls)):
            raise TypeError(f"Argument `a` must be an integer or element of {cls.name}, not {type(a)}.")
        if not isinstance(m, (int, np.integer)):
            raise TypeError(f"Argument `m` must be an integer, not {type(m)}.")
        if not isinstance(n, (int, np.integer)):
            raise TypeError(f"Argument `n` must be an integer, not {type(n)}.")
        if not m > 0:
            raise ValueError(f"Argument `m` must be non-negative, not {m}.")
        if not n > 0:
            raise ValueError(f"Argument `n` must be non-negative, not {n}.")

        dtype = cls._get_dtype(dtype)
        a = cls(a, dtype=dtype)
        if not a.ndim == 0:
            raise ValueError(f"Argument `a` must be a scalar, not {a.ndim}-D.")

        v = a ** np.arange(0, m)
        V = np.power.outer(v, np.arange(0, n))

        return V

    @classmethod
    def Range(cls, start, stop, step=1, dtype=None):
        """
        Creates a Galois field array with a range of field elements.

        Parameters
        ----------
        start : int
            The starting value (inclusive).
        stop : int
            The stopping value (exclusive).
        step : int, optional
            The space between values. The default is 1.
        dtype : numpy.dtype, optional
            The :obj:`numpy.dtype` of the array elements. The default is `None` which represents the smallest valid
            dtype for this class, i.e. the first element in :obj:`galois.GFMeta.dtypes`.

        Returns
        -------
        galois.GFArray
            A Galois field array of a range of field elements.

        Examples
        --------
        .. ipython:: python

            GF = galois.GF(31)
            GF.Range(10,20)
        """
        dtype = cls._get_dtype(dtype)
        if not stop <= cls.order:
            raise ValueError(f"The stopping value must be less than the field order of {cls.order}, not {stop}.")

        if dtype != np.object_:
            array = np.arange(start, stop, step=step, dtype=dtype)
        else:
            array = np.array(range(start, stop, step), dtype=dtype)

        return array.view(cls)

    @classmethod
    def Random(cls, shape=(), low=0, high=None, dtype=None):
        """
        Creates a Galois field array with random field elements.

        Parameters
        ----------
        shape : tuple
            A numpy-compliant `shape` tuple, see :obj:`numpy.ndarray.shape`. An empty tuple `()` represents a scalar.
            A single integer or 1-tuple, e.g. `N` or `(N,)`, represents the size of a 1-dim array. An n-tuple, e.g.
            `(M,N)`, represents an n-dim array with each element indicating the size in each dimension.
        low : int, optional
            The lowest value (inclusive) of a random field element. The default is 0.
        high : int, optional
            The highest value (exclusive) of a random field element. The default is `None` which represents the
            field's order :math:`p^m`.
        dtype : numpy.dtype, optional
            The :obj:`numpy.dtype` of the array elements. The default is `None` which represents the smallest valid
            dtype for this class, i.e. the first element in :obj:`galois.GFMeta.dtypes`.

        Returns
        -------
        galois.GFArray
            A Galois field array of random field elements.

        Examples
        --------
        .. ipython:: python

            GF = galois.GF(31)
            GF.Random((2,5))
        """
        dtype = cls._get_dtype(dtype)
        high = cls.order if high is None else high
        if not 0 <= low < high <= cls.order:
            raise ValueError(f"Arguments must satisfy `0 <= low < high <= order`, not `0 <= {low} < {high} <= {cls.order}`.")

        if dtype != np.object_:
            array = np.random.randint(low, high, shape, dtype=dtype)
        else:
            array = np.empty(shape, dtype=dtype)
            iterator = np.nditer(array, flags=["multi_index", "refs_ok"])
            for _ in iterator:
                array[iterator.multi_index] = random.randint(low, high - 1)

        return array.view(cls)

    @classmethod
    def Elements(cls, dtype=None):
        """
        Creates a Galois field array of the field's elements :math:`\\{0, \\dots, p^m-1\\}`.

        Parameters
        ----------
        dtype : numpy.dtype, optional
            The :obj:`numpy.dtype` of the array elements. The default is `None` which represents the smallest valid
            dtype for this class, i.e. the first element in :obj:`galois.GFMeta.dtypes`.

        Returns
        -------
        galois.GFArray
            A Galois field array of all the field's elements.

        Examples
        --------
        .. ipython:: python

            GF = galois.GF(31)
            GF.Elements()
        """
        return cls.Range(0, cls.order, step=1, dtype=dtype)

    @classmethod
    def Vector(cls, array, dtype=None):
        """
        Creates a Galois field array over :math:`\\mathrm{GF}(p^m)` from length-:math:`m` vectors over the prime subfield :math:`\\mathrm{GF}(p)`.

        Parameters
        ----------
        array : array_like
            The input array with field elements in :math:`\\mathrm{GF}(p)` to be converted to a Galois field array in :math:`\\mathrm{GF}(p^m)`.
            The last dimension of the input array must be :math:`m`. An input array with shape `(n1, n2, m)` has output shape `(n1, n2)`.
        dtype : numpy.dtype, optional
            The :obj:`numpy.dtype` of the array elements. The default is `None` which represents the smallest valid
            dtype for this class, i.e. the first element in :obj:`galois.GFMeta.dtypes`.

        Returns
        -------
        galois.GFArray
            A Galois field array over :math:`\\mathrm{GF}(p^m)`.

        Examples
        --------
        .. ipython:: python

            GF = galois.GF(2**6)
            vec = galois.GF2.Random((3,6)); vec
            a = GF.Vector(vec); a
            with GF.display("poly"):
                print(a)
            a.vector()
        """
        order = cls.prime_subfield.order
        degree = cls.degree
        array = cls.prime_subfield(array).view(np.ndarray).astype(cls.dtypes[-1])  # Use the largest dtype so computation doesn't overflow
        if not array.shape[-1] == degree:
            raise ValueError(f"The last dimension of `array` must be the field extension dimension {cls.degree}, not {array.shape[-1]}.")
        degrees = np.arange(degree - 1, -1, -1, dtype=cls.dtypes[-1])
        array = np.sum(array * order**degrees, axis=-1)
        return cls(array, dtype=dtype)

    ###############################################################################
    # Array methods
    ###############################################################################

    def vector(self, dtype=None):
        """
        Converts the Galois field array over :math:`\\mathrm{GF}(p^m)` to length-:math:`m` vectors over the prime subfield :math:`\\mathrm{GF}(p)`.

        For an input array with shape `(n1, n2)`, the output shape is `(n1, n2, m)`.

        Parameters
        ----------
        dtype : numpy.dtype, optional
            The :obj:`numpy.dtype` of the array elements. The default is `None` which represents the smallest valid
            dtype for this class, i.e. the first element in :obj:`galois.GFMeta.dtypes`.

        Returns
        -------
        galois.GFArray
            A Galois field array of length-:math:`m` vectors over :math:`\\mathrm{GF}(p)`.

        Examples
        --------
        .. ipython:: python

            GF = galois.GF(2**6)
            a = GF.Random(3); a
            vec = a.vector(); vec
            GF.Vector(vec)
        """
        order = type(self).prime_subfield.order
        degree = type(self).degree
        array = self.view(np.ndarray)
        array = np.repeat(array, degree).reshape(*array.shape, degree)
        x = 0
        for i in range(degree):
            q = (array[...,i] - x) // order**(degree - 1 - i)
            array[...,i] = q
            x += q*order**(degree - 1 - i)
        return type(self).prime_subfield(array, dtype=dtype)

    def row_reduce(self, ncols=None):
        """
        Performs Gaussian elimination on the matrix to achieve reduced row echelon form.

        **Row reduction operations**

        1. Swap the position of any two rows.
        2. Multiply a row by a non-zero scalar.
        3. Add one row to a scalar multiple of another row.

        Parameters
        ----------
        ncols : int, optional
            The number of columns to perform Gaussian elimination over. The default is `None` which represents
            the number of columns of the input array.

        Returns
        -------
        galois.GFArray
            The reduced row echelon form of the input array.

        Examples
        --------
        .. ipython:: python

            GF = galois.GF(31)
            A = GF.Random((4,4)); A
            A.row_reduce()
            np.linalg.matrix_rank(A)

        One column is a linear combination of another.

        .. ipython:: python

            GF = galois.GF(31)
            A = GF.Random((4,4)); A
            A[:,2] = A[:,1] * GF(17); A
            A.row_reduce()
            np.linalg.matrix_rank(A)

        One row is a linear combination of another.

        .. ipython:: python

            GF = galois.GF(31)
            A = GF.Random((4,4)); A
            A[3,:] = A[2,:] * GF(8); A
            A.row_reduce()
            np.linalg.matrix_rank(A)
        """
        return row_reduce(self, ncols=ncols)

    def lu_decompose(self):
        """
        Decomposes the input array into the product of lower and upper triangular matrices.

        Returns
        -------
        galois.GFArray
            The lower triangular matrix.
        galois.GFArray
            The upper triangular matrix.

        Examples
        --------
        .. ipython:: python

            GF = galois.GF(5)

            # Not every square matrix has an LU decomposition
            A = GF([[2, 4, 4, 1], [3, 3, 1, 4], [4, 3, 4, 2], [4, 4, 3, 1]])
            L, U = A.lu_decompose()
            L
            U

            # A = L U
            np.array_equal(A, L @ U)
        """
        return lu_decompose(self)

    def lup_decompose(self):
        """
        Decomposes the input array into the product of lower and upper triangular matrices using partial pivoting.

        Returns
        -------
        galois.GFArray
            The lower triangular matrix.
        galois.GFArray
            The upper triangular matrix.
        galois.GFArray
            The permutation matrix.

        Examples
        --------
        .. ipython:: python

            GF = galois.GF(5)
            A = GF([[1, 3, 2, 0], [3, 4, 2, 3], [0, 2, 1, 4], [4, 3, 3, 1]])
            L, U, P = A.lup_decompose()
            L
            U
            P

            # P A = L U
            np.array_equal(P @ A, L @ U)
        """
        return lup_decompose(self)

    ###############################################################################
    # Overridden numpy methods
    ###############################################################################

    def astype(self, dtype, **kwargs):  # pylint: disable=arguments-differ
        if dtype not in type(self).dtypes:
            raise TypeError(f"{type(self).name} arrays can only be cast as integer dtypes in {type(self).dtypes}, not {dtype}.")
        return super().astype(dtype, **kwargs)

    def __array_finalize__(self, obj):
        """
        A numpy dunder method that is called after "new", "view", or "new from template". It is used here to ensure
        that view casting to a Galois field array has the appropriate dtype and that the values are in the field.
        """
        if obj is not None and not isinstance(obj, GFArray):
            # Only invoked on view casting
            if obj.dtype not in type(self).dtypes:
                raise TypeError(f"{type(self).name} can only have integer dtypes {type(self).dtypes}, not {obj.dtype}.")
            if np.any(obj < 0) or np.any(obj >= type(self).order):
                idxs = np.logical_or(obj < 0, obj >= type(self).order)
                raise ValueError(f"{type(self).name} arrays must have values in 0 <= x < {type(self).order}, not {obj[idxs]}.")

    def __getitem__(self, key):
        item = super().__getitem__(key)
        if np.isscalar(item):
            # Return scalar array elements as 0-dimension Galois field arrays. This enables Galois field arithmetic
            # on scalars, which would otherwise be implemented using standard integer arithmetic.
            item = self.__class__(item, dtype=self.dtype)
        return item

    def __setitem__(self, key, value):
        # Verify the values to be written to the Galois field array are in the field
        value = self._check_array_like_object(value)
        super().__setitem__(key, value)

    def __array_function__(self, func, types, args, kwargs):
        if func in OVERRIDDEN_FUNCTIONS:
            output = OVERRIDDEN_FUNCTIONS[func](*args, **kwargs)

        elif func in UNSUPPORTED_FUNCTIONS:
            raise NotImplementedError(f"The numpy function '{func.__name__}' is not supported on Galois field arrays. If you believe this function should be supported, please submit a GitHub issue at https://github.com/mhostetter/galois/issues.\n\nIf you'd like to perform this operation on the data (but not necessarily a Galois field array), you should first call `array = array.view(np.ndarray)` and then call the function.")

        else:
            if func is np.insert:
                args = list(args)
                args[2] = self._check_array_like_object(args[2])
                args = tuple(args)

            output = super().__array_function__(func, types, args, kwargs)  # pylint: disable=no-member

            if func in FUNCTIONS_REQUIRING_VIEW:
                if np.isscalar(output):
                    output = type(self)(output, dtype=self.dtype)
                else:
                    output = output.view(type(self))

        return output

    def __array_ufunc__(self, ufunc, method, *inputs, **kwargs):  # pylint: disable=too-many-branches
        # print(ufunc, method, inputs, kwargs)
        meta = {}
        meta["types"] = [type(inputs[i]) for i in range(len(inputs))]
        meta["operands"] = list(range(len(inputs)))
        if method in ["at", "reduceat"]:
            # Remove the second argument for "at" ufuncs which is the indices list
            meta["operands"].pop(1)
        meta["field_operands"] = [i for i in meta["operands"] if isinstance(inputs[i], self.__class__)]
        meta["non_field_operands"] = [i for i in meta["operands"] if not isinstance(inputs[i], self.__class__)]
        meta["field"] = self.__class__
        meta["dtype"] = self.dtype
        # meta["ufuncs"] = self._ufuncs

        if ufunc in OVERRIDDEN_UFUNCS:
            # Set all ufuncs with "casting" keyword argument to "unsafe" so we can cast unsigned integers
            # to integers. We know this is safe because we already verified the inputs.
            if method not in ["reduce", "accumulate", "at", "reduceat"]:
                kwargs["casting"] = "unsafe"

            # Need to set the intermediate dtype for reduction operations or an error will be thrown. We
            # use the largest valid dtype for this field.
            if method in ["reduce"]:
                kwargs["dtype"] = type(self).dtypes[-1]

            return getattr(type(self), OVERRIDDEN_UFUNCS[ufunc])(ufunc, method, inputs, kwargs, meta)

        elif ufunc in UNSUPPORTED_UFUNCS:
            raise NotImplementedError(f"The numpy ufunc '{ufunc.__name__}' is not supported on Galois field arrays. If you believe this ufunc should be supported, please submit a GitHub issue at https://github.com/mhostetter/galois/issues.")

        else:
            inputs, kwargs = type(self)._view_inputs_as_ndarray(inputs, kwargs)
            output = super().__array_ufunc__(ufunc, method, *inputs, **kwargs)  # pylint: disable=no-member

            if ufunc in UFUNCS_REQUIRING_VIEW:
                output = output.view(type(self))

            return output

    ###############################################################################
    # Display methods
    ###############################################################################

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        # pylint: disable=attribute-defined-outside-init
        formatter = {}
        if type(self).display_mode == "poly":
            formatter["int"] = self._print_poly
            formatter["object"] = self._print_poly
        elif type(self).display_mode == "power":
            nonzero_idxs = np.nonzero(self)
            if self.ndim > 1:
                self._display_power_pre_width = 0 if nonzero_idxs[0].size == self.size else 1
                max_power = np.max(np.log(self[nonzero_idxs]))
                if max_power > 1:
                    self._display_power_width = self._display_power_pre_width + 2 + len(str(max_power))
                else:
                    self._display_power_width = self._display_power_pre_width + 1
            else:
                self._display_power_pre_width = None
                self._display_power_width = None
            formatter["int"] = self._print_power
            formatter["object"] = self._print_power
        elif self.dtype == np.object_:
            formatter["object"] = self._print_int

        cls = type(self)
        class_name = cls.__name__
        with np.printoptions(formatter=formatter):
            cls.__name__ = "GF"  # Rename the class so very large fields don't create large indenting
            string = super().__repr__()
        cls.__name__ = class_name

        if cls.degree == 1:
            order = "{}".format(cls.order)
        else:
            order = "{}^{}".format(cls.characteristic, cls.degree)

        # Remove the dtype from the repr and add the Galois field order
        dtype_idx = string.find("dtype")
        if dtype_idx == -1:
            string = string[:-1] + f", order={order})"
        else:
            string = string[:dtype_idx] + f"order={order})"

        return string

    @staticmethod
    def _print_int(element):
        return "{:d}".format(int(element))

    def _print_poly(self, element):
        poly = integer_to_poly(element, type(self).characteristic)
        poly_var = "α" if type(self).primitive_element == type(self).characteristic else "x"
        return poly_to_str(poly, poly_var=poly_var)

    def _print_power(self, element):
        if element == 0:
            s = "-∞"
        else:
            power = type(self)._ufuncs["log"](element)
            if power > 1:
                s = f"α^{power}"
            elif power == 1:
                s = "α"
            else:
                s = "1"

            if self._display_power_pre_width:
                s = " " + s

        if self._display_power_width:
            return s + " "*(self._display_power_width - len(s))
        else:
            return s

    @classmethod
    def _poly_eval(cls, coeffs, x):
        coeffs = cls(coeffs)  # Convert coefficient into the field
        coeffs = coeffs.view(np.ndarray)  # View cast to normal integers so ufunc_poly_eval call uses normal arithmetic
        coeffs = np.atleast_1d(coeffs)
        if coeffs.size == 1:
            # TODO: Why must coeffs have atleast 2 elements otherwise it will be converted to a scalar, not 1d array?
            coeffs = np.insert(coeffs, 0, 0)

        x = cls(x)  # Convert evaluation values into the field (checks that values are in the field)
        x = x.view(np.ndarray)  # View cast to normal integers so ufunc_poly_eval call uses normal arithmetic
        x = np.atleast_1d(x)

        if cls.dtypes[-1] == np.object_:
            # For object dtypes, call the vectorized classmethod
            y = cls._ufuncs["poly_eval"](coeffs=coeffs, values=x)  # pylint: disable=not-callable
        else:
            # For integer dtypes, call the JIT-compiled gufunc
            y = np.copy(x)
            cls._ufuncs["poly_eval"](coeffs, x, y, casting="unsafe")  # pylint: disable=not-callable

        y = cls(y)
        if y.size == 1:
            y = y[0]

        return y
