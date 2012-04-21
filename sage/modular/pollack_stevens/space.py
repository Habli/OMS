from sage.modules.module import Module
from sage.structure.factory import UniqueFactory
from distributions import Distributions
from sage.modular.dirichlet import DirichletCharacter
from sage.modular.arithgroup.all import Gamma0
from sage.rings.integer import Integer
from sage.rings.rational_field import QQ
from sage.rings.integer_ring import ZZ
from modsym import PSModularSymbolElement_symk, PSModularSymbolElement_dist, PSModSymAction
from fund_domain import ManinRelations, M2ZSpace
from sage.rings.padics.precision_error import PrecisionError
from sage.rings.infinity import infinity as oo

class PSModularSymbols_constructor(UniqueFactory):
    def create_key(self, group, weight=None, sign=0, base_ring=None, p=None, prec_cap=None, coefficients=None):
        if isinstance(group, (int, Integer)):
            group = Gamma0(group)
        if coefficients is None:
            if isinstance(group, DirichletCharacter):
                character = group.minimize_base_ring()
                group = Gamma0(character.modulus())
                character = (character, None)
            else:
                character = None
            if weight is None: raise ValueError("you must specify a weight or coefficient module")
            k = weight - 2
            coefficients = Distributions(k, p, prec_cap, base_ring, character)
        else:
            # TODO: require other stuff to be None
            pass
        return (group, coefficients, sign)

    def create_object(self, version, key):
        return PSModularSymbolSpace(*key)

PSModularSymbols = PSModularSymbols_constructor('PSModularSymbols')

