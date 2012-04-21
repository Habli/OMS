from sage.structure.element import ModuleElement
from sage.matrix.matrix_integer_2x2 import MatrixSpace_ZZ_2x2
from sage.rings.integer_ring import ZZ
from manin_map import ManinMap
import operator
from sage.misc.cachefunc import cached_method
from sage.rings.padics.factory import Qp
from sage.rings.polynomial.all import PolynomialRing
from sage.rings.padics.padic_generic import pAdicGeneric

from sage.categories.action import Action

from fund_domain import M2ZSpace, M2Z, Id
minusproj = M2Z([1,0,0,-1])

class PSModSymAction(Action):
    def __init__(self, actor, MSspace):
        Action.__init__(self, actor, MSspace, False, operator.mul)

    def _call_(self, sym, g):
        return sym.__class__(sym._map * g, sym.parent(), construct=True)
    
class PSModularSymbolElement(ModuleElement):
    def __init__(self, map_data, parent, construct=False):
        ModuleElement.__init__(self, parent)
        if construct:
            self._map = map_data
        else:
            self._map = ManinMap(parent._coefficients, parent._manin_relations, map_data)

    def _repr_(self):
        return "Modular symbol with values in %s"%(self.parent().coefficient_module())

    def dict(self):
        D = {}
        for g in self.parent().source().gens():
            D[g] = self._map[g]
        return D

    def weight(self):
        """
        Return the weight of this Pollack-Stevens modular symbols.

        This is k-2, where k is the usual notion of weight for modular
        forms!!!

        
        """
        return self.parent().weight()

    def values(self):
        return [self._map[g] for g in self.parent().source().gens()]

    def __cmp__(self, other):
        gens = self.parent().source().gens()
        for g in gens:
            c = cmp(self._map[g], other._map[g])
            if c: return c
        return 0

    def _add_(self, right):
        return self.__class__(self._map + right._map, self.parent(), construct=True)

    def _lmul_(self, right):
        return self.__class__(self._map * right, self.parent(), construct=True)

    def _rmul_(self, right):
        return self.__class__(self._map * right, self.parent(), construct=True)

    def _sub_(self, right):
        return self.__class__(self._map - right._map, self.parent(), construct=True)

    def plus_part(self):
        r"""
        Returns the plus part of self -- i.e. self + self | [1,0,0,-1].

        Note that we haven't divided by 2.  Is this a problem?

        OUTPUT:

        self + self | [1,0,0,-1]

        EXAMPLES:

        ::

        sage: E = EllipticCurve('11a')
        sage: from sage.modular.pollack_stevens.space import ps_modsym_from_elliptic_curve
        sage: phi = ps_modsym_from_elliptic_curve(E); phi.values()
        [-1/5, 3/2, -1/2]
        sage: (phi.plus_part()+phi.minus_part()) == phi.scale(2)
        True
        """
        return self * minusproj + self

    def minus_part(self):
        r"""
        Returns the minus part of self -- i.e. self - self | [1,0,0,-1]

        Note that we haven't divided by 2.  Is this a problem?

        OUTPUT:

        self - self | [1,0,0,-1]

        EXAMPLES:

        ::

        sage: E = EllipticCurve('11a')
        sage: from sage.modular.pollack_stevens.space import ps_modsym_from_elliptic_curve
        sage: phi = ps_modsym_from_elliptic_curve(E); phi.values()
        [-1/5, 3/2, -1/2]
        sage: (phi.plus_part()+phi.minus_part()) == phi * 2
        True
        """
        return self - self * minusproj

    def hecke(self, ell, algorithm="prep"):
        r"""
        Returns self | `T_{\ell}` by making use of the precomputations in
        self.prep_hecke()

        INPUT:

        - ``ell`` -- a prime

        - ``algorithm`` -- a string, either 'prep' (default) or
          'naive'

        OUTPUT:

        - The image of this element under the hecke operator
          `T_{\ell}`

        ALGORITHMS:

        - If ``algorithm == 'prep'``, precomputes a list of matrices
          that only depend on the level, then uses them to speed up
          the action.

        - If ``algorithm == 'naive'``, just acts by the matrices
          defining the Hecke operator.  That is, it computes
          sum_a self | [1,a,0,ell] + self | [ell,0,0,1],
          the last term occurring only if the level is prime to ell.

        EXAMPLES::

            sage: E = EllipticCurve('11a')
            sage: from sage.modular.pollack_stevens.space import ps_modsym_from_elliptic_curve
            sage: phi = ps_modsym_from_elliptic_curve(E); phi.values()
            [-1/5, 3/2, -1/2]
            sage: phi.hecke(2) == phi * E.ap(2)
            True
            sage: phi.hecke(3) == phi * E.ap(3)
            True
            sage: phi.hecke(5) == phi * E.ap(5)
            True
            sage: phi.hecke(101) == phi * E.ap(101)
            True

            sage: all([phi.hecke(p, algorithm='naive') == phi * E.ap(p) for p in [2,3,5,101]])
            True
        """
        return self.__class__(self._map.hecke(ell, algorithm), self.parent(), construct=True)

    def valuation(self, p):
        r"""
        Returns the valuation of self at `p`.

        Here the valuation if the exponent of the largest power of `p`
        which divides all of the coefficients of all values of self.

        INPUT:

        - ``p`` - prime

        OUTPUT:

        - The valuation of self at `p`

        EXAMPLES:

        ::

        sage: E = EllipticCurve('11a')
        sage: from sage.modular.pollack_stevens.space import ps_modsym_from_elliptic_curve
        sage: phi = ps_modsym_from_elliptic_curve(E)
        sage: phi.values()
        [-1/5, 3/2, -1/2]
        sage: phi.valuation(2)
        -1
        sage: phi.valuation(3)
        0
        sage: phi.valuation(5)
        -1
        sage: phi.valuation(7)
        0
        """
        return min([val.valuation(p) for val in self._map])

    def change_ring(self,R):
        r"""
        Changes the base ring of self to `R`
        """
        pass

    @cached_method
    def is_Tq_eigensymbol(self,q,p=None,M=None):
        r"""
        Determines if self is an eigenvector for `T_q` modulo `p^M`

        INPUT:

        - ``q`` -- prime of the Hecke operator
        - ``p`` -- prime we are working modulo
        - ``M`` -- degree of accuracy of approximation

        OUTPUT:

        - True/False

        EXAMPLES:

        ::

        sage: E = EllipticCurve('11a')
        sage: from sage.modular.pollack_stevens.space import ps_modsym_from_elliptic_curve
        sage: phi = ps_modsym_from_elliptic_curve(E)
        sage: phi.values()
        [-1/5, 3/2, -1/2]
        sage: phi_ord = phi.p_stabilize(p = 3, ap = E.ap(3), M = 10, ordinary = True)
        sage: phi_ord.is_Tq_eigensymbol(2,3,10)
        True
        sage: phi_ord.is_Tq_eigensymbol(2,3,100)
        True
        sage: phi_ord.is_Tq_eigensymbol(2,3,1000)
        True
        sage: phi_ord.is_Tq_eigensymbol(3,3,10)
        True
        sage: phi_ord.is_Tq_eigensymbol(3,3,100)
        False
        """
        try:
            aq = self.Tq_eigenvalue(q, p, M)
            return True
        except ValueError:
            return False
        

    # what happens if a cached method raises an error?  Is it recomputed each time?
    @cached_method
    def Tq_eigenvalue(self, q, p=None, M=None, check=True):
        r"""
        Eigenvalue of `T_q` modulo `p^M`

        INPUT:

        - ``q`` -- prime of the Hecke operator
        - ``p`` -- prime we are working modulo
        - ``M`` -- degree of accuracy of approximation

        OUTPUT:

        - Constant `c` such that `self|T_q - c * self` has valuation greater than
          or equal to `M` (if it exists), otherwise raises ValueError

        EXAMPLES:

        ::

        sage: E = EllipticCurve('11a')
        sage: from sage.modular.pollack_stevens.space import ps_modsym_from_elliptic_curve 
        sage: phi = ps_modsym_from_elliptic_curve(E)
        sage: phi.values()
        [-1/5, 3/2, -1/2]
        sage: phi_ord = phi.p_stabilize(p = 3, ap = E.ap(3), M = 10, ordinary = True)
        sage: phi_ord.Tq_eigenvalue(2,3,10)
        -2
        sage: phi_ord.Tq_eigenvalue(2,3,100)
        -2
        sage: phi_ord.Tq_eigenvalue(2,3,1000)
        -2
        sage: phi_ord.Tq_eigenvalue(3,3,10)
        -2136133753/1068066874
        sage: phi_ord.Tq_eigenvalue(3,3,100)
        ...
        ValueError: not a scalar multiple
        """
        f = self.hecke(q)
        gens = self.parent().source().gens()
        g = gens[0]
        if p is None:
            p = self.parent().prime()
        aq = self._map[g].find_scalar(f._map[g], p, M, check)
        if check:
            if p is None or M is None:
                for g in gens[1:]:
                    if f._map[g] != aq * self._map[g]:
                        raise ValueError("not a scalar multiple")
            elif (f - aq * self).valuation(p) < M:
                raise ValueError("not a scalar multiple")
        return aq
    
    def lift(self, algorithm = None, eigensymbol = None):
        r"""
        """
        raise NotImplementedError

