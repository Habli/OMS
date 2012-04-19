"""
Manin Maps.

This is a class that represents maps from a set of right coset
representatives to a coefficient module.  This is a basic building
block for implementing modular symbols, and provides basic arithmetic
and right action of matrices.


"""
from sage.rings.arith import convergents
from sage.matrix.matrix_integer_2x2 import MatrixSpace_ZZ_2x2, Matrix_integer_2x2
M2Z = MatrixSpace_ZZ_2x2()
t00 = (0,0)
t10 = (1,0)
t01 = (0,1)
t11 = (1,1)

def unimod_matrices_to_infty(r, s):
    """
    Returns a list of matrices whose associated unimodular paths
    connect r/s to infty.  (This is Manin's continued fraction trick.)

    INPUT:

    - r,s -- rational numbers

    OUTPUT:

    - a list of matrices in `SL_2(\ZZ)`

    EXAMPLES::

        sage: from sage.modular.pollack_stevens.manin_map import unimod_matrices_to_infty
        sage:
    """
    if s == 0:
        return []
    # the function contfrac_q in
    # https://github.com/williamstein/psage/blob/master/psage/modform/rational/modular_symbol_map.pyx
    # is very, very relevant to massively optimizing this.
    L = convergents(r / s)
    # Computes the continued fraction convergents of r/s
    v = [M2Z([1, L[0].numerator(), 0, L[0].denominator()])]
    # Initializes the list of matrices
    for j in range(0, len(L)-1):
        a = L[j].numerator()
        c = L[j].denominator()
        b = L[j + 1].numerator()
        d = L[j + 1].denominator()
        v.append(M2Z([(-1)**(j + 1) * a, b, (-1)**(j + 1) * c, d]))
        # The matrix connecting two consecutive convergents is added on
    return v

def unimod_matrices_from_infty(r, s):
    """
    Returns a list of matrices whose associated unimodular paths connect r/s to infty.
    (This is Manin's continued fraction trick.)

    INPUT:
        r, s -- rational numbers

    OUTPUT:
        a list of SL_2(Z) matrices

    EXAMPLES:
    """
    if s != 0:
        L = convergents(r / s)
        # Computes the continued fraction convergents of r/s
        v = [M2Z([-L[0].numerator(), 1, -L[0].denominator(), 0])]
        # Initializes the list of matrices
        # the function contfrac_q in https://github.com/williamstein/psage/blob/master/psage/modform/rational/modular_symbol_map.pyx
        # is very, very relevant to massively optimizing this.
        for j in range(0, len(L) - 1):
            a = L[j].numerator()
            c = L[j].denominator()
            b = L[j + 1].numerator()
            d = L[j + 1].denominator()
            v.append(M2Z([-b, (-1)**(j + 1) * a, -d, (-1)**(j + 1) * c]))
            # The matrix connecting two consecutive convergents is added on
        return v
    else:
        return []


def basic_hecke_matrix(a, ell):
    """
    Returns the matrix [1, a, 0, ell] (if a<ell) and [ell, 0, 0, 1] if a>=ell

    INPUT:
        a -- an integer or Infinity
        ell -- a prime

    OUTPUT:
        a 2 x 2 matrix of determinant ell

    EXAMPLES:
    """
    if a < ell:
        return M2Z([1, a, 0, ell])
    else:
        return M2Z([ell, 0, 0, 1])