class PSModularSymbolSpace(Module):
    """
    A class for spaces of modular symbols that use Glenn Stevens'
    conventions.

    There are two main differences between the modular symbols in this
    directory and the ones in sage.modular.modsym.

    - There is a shift in the weight: weight `k=0` here corresponds to
      weight `k=2` there.

    - There is a duality: these modular symbols are functions from
      `Div^0(P^1(\QQ))`, the others are formal linear combinations of
      such elements.

    INPUT:

    - ``V`` -- the coefficient module, which should have a right action of `M_2(\ZZ)`

    - ``domain`` -- a set or None, giving the domain
    """
    def __init__(self, group, coefficients, sign=None):
        Module.__init__(self, coefficients.base_ring())
        if sign == None:
            sign = 0
            # sign should be 0, 1 or -1
        self._group = group
        self._coefficients = coefficients
        if coefficients.is_symk():
            self.Element = PSModularSymbolElement_symk
        else:
            self.Element = PSModularSymbolElement_dist
        self._sign = sign
        # should distingish between Gamma0 and Gamma1...
        self._manin_relations = ManinRelations(group.level())
        # We have to include the first action so that scaling by Z doesn't try to pass through matrices
        actions = [PSModSymAction(ZZ, self), PSModSymAction(M2ZSpace, self)]
        self._populate_coercion_lists_(action_list=actions)

    def _repr_(self):
        r"""
        Returns print representation.
        """
        s = "Space of overconvergent modular symbols for %s with sign %s and values in %s"%(self.group(), self.sign(), self.coefficient_module())
        return s

    def source(self):
        return self._manin_relations

    def coefficient_module(self):
        r"""
        Returns the coefficient module of self.

        EXAMPLES::


        """
        return self._coefficients

    def group(self):
        r"""
        Returns the congruence subgroup of self.

        EXAMPLES::

            sage: D = Distributions(2, 5)
            sage: G = Gamma0(23)
            sage: M = PSModularSymbolSpace(G, D)
            sage: M.group()
            Congruence Subgroup Gamma0(23)
            sage: D = Distributions(4)
            sage: G = Gamma1(11)
            sage: M = PSModularSymbolSpace(G, D)
            sage: M.group()
            Congruence Subgroup Gamma1(11)

        """
        return self._group

    def sign(self):
        r"""
        Returns the sign of self.

        EXAMPLES::

            sage: D = Distributions(3, 17)
            sage: M = PSModularSymbolSpace(Gamma(5), D)
            sage: M.sign()
            0
            sage: D = Distributions(4)
            sage: M = PSModularSymbolSpace(Gamma1(8), D, -1)
            sage: M.sign()
            -1

        """
        return self._sign

    def ngens(self):
        r"""
        Returns the number of generators defining self.

        EXAMPLES::

            sage: D = Distributions(4, 29)
            sage: M = PSModularSymbolSpace(Gamma1(12), D)
            sage: M.ngens()
            5
            sage: D = Distributions(2)
            sage: M = PSModularSymbolSpace(Gamma0(2), D)
            sage: M.ngens()
            2

        """
        return len(self._manin_relations.indices())

    def ncoset_reps(self):
        r"""
        Returns the number of coset representatives defining the full_data of self

        OUTPUT:
        The number of coset representatives stored in the manin relations. (Just the size
        of P^1(Z/NZ))

        EXAMPLES::

            sage: D = Distributions(2)
            sage: M = PSModularSymbolSpace(Gamma0(2), D)
            sage: M.ncoset_reps()
            3

        """
        return len(self._manin_relations.reps())

    def level(self):
        r"""
        Returns the level `N` when self is of level `Gamma_0(N)`.

        INPUT:
            none

        OUTPUT:

        The level `N` when self is of level `Gamma_0(N)`

        EXAMPLES::

            sage: D = Distributions(7, 11)
            sage: M = PSModularSymbolSpace(Gamma1(14), D)
            sage: M.level()
            14

        """

        return self._manin_relations.level()

    def _grab_relations(self):
        r"""


        EXAMPLES::

            sage: D = Distributions(4, 3)
            sage: M = PSModularSymbolSpace(Gamma1(13), D)
            sage: M._grab_relations()
            [[(1, [1 0]
            [0 1], 0)], [(-1, [-1 -1]
            [ 0 -1], 0)], [(1, [1 0]
            [0 1], 2)], [(1, [1 0]
                [0 1], 3)], [(1, [1 0]
                    [0 1], 4)], [(1, [1 0]
                        [0 1], 5)]]

        """

        v = []
        for r in range(len(self._manin_relations.gens())):
            for j in range(len(self._manin_relations.reps())):
                R = self._manin_relations.relations(j)
                if (len(R) == 1) and (R[0][2] == self._manin_relations.indices(r)):
                    if R[0][0] <> -1 or R[0][1] <> M2ZSpace.one():
                        v = v + [R]
        return v

    def zero_element(self):
        r"""
        Returns the zero element of the space where self takes values.

        INPUT:
            none

        OUTPUT:

        The zero element in the space where self takes values.

        EXAMPLES::

            sage: D = Distributions(2)
            sage: M = PSModularSymbolSpace(Gamma(3), D)
            sage: M.zero_element()
            (0, 0, 0)
        """
        return self.coefficient_module().zero_element()

    def zero(self):
        r"""
        Returns the modular symbol all of whose values are zero.

        INPUT:
            none

        OUTPUT:

        The zero modular symbol of self.

        EXAMPLES::

            sage: D = Distributions(4,2)
            sage: M = PSModularSymbolSpace(Gamma1(6), D)
            sage: M.zero()
            A modular symbol with values in Space of 2-adic distributions with
            k=4 action and precision cap 5

        """
        D = {}
        for rep in self._manin_relations.reps():
            D[rep] = self.zero_element()
        #v = [self.zero_elt() for i in range(0, self.ngens())]
        #return C(v, self._manin_relations)
        return self(D)

    def precision_cap(self):
        r"""
        Returns the number of moments of each value of self.

        EXAMPLES::

            sage: D = Distributions(2, 5)
            sage: M = PSModularSymbolSpace(Gamma1(13), D)
            sage: M.precision_cap()
            3
            sage: D = Distributions(3, 7, prec_cap=10)
            sage: M = PSModularSymbolSpace(Gamma0(7), D)
            sage: M.precision_cap()
            10

        """

        return self.coefficient_module()._prec_cap

    def weight(self):
        r"""
        Returns the weight of self.

        EXAMPLES::

            sage: D = Distributions(5)
            sage: M = PSModularSymbolSpace(Gamma1(7), D)
            sage: M.weight()
            5

        """
        return self.coefficient_module()._k

    def prime(self):
        r"""
        Returns the prime of self.

        EXAMPLES:
            sage: D = Distributions(2, 11)
            sage: M = PSModularSymbolSpace(Gamma(2), D)
            sage: M.prime()
            11

        """
        return self.coefficient_module()._p

    def p_stabilize(self, p, M=None, check=True):
        r"""
        Returns the zero element of the space where self takes values.

        INPUT:
            - ``p`` -- prime number
            - ``M`` -- number of moments

        OUTPUT:

        The space of modular symbols of level p * N, where N is the level of
        self, with precision M.

        EXAMPLES::

            sage: D = Distributions(2, 7)
            sage: M = PSModularSymbolSpace(Gamma(13), D)
            sage: M.p_stabilize(7)
            Space of overconvergent modular symbols for Congruence Subgroup
            Gamma(91) with sign 0 and values in Space of 7-adic distributions
            with k=2 action and precision cap 3
            sage: D = Distributions(4, 17)
            sage: M = PSModularSymbolSpace(Gamma1(3), D)
            sage: M.p_stabilize(17, 15)
            Space of overconvergent modular symbols for Congruence Subgroup
            Gamma1(51) with sign 0 and values in Space of 17-adic distributions
            with k=4 action and precision cap 15
        """

        if M == None:
            M = self.precision_cap()
        N = self.level()
        if check and N % p == 0:
            raise ValueError("the level isn't prime to p")
        from sage.modular.arithgroup.all import Gamma, is_Gamma, Gamma0, is_Gamma0, Gamma1, is_Gamma1
        G = self.group()
        if is_Gamma0(G):
            G = Gamma0(N*p)
        elif is_Gamma1(G):
            G = Gamma1(N*p)
        elif is_Gamma(G):
            G = Gamma(N*p)
        else:
            raise NotImplementedError
        return PSModularSymbols(G, coefficients=self.coefficient_module().lift(p, M), sign=self.sign())

    def _an_element_(self):
        r"""
        Returns an element of self

        EXAMPLES:
            sage: D = Distributions(4)
            sage: M = PSModularSymbolSpace(Gamma(6), D)
            sage: M.an_element()
            A modular symbol with values in Sym^4 Q^2
            sage: D = Distributions(2, 11)
            sage: M = PSModularSymbolSpace(Gamma0(2), D)
            sage: M.an_element()
            A modular symbol with values in Space of 11-adic distributions with
            k=2 action and precision cap 3

        """

        D = {}
        for g in self.source().gens():
            D[g] = self.coefficient_module().an_element()
        return self(D)

    def random_element(self, M):
        r"""
        Returns a random OMS with tame level `N`, prime `p`, weight `k`, and
        `M` moments --- requires no `2` or `3`-torsion
        INPUT:

        - M: the number of moments

        OUTPUT:

        - A random element of self

        EXAMPLES:


        ::


        """

        if M > self.precision_cap():
            raise PrecisionError ("Too many moments requested.")

        # Sorry, I messed this up.
        # Somebody who understands the details should take a careful look.
        N = self.level()
        p = self.prime()
        if p == None:
            p = 1
        manin = ManinRelations(N * p)
        D = {}
        for g in manin.gens()[1:]:
            mu = self.coefficient_module().random_element(M)
            if g in manin.reps_with_two_torsion:
                rj = manin.indices_with_two_torsion[g]
                gam = manin.two_torsion[rj]
                D[g] = mu.act_right(gam)._sub_(mu)._lmul_(ZZ(1) / ZZ(2))
            else:
                D[g] = mu
        #t = self.zero()
        print "gens", manin.gens()
        for j in range(2, len(manin.relations())):
            R = manin.relations(j)
            if len(R) == 1:
                print "R=", R
                if R[0][0] == 1:
                    print "j=", j
                    print "indices(j)", manin.indices(j)
                    rj = manin.gens()[j -1] #manin.indices(j - 1)]
                    #t = t + D[rj]
                    # Should t do something?
                else:
                    index = R[0][2]
                    rj = manin.gens()[index - 1]
                    mu = D[rj]
                    #t = t + mu.act_right(R[0][1])._lmul_(R[0][0])
                    # Should t do something?
        D[manin.gens()[0]] = mu._lmul_(-1)
        return modsym_dist(D, self)

