import scipy.linalg
import numpy as np

from wishart import utils
from wishart import Wishart_e
import cir
from application.elgm import ELGM

class Fonseca_model:
    '''
    dY_t = (r - 1/2 * diag(X_t))dt + \sqrt(Xt)(\bar{\rho} dB_t + dW_t^T\rho),
    dX_t = (\alpha + bX_t + X_t^b^T)dt + \sqrt(X_t)dW_ta + a^T (dW_t)^T \sqrt(X_t).
    Where \alpha = \bar{\alpha} * a^Ta, for \bar{\alpha} > d-1.
    '''
    def __init__(self, r, rho, coef, b, a):
        '''
        * Params:
            r, real-number. The interest rate.
            rho, np.array, of shape (d,). The correlation vector.
            b, np.array, of shape (d, d).
            a, np.array, of shape (d, d). 
        '''
        d = len(rho)
        assert b.shape==(d, d) and a.shape==(d, d)
        assert rho.shape == (d,)
        self.r = r
        self.d = d
        self.rho = rho
        self.bar_rho = np.sqrt(1 - np.linalg.norm(rho))
        self.alpha = coef * (a.T @ a)
        self.bar_alpha = coef
        self.b = b
        self.a = a
        
        self.init_elgm()
        
    def init_elgm(self):
        '''
        This function calculates the parameters of elgm, and initialise the
        elgm instance.
        '''
        # Calculate I_d^n, u, b_u, and delta.
        aTa = self.a.T @ self.a
        c, k, p, n = utils.decompose_cholesky(aTa)
        self.n = n # n used in I_d^n.
        # Build uT.
        uT = np.eye(self.d)
        uT[:n, :n] = c
        uT[n:, :n] = k
        uT = np.matmul(np.linalg.inv(p), uT)
        self.u = uT.T # u, where x = u^T z u.
        self.inv_u = np.linalg.inv(self.u) # inverse of u.
        tmp_Idn = np.zeros(self.d)
        tmp_Idn[:n] = 1
        tmp_Idn = np.diag(tmp_Idn)
        delta = self.bar_alpha * tmp_Idn
        bu = np.matmul(self.inv_u.T, np.matmul(self.b, self.u.T)) # bu = (u^T)^-1 b u^T
        self.elgm_gen = ELGM(rho=self.rho, alpha=delta, b=bu, n=n)
        
    
    def gen(self, x, y, T, N=1, num=1, comb='r', **kwargs):
        '''
        This function generates `num` independent samples with end time `T` and
        separated to `N` pieces.
        '''
        assert x.shape == (self.d, self.d)
        assert y.shape == (self.d,)
        dt = T/N
        # Initialise the elgm generator.
        self.elgm_gen.pre_gen(T=T, N=N, num=num, comb=comb, **kwargs)
        
        # Generate
        lst_trace_Xt = np.zeros((num, N+1, self.d, self.d))
        lst_trace_Yt = np.zeros((num, N+1, self.d))
        lst_trace_Xt[:, 0] = x
        lst_trace_Yt[:, 0] = y
        
        lst_it = range(num)
        if 'tqdm' in kwargs:
            lst_it = kwargs['tqdm'](lst_it)
            
        for i in lst_it:
            for j in range(1, N+1):
                x = lst_trace_Xt[i, j-1]
                y = lst_trace_Yt[i, j-1]
                Xt, Yt = self.step(x=x, y=y, dt=dt, comb=comb)
                lst_trace_Xt[i, j] = Xt
                lst_trace_Yt[i, j] = Yt

        if 'trace' in kwargs and not kwargs['trace']:
            return lst_trace_Xt[:, -1], lst_trace_Yt[:, -1]
        else:
            return lst_trace_Xt, lst_trace_Yt
        
    def step(self, x, y, dt, dBt=None, comb='r'):
        '''
        Remark: Before calling this function, the `self.elgm_gen` must be 
        initilised by calling its `pre_gen` function. If not, step_L_tilde will
        definitely fail.
        '''
        Xt = x
        Yt = y
        if comb == 'euler':
            Xt, Yt = self.step_euler(x=Xt, y=Yt, dt=dt, dBt=dBt)
            return Xt, Yt
        elif comb=='r' or comb=='2' or comb==2:
            zeta = np.random.rand()
            if zeta < .5:
                Xt, Yt = self.step_L_1(x=Xt, y=Yt, dt=dt, dBt=dBt)
                Xt, Yt = self.step_L_tilde(x=Xt, y=Yt, dt=dt, comb=comb)
            else:
                Xt, Yt = self.step_L_tilde(x=Xt, y=Yt, dt=dt, comb=comb)
                Xt, Yt = self.step_L_1(x=Xt, y=Yt, dt=dt, dBt=dBt)
            return Xt, Yt
        elif comb=='1' or comb==1:
            if dBt is None:
                dBt = np.random.normal(size=(2, self.d)) * np.sqrt(dt/2)
            else:
                dBt = np.array(dBt)
                if dBt.shape != (2, self.d): # If dBt is of shape (d, d).
                    assert dBt.shape == (self.d,)
                    # Use the Brownian Bridge.
                    dBt_0 = dBt/2  + np.random.normal(size=(self.d)) * np.sqrt(dt/4)
                    dBt_1 = dBt - dBt_0
                    dBt = np.array([dBt_0, dBt_1])
            Xt, Yt = self.step_L_1(x=Xt, y=Yt, dt=dt/2, dBt = dBt[0])
            Xt, Yt = self.step_L_tilde(x=Xt, y=Yt, dt=dt, comb=comb)
            Xt, Yt = self.step_L_1(x=Xt, y=Yt, dt=dt/2, dBt = dBt[1])
            return Xt, Yt

    def step_euler(self, x, y, dt, dBt=None):
        if dBt is None:
            dBt = np.random.normal(size=(self.d)) * np.sqrt(dt)
        dWt = np.random.normal(size=(self.d, self.d)) * np.sqrt(dt)

        sqrt_x = utils.cholesky(x)
        Yt = y + (self.r - 1/2*np.diag(x))*dt + np.matmul(sqrt_x*self.bar_rho, dBt) + dWt.dot(self.rho)
        Xt = (self.alpha + np.matmul(self.b, x) + np.matmul(x, self.b))*dt + \
             np.matmul(np.matmul(sqrt_x, dWt), self.a) + \
             np.matmul(self.a.T, np.matmul(dWt.T, sqrt_x))

        return Xt, Yt

    def step_L_1(self, x, y, dt, dBt=None):
        '''
        dYt = (r = diag(x)/2)dt + \bar{\rho}\sqrt(x)dBt.
        '''
        if dBt is None:
            dBt = np.random.normal(size=(self.d)) * np.sqrt(dt)
        c = utils.cholesky(x)
        Yt = y + (self.r - np.diag(x)/2)*dt + self.bar_rho * (c @ dBt)
        Xt = x
        return Xt, Yt
    
    def step_L_tilde(self, x, y, dt, comb='r'):
        r = np.matmul(self.inv_u.T, y)
        v = np.matmul(self.inv_u.T, np.matmul(x, self.inv_u))
        
        Vt, Rt = self.elgm_gen.step(x=v, y=r, dt=dt, comb=comb)
        Yt = np.matmul(self.u.T, Rt)
        Xt = np.matmul(self.u.T, np.matmul(Vt, self.u))
        return Xt, Yt

    def character(self, Gamma, Lambda, Xt, Yt):
        return (np.exp(-1j * (np.trace(np.matmul(Gamma, Xt), axis1=1, axis2=2) + np.matmul(Yt, Lambda)))).mean()
        