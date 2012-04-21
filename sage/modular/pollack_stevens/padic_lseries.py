from sage.rings.padics.all import pAdicField
from sage.rings.all import ZZ, QQ
from sage.rings.power_series_ring import PowerSeriesRing
from sage.rings.big_oh import O
from sage.rings.arith import binomial, gcd, kronecker

from fund_domain import M2Z

class pAdicLseries(SageObject):
    r"""
    The `p`-adic `L`-series associated to an overconvergent eigensymbol.
    """

    def __init__(self, symb, gamma = None, quad_twist = 1, precision = None):
        r"""

        INPUT:
            - ``symb`` -- overconvergent eigensymbol
            - ``gamma`` -- topological generator of `1 + pZ_p`
            - ``quad_twist`` -- conductor of quadratic twist `\chi`, default 1
            - ``precision`` -- if None is specified, the correct precision bound is computed and the answer is returned modulo
              that accuracy

        """
        if symb.parent().prime() == None:
            raise ValueError ("Not a p-adic overconvergent modular symbol.")

        self._symb = symb

        if gamma == None:
            gamma = 1 + self._symb.parent().prime()

        self._gamma = gamma
        self._quad_twist = quad_twist
        self._precision = precision

    def __getitem__(self, n):
        try:
            return self.series[n]
        except IndexError:
            p = self.prime()
            symb = self.symb()
            ap = symb.ap(p)
            gamma = self._gamma
            precision = self._precision
            S = QQ[['z']]
            z = S.gen()
            M = symb.precision_cap()
            K = pAdicField(p, M)
            dn = 0
            if n == 0:
                precision = M
                lb = [1] + [0 for a in range(M-1)]
            else:
                lb = log_gamma_binomial(p, gamma, z, n, 2*M)
                if precision == None:
                    precision = min([j + lb[j].valuation(p) for j in range(M, len(lb))])
                lb = [lb[a] for a in range(M)]

            for j in range(len(lb)):
                cjn = lb[j]
                temp = sum((ZZ(K.teichmuller(a))**(-j)) * self._basic_integral(a, j) for a in range(1, p))
                dn = dn + cjn*temp
            self.series[n] = dn + O(p**precision)
            return self.series[n]

    def symb(self):
        r"""
        """
        return self._symb

    def prime(self):
        r"""
        """
        return self._symb.parent().prime()

    def quadratic_twist(self)
        r"""
        """
        return self._quad_twist

    def _repr_(self):
        r"""
        Return print representation.
        """
        s = "%s-adic L-series of $s"%(self.prime(), self.symb())
        return s

    def series(self, n, prec):
        r"""
        """
        p = self.prime()
        M = self.symb.precision_cap()
        K = pAdicField(p, M)
        R = PowerSeriesRing(K, 'T', prec)
        T = R(R.gen(), prec)
        return sum(self.series[i] * T**i for i in range(n)) + O(T**n)

    def eval_twisted_symbol_on_Da(self, a): # rename! should this be in modsym?
        """
        Returns `\Phi_{\chi}(\{a/p}-{\infty})` where `Phi` is the OMS and
        `\chi` is a the quadratic character corresponding to self


        INPUT:
            - ``a`` -- integer in [0..p-1]

        OUTPUT:

        The distribution `\Phi_{\chi}(\{a/p\}-\{\infty\})`.

        EXAMPLES:

        """
        symb = self.symb()
        p = symb.parent().prime()
        twisted_dist = symb.parent().zero_element()
        m_map = symb._map
        D = self._quad_twist
        for b in range(1, abs(D) + 1):
            if gcd(b, D) == 1:
                M1 = M2Z([1, b / abs(D), 0, 1])
                new_dist = m_map.__call__(M1 * M2Z[a, 1, p, 0])._rmul_(M1)
                new_dist = new_dist.scale(kronecker(D, b)).normalize()
                twisted_dist = twisted_dist._add(new_dist)
                #ans = ans + self.eval(M1 * M2Z[a, 1, p, 0])._right_action(M1)._lmul_(kronecker(D, b)).normalize()
        return twisted_dist.normalize()

    def _basic_integral(self, a, j):
        r"""
        Returns `\int_{a+pZ_p} (z-{a})^j d\Phi(0-infty)`
        -- see formula [Pollack-Stevens, sec 9.2]

        """
        symb = self.symb()
        M = symb.precision_cap()
        if j > M:
            raise PrecisionError ("Too many moments requested")
        p = self.prime()
        ap = symb.ap(p)
        ap = ap * kronecker(D, p)
        K = Qp(p, M)
        symb_twisted = twisted_symbol_on_Da(symb, a)
        return sum(binomial(j, r) * ((a - ZZ(K.teichmuller(a)))**(j - r)) *
                (p**r) * self.phi_on_Da(a, D).moment(r) for r in range(j + 1)) / ap


def log_gamma_binomial(p,gamma,z,n,M):
    r"""
    Returns the list of coefficients in the power series
    expansion (up to precision `M`) of `{\log_p(z)/\log_p(\gamma) \choose n}`

    INPUT:

        - ``p`` --  prime
        - ``gamma`` -- topological generator e.g., `1+p`
        - ``z`` -- variable
        - ``n`` -- nonnegative integer
        - ``M`` -- precision

    OUTPUT:

    The list of coefficients in the power series expansion of
    `{\log_p(z)/\log_p(\gamma) \choose n}`

    EXAMPLES:

        sage: R.<z> = QQ['z']
        sage: loggam_binom(5,1+5,z,2,4)
        [0, -3/205, 651/84050, -223/42025]
        sage: loggam_binom(5,1+5,z,3,4)
        [0, 2/205, -223/42025, 95228/25845375]
    """
    L = sum([ZZ(-1)**j/j*(gamma-1)**j for j in range (1,M)]) #log_p(1+z)
    loggam = L/(L(gamma-1))                  #log_{gamma}(1+z)= log_p(1+z)/log_p(gamma)
    return z.parent()(binomial(loggam,n)).truncate(M).list()