def cusps_from_mat(g):
    r"""
    Returns the cusps associated to an element of a congruence subgroup.

    INPUT:

    - ``g`` -- the matrix associated to an element of a congruence subgroup

    OUTPUT:

    - The cusps associated to ``g``

    EXAMPLES::
        sage: g = SL2Z.one().matrix()
        sage: cusps_from_mat(g)
        (+Infinity, 0)
        sage: g = GammaH(3, [2]).generators()[1]
        sage: cusps_from_mat(g)
        (1/3, 1/2)
    """
    a, b, c, d = g.list()
    if c: ac = a/c
    else: ac = oo
    if d: bd = b/d
    else: bd = oo
    return ac, bd

def form_modsym_from_elliptic_curve(E):
    r"""
        Returns the PS modular symbol associated to an elliptic curve defined
        over the rationals.
        INPUT:

        - ``E`` -- an elliptic curve defined over the rationals

        OUTPUT:

        - the Pollack-Stevens modular symbol associated to ``E``

        EXAMPLES::

        sage: E = EllipticCurve('113a1')
        sage: symb = form_modsym_from_elliptic_curve(E)
        sage: symb
        A modular symbol with values in Sym^0 Q^2
        sage: symb.values()
        [-1/2, 3/2, -2, 1/2, 0, 1, 2, -3/2, 0, -3/2, 0, -1/2, 0, 1, -2, 1/2, 0,
        0, 2, 0, 0]
        sage: E = EllipticCurve([0,1])
        sage: symb = form_modsym_from_elliptic_curve(E)
        sage: symb.values()
        [-1/6, 7/12, 1, 1/6, -5/12, 1/3, -7/12, -1, -1/6, 5/12, 1/4, -1/6,
        -5/12]

        """
    if not E.base_ring() is QQ:
        raise ValueError ("The elliptic curve must be defined over the
        rationals.")
    N = E.conductor()
    V = PSModularSymbols(Gamma0(N), 2)
    D = V.coefficient_module()
    manin = V.source()
    plus_sym = E.modular_symbol(sign = 1)
    minus_sym = E.modular_symbol(sign = -1)
    val = {}
    for g in manin.gens():
        ac, bd = cusps_from_mat(g)
        val[g] = D([plus_sym(ac) + minus_sym(ac) - plus_sym(bd) - minus_sym(bd)])
    return V(val)

def form_modsym_from_decomposition(A):
    """
    """
    M = A.ambient_module()
    w = A.dual_eigenvector()
    K = w.base_ring()
    V = PSModularSymbols(A.group(), A.weight(), base=K) # should eventually add sign as well.
    D = V.coefficient_module()
    N = V.level()
    k = V.weight() # = A.weight() - 2
    manin = V.source()
    val = {}
    for g in manin.gens():
        ac, bd = cusps_from_mat(g)
        v = []
        for j in range(k+1):
            # The following might be backward: it should be the coefficient of X^j Y^(k-j)
            v.append(w.dot_product(M.modular_symbol([j, ac, bd]).element()) * binomial(k, j))
        val[g] = D(v)
    return V(val)