class PSModularSymbolElement_symk(PSModularSymbolElement):
    def p_stabilize(self, p=None, M=None, alpha=None, ap=None, new_base_ring=None, ordinary=True, check=True):
        if check:
            pp = self.parent().prime()
            ppp = (alpha is not None) and alpha.parent().hasattr('prime') and alpha.parent().prime()
            p = ZZ(p) or pp or ppp
            if not p:
                raise ValueError("you must specify a prime")
            if (pp and p != pp) or (ppp and p != ppp):
                raise ValueError("inconsistent prime")
            if M is None:
                M = self.parent().precision_cap()
        k = self.parent().weight()
        if alpha is None:
            if ap is None:
                ap = self.Tq_eigenvalue(p, check=check)
            if check and ap % p == 0:
                raise ValueError("p is not ordinary")
            if new_base_ring is None:
                disc = ap**2 - 4*p**(k+1)
                if M is None:
                    if disc.is_square():
                        new_base_ring = disc.parent()
                    else:
                        poly = PolynomialRing(disc.parent(), 'x')([-disc, 0, 1])
                        new_base_ring = disc.parent().extension(poly, 'a')
                elif p == 2:
                    new_base_ring = Qp(2, M+1)
                else:
                    new_base_ring = Qp(p, M)
            sdisc = new_base_ring(disc).sqrt()
            v0 = (new_base_ring(ap) + sdisc) / 2
            v1 = (new_base_ring(ap) - sdisc) / 2
            if v0.valuation(p) > 0:
                v0, v1 = v1, v0
            if ordinary:
                alpha = v0
            else:
                alpha = v1
        else:
            if new_base_ring is None:
                new_base_ring = alpha.parent()
            if check:
                if ap is None:
                    ap = alpha + p**(k+1)/alpha
                elif alpha**2 - ap * alpha + p**(k+1) != 0:
                    raise ValueError("alpha must be a root of x^2 - a_p*x + p^(k+1)")
                if self.hecke(p) != ap * self:
                    raise ValueError("alpha must be a root of x^2 - a_p*x + p^(k+1)")
        V = self.parent()._p_stabilize_parent_space(p, new_base_ring)
        return self.__class__(self._map.p_stabilize(p, alpha, V), V, construct=True)
    
    def completions(self, p, M):
        r"""
        If `K` is the base_ring of self, this function takes all maps
        `K-->Q_p` and applies them to self return a vector of
        <modular symbol,map: `K-->Q_p`> as map varies over all such maps.

        NOTE: This only returns all completions when `p` splits completely in `K`

        INPUT:
            - ``p`` -- prime
            - ``M`` -- precision

        OUTPUT:

        EXAMPLES:
        """
        K = self.base_ring()
        f = K.defining_polynomial()
        R = pAdicField(p,M+10)['x']
        x = R.gen()
        v = R(f).roots()
        if len(v) == 0:
            raise ValueError, "No coercion possible -- no prime over p has degree 1"
        else:
            roots = [r[0] for r in v]
            ans = []
            for r in root:
                psi = K.hom([root],pAdicField(p,M))
                ans.append([self.map(psi),psi])
            return ans

    def lift(self, p=None, M=None, new_base_ring=None, algorithm = None, eigensymbol = None):
        r"""
        """
        if p is None:
            p = self.parent().prime()
            if p is None:
                raise ValueError("must specify a prime")
        elif self.parent().prime() is not None and p != self.parent().prime():
            raise ValueError("inconsistent prime")
        if M is None:
            M = self.parent().precision_cap() + 1
        if new_base_ring is None:
            if isinstance(self.parent().base_ring(), pAdicGeneric):
                new_base_ring = self.parent().base_ring()
            else:
                # should eventually be a completion
                new_base_ring = Qp(p, M)
        if algorithm is None:
            raise NotImplementedError
        if algorithm == 'stevens':
            if eigensymbol:
                return self._lift_to_OMS_eigen(p, M, new_base_ring)
            else:
                return self._lift_to_OMS(p, M, new_base_ring)
        else:
            return self._lift_greenberg(p, M, new_base_ring)

    def _lift_to_OMS(self, p, M, new_base_ring):
        D = {}
        manin = self.parent().source()
        MSS = self.parent().lift(p, M, new_base_ring)
        half = ZZ(1) / ZZ(2)
        for g in manin.gens()[1:]:
            twotor = g in manin.reps_with_two_torsion
            threetor = g in manin.reps_with_three_torsion
            if twotor:
                # See [PS] section 4.1
                gam = manin.two_torsion[g]
                mu = self._map[g].lift(p, M, new_base_ring)
                D[g] = (mu * gam - mu) * half
            elif threetor:
                # See [PS] section 4.1
                gam = manin.three_torsion[g]
                mu = self._map[g].lift(p, M, new_base_ring)
                D[g] = (2 * mu - mu * gam - mu * (gam**2)) * half
            else:
                # no two or three torsion
                D[g] = self._map[g].lift(p, M, new_base_ring)

        t = self.parent().coefficient_module().lift(p, M, new_base_ring).zero_element()
        for h in manin[2:]:
            R = manin.relations(h)
            if len(R) == 1:
                c, A, g = R[0]
                if c == 1:
                    t += self._map[h].lift(p, M, new_base_ring)
                elif A is not Id:
                    # rules out extra three torsion terms
                    t += c * self._map[g].lift(p, M, new_base_ring) * A
        D[manin.gen(0)] = t.solve_diff_eqn()
        return MSS(D)

class PSModularSymbolElement_dist(PSModularSymbolElement):


    def reduce_precision(self, M):
        r"""
        Only holds on to `M` moments of each value of self
        """
        sd = self._dict
        for val in sd.itervalues():
            val.reduce_precision(M)
        return self

    def precision_absolute(self):
        r"""
        Returns the number of moments of each value of self
        """
        return self.precision_cap()

    def specialize(self):
        r"""
        Returns the underlying classical symbol of weight `k` -- i.e.,
        applies the canonical map `D_k --> Sym^k` to all values of
        self
        """
        sd = self._dict
        for val in sd.itervalues():
            val.specialize()
        return self