class ManinMap(object):
    """
    Map from a set of right coset representatives of Gamma0(N) in
    SL_2(Z) to a coefficient module that satisfies the Manin
    relations.
    """
    def __init__(self, codomain, manin_relations, defining_data, check=True):
        self._codomain = codomain
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

    def _compute_image_from_gens(self, B):
        L = self._manin._rel_dict[B]
        # could raise KeyError if B is not a coset rep
        if len(L) == 0:
            t = self._codomain(0)
        else:
            c, A, g = L[0]
            t = (self._dict[g] * A) * c
            for c, A, g in L[1:]:
                t += (self._dict[g] * A) * c
        return t

    def __getitem__(self, B):
        try:
            return self._dict[B]
        except KeyError:
            self._dict[B] = self._compute_image_from_gens(B)
            return self._dict[B]

    def compute_full_data(self):
        for B in self._manin.coset_reps():
            if not self._dict.has_key(B):
                self._dict[B] = self._compute_image_from_gens(B)

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
        return self.__class__(self._codomain, self._manin, D, check=False)

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
        return self.__class__(self._codomain, self._manin, D, check=False)

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
        return self.__class__(self._codomain, self._manin, D, check=False)

    def __repr__(self):
        return "Map from the set of right cosets of Gamma0(%s) in SL_2(Z) to %s"%(
            self._manin.level(), self._codomain)

    def _eval_sl2(self, A):
        B = self._manin.find_coset_rep(A)
        gaminv = B * A.__invert__unit()
        return self[A] * gaminv

    def __call__(self, A):
        a = A[t00]
        b = A[t01]
        c = A[t10]
        d = A[t11]
        # v1: a list of unimodular matrices whose divisors add up to {b/d} - {infty}
        v1 = unimod_matrices_to_infty(b,d)
        # v2: a list of unimodular matrices whose divisors add up to {a/c} - {infty}
        v2 = unimod_matrices_to_infty(a,c)
        # ans: the value of self on A
        ans = self._codomain(0)
        # This loop computes self({b/d}-{infty}) by adding up the values of self on elements of v1
        for B in v1:
            ans = ans + self._eval_sl2(B)

        # This loops subtracts away the value self({a/c}-{infty}) from ans by subtracting away the values of self on elements of v2
        # and so in the end ans becomes self({b/d}-{a/c}) = self({A(0)} - {A(infty)}
        for B in v2:
            ans = ans - self._eval_sl2(B)
        return ans

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
        return self.__class__(self._codomain, self._manin, D, check=False)

    def __iter__(self):
        """
        Returns iterator over the values of this map on the reduced
        representatives.

        This might be used to compute the valuation.
        """
        for A in self._manin._gens:
            yield self._dict[A]

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
            D[ky] = self(gamma*ky) * gamma
        return self.__class__(self._codomain, self._manin, D, check=False)

    def _prep_hecke_on_gen(self, ell, m):
        """
        This function does some precomputations needed to compute T_ell.

        In particular, if phi is a modular symbol and D_m is the divisor associated to our m-th chosen
        generator, to compute (phi|T_ell)(D_m) one needs to compute phi(gam_a D_m)|gam_a where
        gam_a run thru the ell+1 matrices defining T_ell.  One then takes gam_a D_m and writes it
        as a sum of unimodular divisors.  For each such unimodular divisor, say [M] where M is a
        SL_2 matrix, we then write M=gam*M_i where gam is in Gamma_0(N) and M_i is one of our
        chosen coset representatives.  Then phi([M]) = phi([M_i]) | gam^(-1).  Thus, one has

            (phi | gam_a)(D_m) = sum_i sum_j phi([M_i]) | gam_{ij}^(-1) * gam_a

        as i runs over the indices of all coset representatives and j simply runs over however many
        times M_i appears in the above computation.

        Finally, the output of this function is a list L enumerated by the coset representatives
        in M.coset_reps() where each element of this list is a list of matrices, and the entries of L
        satisfy:

            L[i][j] = gam_{ij} * gam_a

        INPUT:
            -- ``ell`` - a prime
            -- ``m`` - index of a generator

        OUTPUT:

        A list of lists (see above).

        EXAMPLES:

        ::

        sage: E = EllipticCurve('11a')
        sage: from sage.modular.overconvergent.pollack.modsym_symk import form_modsym_from_elliptic_curve
        sage: phi = form_modsym_from_elliptic_curve(E); phi
        [-1/5, 3/2, -1/2]
        sage: phi.prep_hecke_individual(2,0)
        [[[1 0]
        [0 2], [1 1]
        [0 2], [2 0]
        [0 1]], [], [], [], [], [], [], [], [], [], [], [[ 1 -1]
        [ 0  2]]]

        The output the original version of this file claimed is the
        following, but this disagrees with what we get, and with the
        .sage version (which agree with each other)::
        [[[1 0]
        [0 2], [1 1]
        [0 2], [2 0]
        [0 1]], [], [], [], [], [], [[ 1 -1]
        [ 0  2]], [], [], [], [], []]

        """
        M = self._manin
        N = M.level()

        ans = [[] for a in range(len(M.coset_reps()))]
        # this will be the list L above enumerated by coset reps

        #  This loop will runs thru the ell+1 (or ell) matrices defining T_ell of the form [1, a, 0, ell] and carry out the computation
        #  described above.
        #  -------------------------------------
        for a in range(ell + 1):
           if (a < ell) or (N % ell != 0):
               # if the level is not prime to ell the matrix [ell, 0, 0, 1] is avoided.
               gama = basic_hecke_matrix(a, ell)
               t = gama*M.coset_reps(M.generator_indices(m))
               #  In the notation above this is gam_a * D_m
               v = unimod_matrices_from_infty(t[0, 0], t[1, 0]) + unimod_matrices_to_infty(t[0, 1], t[1, 1])
               #  This expresses t as a sum of unimodular divisors

               # This loop runs over each such unimodular divisor
               # ------------------------------------------------
               for b in range(len(v)):
                   A = v[b]
                   #  A is the b-th unimodular divisor
                   i = M.P1().index(A[1, 0], A[1, 1])
                   #  i is the index in SAGE P1 of the bottom row of A
                   j = M.P1_to_coset_index(i)
                   #  j is the index of our coset rep equivalent to A
                   B = M.coset_reps(j)
                   #  B is that coset rep
                   C = M2Z([A[1, 1], -A[0, 1], -A[1, 0], A[0, 0]])
                   #  C equals A^(-1).  This is much faster than just inverting thru SAGE
                   gaminv = B * C
                   #  gaminv = B*A^(-1)
                   ans[j] = ans[j] + [gaminv * gama]
                   #  The matrix gaminv * gama is added to our list in the j-th slot (as described above)

        return ans

    def prep_hecke(self, ell):
        """
        Carries out prep_hecke_individual for each generator index and puts all of the answers in a long list.

        INPUT:
            -- ``ell`` - a prime

        OUTPUT:

        A list of lists of lists

        EXAMPLES:

        ::

        sage: E = EllipticCurve('11a')
        sage: from sage.modular.overconvergent.pollack.modsym_symk import form_modsym_from_elliptic_curve
        sage: phi = form_modsym_from_elliptic_curve(E); phi
        [-1/5, 3/2, -1/2]
        sage: phi.prep_hecke(2)
        [[[[1 0]
        [0 2], [1 1]
        [0 2], [2 0]
        [0 1]], [], [], [], [], [], [], [], [], [], [], [[ 1 -1]
        [ 0  2]]], [[[1 2]
        [0 2], [1 1]
        [0 2], [2 1]
        [0 1]], [[ 1 -2]
        [ 0  2], [ 1 -1]
        [ 0  2], [ 2 -1]
        [ 0  1]], [], [[-4 -2]
        [11  5], [-8 -3]
        [22  8]], [], [], [], [], [], [[1 0]
        [0 2]], [[-5 -2]
        [11  4], [-1  1]
        [ 0 -2]], []], [[[1 2]
        [0 2], [1 1]
        [0 2], [2 1]
        [0 1]], [[1 0]
        [0 2], [ 1 -1]
        [ 0  2], [2 0]
        [0 1]], [], [], [[-6 -4]
        [11  7]], [[-7 -4]
        [11  6], [-1  1]
        [ 0 -2], [-2  0]
        [ 0 -1]], [], [], [[-1  0]
        [ 0 -2]], [[1 0]
        [0 2]], [], [[-5 -2]
        [11  4]]]]

        WARNING: changed from this (which disagreed with .sage file):
        [[[[1 0]
        [0 2], [1 1]
        [0 2], [2 0]
        [0 1]], [], [], [], [], [], [[ 1 -1]
        [ 0  2]], [], [], [], [], []], [[[1 2]
        [0 2], [1 1]
        [0 2], [2 1]
        [0 1]], [[ 1 -2]
        [ 0  2], [ 1 -1]
        [ 0  2], [ 2 -1]
        [ 0  1]], [], [[-4 -2]
        [11  5], [-8 -3]
        [22  8]], [], [], [], [[-5 -2]
        [11  4], [-1  1]
        [ 0 -2]], [[1 0]
        [0 2]], [], [], []], [[[1 2]
        [0 2], [1 1]
        [0 2], [2 1]
        [0 1]], [[1 0]
        [0 2], [ 1 -1]
        [ 0  2], [2 0]
        [0 1]], [], [], [[-6 -4]
        [11  7]], [[-7 -4]
        [11  6], [-1  1]
        [ 0 -2], [-2  0]
        [ 0 -1]], [[-5 -2]
        [11  4]], [], [[1 0]
        [0 2]], [[-1  0]
        [ 0 -2]], [], []]]

        """
        ans = []
        for m in range(len(self._manin.generator_indices()))
            ans = ans + [self._prep_hecke_individual(ell, m)]
        return ans

    def _grab_relations(self):
        v = []
        for r in range(len(self._manin.coset_reps())):
            for j in range(self._manin.coset_reps()):
                R = self._manin.coset_relations[j]
                if (len(R) == 1) and (R[0][2] == self._manin().generator_indices(r)):
                    if R[0][0] <> -1 or R[0][1] <> Id:
                        v = v + [R]
        return v

