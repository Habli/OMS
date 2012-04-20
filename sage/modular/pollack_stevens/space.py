from sage.modules.module import Module
from sage.structure.factory import UniqueFactory
from distributions import Distributions
from sage.modular.dirichlet import DirichletCharacter
from sage.modular.arithgroup.all import Gamma0
from sage.rings.integer import Integer
from sage.rings.rational_field import QQ
from modsym import PSModularSymbolElement, PSModSymAction
from fund_domain import ManinRelations
from sage.rings.padics.precision_error import PrecisionError

class PSModularSymbols_constructor(UniqueFactory):
    def create_key(self, group, weight=None, sign=0, base_ring=None, p=None, prec_cap=None, coefficients=None):
        if isinstance(group, (int, Integer)):
            group = Gamma0(group)
        if base_ring is None and p is None:
            base_ring = QQ
        if coefficients is None:
            if p is not None and prec_cap is None:
                prec_cap = 20
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
    Element = PSModularSymbolElement
    def __init__(self, group, coefficients, sign=None):
        if sign == None:
            sign = 0
            # sign should be 0, 1 or -1
        self._group = group
        self._coefficients = coefficients
        self._sign = sign
        self._manin_relations = ManinRelations(group.level())
        # should distingish between Gamma0 and Gamma1...
        act = PSModSymAction(self)
        self._populate_coercion_lists_(action_list=[act])

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
            sage: M = PSModularSymbolSpace(Gamma0(5), D)
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

        # Should this return a dictionary as opposed to a list?
        v = []
        for r in range(len(self._manin_relations.reps())):
            for j in range(self._manin_relations.reps()):
                R = self._manin_relations[j]
                if (len(R) == 1) and (R[0][2] == self._manin_relations.indices(r)):
                    if R[0][0] <> -1 or R[0][1] <> Id:
                        v = v + [R]
        return v

    def zero_element(self):
        r"""
        Returns the zero element of the space where self takes values.

        INPUT:
            none

        OUTPUT:

        The zero element in the space where self takes values

        EXAMPLES::

            sage: D = Distributions(2)
            sage: M = PSModularSymbolSpace(Gamma0(3), D)
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

          #  sage: D = Distributions(4,2)
          #  sage: M = PSModularSymbolSpace(Gamma1(6), D)
          #  sage: M.zero()
          #  0

        """

        dd = {}
        for rep in self._manin_relations.reps():
            dd[rep] = self.zero_element()
        #v = [self.zero_elt() for i in range(0, self.ngens())]
        #return C(v, self._manin_relations)
        return PSModularSymbolElement(dd, self)

    def precision_cap(self):
        r"""
        Returns the number of moments of each value of self

        EXAMPLES::

            sage: D = Distributions(2, 5)
            sage: M = PSModularSymbolSpace(Gamma1(13), D)
            sage: M.precision_cap()
            20
            sage: D = Distributions(3, 7, prec_cap=10)
            sage: M = PSModularSymbolSpace(Gamma0(7), D)
            sage: M.precision_cap()
            10

        """
        return self.coefficient_module()._prec_cap

    def weight(self):
        r"""
        Returns the weight of self

        EXAMPLES::

            sage: D = Distributions(5)
            sage: M = PSModularSymbolSpace(Gamma1(7), D)
            sage: M.weight()
            5

        """
        return self.coefficient_module()._k

    def prime(self):
        r"""
        Returns the prime of self

        EXAMPLES:
            sage: D = Distributions(2, 11)
            sage: M = PSModularSymbolSpace(Gamma0(2), D)
            sage: M.prime()
            11

        """
        return self.coefficient_module()._p

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
            raise PrecisionError ("Too many moments for self.")

        # Sorry, I messed this up.
        # Somebody who understands the details should take a careful look.
        N = self.level()
        p = self.prime()
        if p == None:
            p = 1
        manin = ManinRelations(N * p)
        dd = {}
        for g in manin.gens()[1:]:
            mu = self.coefficient_module().random_element(M)
            if g in manin.reps_with_two_torsion:
                rj = manin.indices_with_two_torsion[g]
                gam = manin.two_torsion[rj]
                dd[g] = mu.act_right(gam)._sub_(mu)._lmul_(ZZ(1) / ZZ(2))
            else:
                dd[g] = mu
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
                    #t = t + dd[rj]
                    # Should t do something?
                else:
                    index = R[0][2]
                    rj = manin.gens()[index - 1]
                    mu = dd[rj]
                    #t = t + mu.act_right(R[0][1])._lmul_(R[0][0])
                    # Should t do something?
        dd[manin.gens()[0]] = mu._lmul_(-1)
        return modsym_dist(dd, self)


