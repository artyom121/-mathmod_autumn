import numpy as np
import scipy
from scipy.special import expit


class BaseSmoothOracle(object):
    """
    Base class for implementation of oracles.
    """
    def func(self, x):
        """
        Computes the value of function at point x.
        """
        raise NotImplementedError('Func oracle is not implemented.')

    def grad(self, x):
        """
        Computes the gradient at point x.
        """
        raise NotImplementedError('Grad oracle is not implemented.')
    
    def hess(self, x):
        """
        Computes the Hessian matrix at point x.
        """
        raise NotImplementedError('Hessian oracle is not implemented.')
    
    def func_directional(self, x, d, alpha):
        """
        Computes phi(alpha) = f(x + alpha*d).
        """
        return np.squeeze(self.func(x + alpha * d))

    def grad_directional(self, x, d, alpha):
        """
        Computes phi'(alpha) = (f(x + alpha*d))'_{alpha}
        """
        return np.squeeze(self.grad(x + alpha * d).dot(d))


class QuadraticOracle(BaseSmoothOracle):
    """
    Oracle for quadratic function:
       func(x) = 1/2 x^TAx - b^Tx.
    """

    def __init__(self, A, b):
        if not scipy.sparse.isspmatrix_dia(A) and not np.allclose(A, A.T):
            raise ValueError('A should be a symmetric matrix.')
        self.A = A
        self.b = b

    def func(self, x):
        return 0.5 * np.dot(self.A.dot(x), x) - self.b.dot(x)

    def grad(self, x):
        return self.A.dot(x) - self.b

    def hess(self, x):
        return self.A 


class LogRegL2Oracle(BaseSmoothOracle):
    """
    Oracle for logistic regression with l2 regularization:
         func(x) = 1/m sum_i log(1 + exp(-b_i * a_i^T x)) + regcoef / 2 ||x||_2^2.

    Let A and b be parameters of the logistic regression (feature matrix
    and labels vector respectively).
    For user-friendly interface use create_log_reg_oracle()

    Parameters
    ----------
        matvec_Ax : function
            Computes matrix-vector product Ax, where x is a vector of size n.
        matvec_ATx : function of x
            Computes matrix-vector product A^Tx, where x is a vector of size m.
        matmat_ATsA : function
            Computes matrix-matrix-matrix product A^T * Diag(s) * A,
    """
    def __init__(self, matvec_Ax, matvec_ATx, matmat_ATsA, b, regcoef):
        self.matvec_Ax = matvec_Ax
        self.matvec_ATx = matvec_ATx
        self.matmat_ATsA = matmat_ATsA
        self.b = b
        self.regcoef = regcoef

    def func(self, x):
        Ax = self.matvec_Ax(x)
        return (np.mean(np.logaddexp(0, -self.b * Ax)) + 
                0.5 * self.regcoef * np.linalg.norm(x)**2)

    def grad(self, x):
        Ax = self.matvec_Ax(x)
        sigma = scipy.special.expit(self.b * Ax)
        return (self.matvec_ATx((sigma - 1) * self.b) / len(self.b) + 
                self.regcoef * x)

    def hess(self, x):
        Ax = self.matvec_Ax(x)
        sigma = scipy.special.expit(self.b * Ax)
        S = sigma * (1 - sigma)
        return self.matmat_ATsA(S) / len(self.b) + self.regcoef * np.eye(len(x))


class LogRegL2OptimizedOracle(LogRegL2Oracle):
    """
    Oracle for logistic regression with l2 regularization
    with optimized *_directional methods (are used in line_search).

    For explanation see LogRegL2Oracle.
    """
    def __init__(self, matvec_Ax, matvec_ATx, matmat_ATsA, b, regcoef):
        super().__init__(matvec_Ax, matvec_ATx, matmat_ATsA, b, regcoef)

    def func_directional(self, x, d, alpha):
        # TODO: Implement optimized version with pre-computation of Ax and Ad
        return None

    def grad_directional(self, x, d, alpha):
        # TODO: Implement optimized version with pre-computation of Ax and Ad
        return None


def create_log_reg_oracle(A, b, regcoef, oracle_type='usual'):
    """
    Auxiliary function for creating logistic regression oracles.
        `oracle_type` must be either 'usual' or 'optimized'
    """
    if scipy.sparse.issparse(A):
        matvec_Ax = lambda x: A.dot(x)
        matvec_ATx = lambda x: A.T.dot(x)
        matmat_ATsA = lambda s: A.T.dot(scipy.sparse.diags(s).dot(A))
    else:
        matvec_Ax = lambda x: A @ x
        matvec_ATx = lambda x: A.T @ x
        matmat_ATsA = lambda s: A.T @ (np.diag(s) @ A)

    if oracle_type == 'usual':
        return LogRegL2Oracle(matvec_Ax, matvec_ATx, matmat_ATsA, b, regcoef)
    elif oracle_type == 'optimized':
        return LogRegL2OptimizedOracle(matvec_Ax, matvec_ATx, matmat_ATsA, b, regcoef)
    else:
        raise ValueError(f"Unknown oracle_type={oracle_type}")



def grad_finite_diff(func, x, eps=1e-8):
    """
    Returns approximation of the gradient using finite differences:
        result_i := (f(x + eps * e_i) - f(x)) / eps,
        where e_i are coordinate vectors:
        e_i = (0, 0, ..., 0, 1, 0, ..., 0)
                          >> i <<
    """
    grad = np.zeros_like(x)
    for i in range(len(x)):
        e_i = np.zeros_like(x)
        e_i[i] = 1
        grad[i] = (func(x + eps * e_i) - func(x)) / eps
    return grad


def hess_finite_diff(func, x, eps=1e-5):
    """
    Returns approximation of the Hessian using finite differences:
        result_{ij} := (f(x + eps * e_i + eps * e_j)
                               - f(x + eps * e_i) 
                               - f(x + eps * e_j)
                               + f(x)) / eps^2,
        where e_i are coordinate vectors:
        e_i = (0, 0, ..., 0, 1, 0, ..., 0)
                          >> i <<
    """
    n = len(x)
    hess = np.zeros((n, n))
    for i in range(n):
        for j in range(i, n):
            e_i = np.zeros_like(x)
            e_j = np.zeros_like(x)
            e_i[i] = 1
            e_j[j] = 1
            f_x_ei_ej = func(x + eps * e_i + eps * e_j)
            f_x_ei = func(x + eps * e_i)
            f_x_ej = func(x + eps * e_j)
            f_x = func(x)
            hess[i, j] = hess[j, i] = (f_x_ei_ej - f_x_ei - f_x_ej + f_x) / eps**2
    return hess