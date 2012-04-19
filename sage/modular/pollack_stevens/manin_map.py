"""
Manin Maps.

This is a class that represents maps from a set of right coset
representatives to a coefficient module.  This is a basic building
block for implementing modular symbols, and provides basic arithmetic
and right action of matrices.


"""
from sage.matrix.matrix_integer_2x2 import MatrixSpace_ZZ_2x2, Matrix_integer_2x2
M2Z = MatrixSpace_ZZ_2x2()

class ManinMap(object):
    """
    Map from a set of right coset representatives of Gamma0(N) in
    SL_2(Z) to a coefficient module that satisfies the Manin
    relations.
    """
    def __init__(self, manin_relations, defining_data, check=True):
        self._manin = manin_relations
        if check:
            self._dict = {}
            if isinstance(defining_data, (list, tuple)):
                if len(defining_data) != len(manin_relations.gens()):
                    raise ValueError("length of defining data must be the same as number of manin generators")
                for i in range(len(defining_data)):
                    self._dict[manin_relations.coset_reps(i)] = defining_data[i]
            elif isinstance(defining_data, dict):
                for ky, val in defining_data.iteritems():
                    if not isinstance(ky, Matrix_integer_2x2):
                        # should eventually check that ky is actually a coset rep,
                        # handle elements of P^1, make sure that we cover all cosets....
                        ky = M2Z(ky)
                    self._dict[ky] = val
            else:
                raise TypeError("unrecognized type for defining_data")
        else:
            self._dict = defining_data

    def __getitem__(self, A):
        try:
            return self._dict[A]
        except KeyError:
            i = self._manin.P1().index(A[1,0],A[1,1])
            m = self._manin.P1_to_coset_index(i)
            B = self._manin.coset_reps(m)

    def __add__(self, right):
        """
        Return difference self + right, where self and right are
        assumed to have identical codomains and Manin relations.
        """
        D = {}
        sd = self._dict
        rd = right._dict
        for ky, val in sd.iteritems():
            if ky in rd:
                D[ky] = val + rd[ky]
        return self.__class__(self._manin, D, check=False)

    def __sub__(self, right):
        """
        Return difference self - right, where self and right are
        assumed to have identical codomains and Manin relations.
        """
        D = {}
        sd = self._dict
        rd = right._dict
        for ky, val in sd.iteritems():
            if ky in rd:
                D[ky] = val - rd[ky]
        return self.__class__(self._manin, D, check=False)

    def __mul__(self, right):
        """
        Return scalar multiplication self*right, where right is in the
        base ring of the codomain.
        """
        if isinstance(right, Matrix_integer_2x2):
            return self._right_action(right)
        D = {}
        sd = self._dict
        for ky, val in sd.iteritems():
            D[ky] = val * right
        return self.__class__(self._manin, D, check=False)

    def __repr__(self):
        return "Map from the set of right cosets of Gamma0(%s) in SL_2(Z) to %s"%(
            self._manin.level(), self._codomain)

    def __call__(self, A):
        # NOTE: we should use the high performance specialized type
        #   sage.matrix.matrix_integer_2x2.Matrix_integer_2x2
        # for our matrices.
        raise NotImplementedError

    def apply(self, f):
        """
        Returns Manin map given by x |--> f(self(x)), where f is
        anything that can be called with elements of the coefficient
        module.

        This might be used to normalize, reduce modulo a prime, change
        base ring, etc.
        """
        D = {}
        sd = self._dict
        for ky, val in sd.iteritems():
            D[ky] = f(val)
        return self.__class__(self._manin, D, check=False)

    def __iter__(self):
        """
        Returns iterator over the values of this map on the reduced
        representatives.

        This might be used to compute the valuation.
        """
        raise NotImplementedError

    def _right_action(self, gamma):
        """
        Returns self | gamma, where gamma is a 2x2 integer matrix.

        The action is defined by (self | gamma)(D) = self(gamma D)|gamma

        For the action by a single element gamma to be well defined,
        gamma must normalize Gamma_0(N).  However, this right action
        can also be used to define Hecke operators, in which case each
        individual self | gamma is not a modular symbol on Gamma_0(N),
        but the sum over acting by the appropriate double coset
        representatives is.

        INPUT:

        - ``gamma`` - 2 x 2 matrix which acts on the values of self

        OUTPUT:

        - ManinMap
        """
        D = {}
        sd = self._dict
        # we should eventually replace the for loop with a call to apply_many
        for ky, val in sd.iteritems():
            D[ky] = val * right
        return self.__class__(self._manin, D, check=False)

