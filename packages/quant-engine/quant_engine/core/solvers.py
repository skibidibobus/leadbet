"""Robust numerical root-finding algorithms for probability devigging."""
from __future__ import annotations

from typing import Callable

try:
    from scipy.optimize import brentq as scipy_brentq
    _HAS_SCIPY = True
except ImportError:
    _HAS_SCIPY = False


def brentq_pure(
    f: Callable[[float], float],
    a: float,
    b: float,
    xtol: float = 1e-12,
    rtol: float = 1e-12,
    maxiter: int = 100,
) -> float:
    """Pure-Python implementation of Brent's method (Dekker-Brent algorithm).

    Guarantees quadratic or superlinear convergence without external C-extensions.
    """
    fa = f(a)
    fb = f(b)
    if fa * fb > 0:
        raise ValueError(f"Root is not bracketed: f({a})={fa}, f({b})={fb}")
    if abs(fa) < abs(fb):
        a, b = b, a
        fa, fb = fb, fa

    c = a
    fc = fa
    mflag = True
    d = 0.0

    for _ in range(maxiter):
        if abs(fb) < 1e-15 or abs(b - a) < (2.0 * rtol * abs(b) + xtol):
            return b

        if fa != fc and fb != fc:
            # Inverse quadratic interpolation
            s = (
                (a * fb * fc) / ((fa - fb) * (fa - fc))
                + (b * fa * fc) / ((fb - fa) * (fb - fc))
                + (c * fa * fb) / ((fc - fa) * (fc - fb))
            )
        else:
            # Secant method
            s = b - fb * (b - a) / (fb - fa)

        cond1 = not ((3 * a + b) / 4 <= s <= b or b <= s <= (3 * a + b) / 4)
        cond2 = mflag and abs(s - b) >= abs(b - c) / 2
        cond3 = not mflag and abs(s - b) >= abs(c - d) / 2
        cond4 = mflag and abs(b - c) < xtol
        cond5 = not mflag and abs(c - d) < xtol

        if cond1 or cond2 or cond3 or cond4 or cond5:
            # Bisection fallback
            s = (a + b) / 2
            mflag = True
        else:
            mflag = False

        fs = f(s)
        d = c
        c = b
        fc = fb

        if fa * fs < 0:
            b = s
            fb = fs
        else:
            a = s
            fa = fs

        if abs(fa) < abs(fb):
            a, b = b, a
            fa, fb = fb, fa

    return b


def find_root_brent(
    f: Callable[[float], float],
    a: float,
    b: float,
    xtol: float = 1e-12,
    rtol: float = 1e-12,
    maxiter: int = 100,
) -> float:
    """Brent root-finder utilizing scipy when available, falling back to pure Python."""
    if _HAS_SCIPY:
        try:
            return float(scipy_brentq(f, a, b, xtol=xtol, rtol=rtol, maxiter=maxiter))
        except Exception:
            return brentq_pure(f, a, b, xtol=xtol, rtol=rtol, maxiter=maxiter)
    return brentq_pure(f, a, b, xtol=xtol, rtol=rtol, maxiter=maxiter)
