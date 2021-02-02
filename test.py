def test_cir_characteristic():
    import numpy as np
    import scipy.stats as st
    import matplotlib.pyplot as plt

    import sys
    sys.path.append('./Processus-Wishart-513/')

    import cir

    k = 0.1
    a = 0.04
    sigma = 2
    T = 1
    x0 = 0.3
    num = 100000
    print(f'sigma^2 <= 4a is {sigma * sigma <= 4 * a}.')
    cir_gen = cir.CIR(k, a, sigma, x0=x0)
    cir_gen.character(T=T, v=-1)
    lst_N = np.array([1, 2, 4, 8, 16, 32, 48, 64])
    xT_exact = cir_gen(T=T, n=1, num=num)[:, -1]  # The exact generated XT.
    char_exact = np.mean(np.exp(-1 * xT_exact))
    char_real = cir_gen.character(T=T, v=-1)
    char_2_n = np.zeros(len(lst_N))
    char_3_n = np.zeros(len(lst_N))
    char_ext_n = np.zeros(len(lst_N))
    confiance_ext = np.zeros((len(lst_N), 2))
    confiance_2 = np.zeros((len(lst_N), 2))
    confiance_3 = np.zeros((len(lst_N), 2))

    for i in range(len(lst_N)):
        xT_2 = cir_gen(T=T, n=lst_N[i], num=num, method='2')[:, -1]
        char_2 = np.mean(np.exp(-1 * xT_2))
        sub, top = st.t.interval(0.95, len(lst_N) - 1, loc=char_2, scale=st.sem(np.exp(-1 * xT_2)))
        confiance_2[i] = np.array([sub, top])
        del xT_2
        xT_3 = cir_gen(T=T, n=lst_N[i], num=num, method='3')[:, -1]
        char_3 = np.mean(np.exp(-1 * xT_3))
        sub, top = st.t.interval(0.95, len(lst_N) - 1, loc=char_3, scale=st.sem(np.exp(-1 * xT_3)))
        confiance_3[i] = np.array([sub, top])
        del xT_3
        xT_ext = cir_gen(T=T, n=lst_N[i], num=num, method='exact')[:, -1]
        char_ext = np.mean(np.exp(-1 * xT_ext))
        sub, top = st.t.interval(0.95, len(lst_N) - 1, loc=char_ext, scale=st.sem(np.exp(-1 * xT_ext)))
        confiance_ext[i] = np.array([sub, top])
        del xT_ext
        char_2_n[i] = char_2
        char_3_n[i] = char_3
        char_ext_n[i] = char_ext

    plt.axhline(y=char_real, color='r', label='real')

    plt.plot(np.log(1 / lst_N), char_2_n, color='b', label='2')
    plt.plot(np.log(1 / lst_N), char_3_n, color='orange', label='3')
    plt.plot(np.log(1 / lst_N), char_ext_n, color='g', label='exact_n')
    plt.fill_between(np.log(1 / lst_N), confiance_2[:, 0], confiance_2[:, 1], color='b', alpha=0.2)
    plt.fill_between(np.log(1 / lst_N), confiance_3[:, 0], confiance_3[:, 1], color='orange', alpha=0.2)
    plt.fill_between(np.log(1 / lst_N), confiance_ext[:, 0], confiance_ext[:, 1], color='g', alpha=0.2)
    # plt.plot(lst_N, char_3_n_d, color='y', label='3, original')
    plt.xlabel("log(1/n)")
    plt.legend()
    plt.show()


def test_wishart_processus():
    import numpy as np
    import matplotlib.pyplot as plt

    from wishart.simulation import Wishart

    x = np.array([[1, 1], [1, 2]])
    b = np.array([[1, 0], [0, 0]])
    a = np.array([[2, -1], [2, 1]])
    w = Wishart(x, 3, a, b)
    t = 1
    N = 30

    proc = w(t, N, x, b, a)
    interval = range(N + 1)

    plt.plot(interval, proc[0, :, 0, 0], label="[0,0]")
    plt.plot(interval, proc[0, :, 0, 1], label="[0,1]")
    plt.plot(interval, proc[0, :, 1, 1], label="[1,1]")
    plt.plot(interval, proc[0, :, 1, 0], label="[1,0]")
    plt.title('wishart')
    plt.legend()
    plt.show()

    proc2 = w.wishart_i(t, N, 1, x)
    interval = range(N + 1)

    plt.plot(interval, proc2[0, :, 0, 0], label="[0,0]")
    plt.plot(interval, proc2[0, :, 0, 1], label="[0,1]")
    plt.plot(interval, proc2[0, :, 1, 1], label="[1,1]")
    plt.plot(interval, proc2[0, :, 1, 0], label="[1,0]")
    plt.title('wishart i')
    plt.legend()
    plt.show()


def test_wishart_characteristic():
    import numpy as np
    import scipy.stats as st
    import matplotlib.pyplot as plt
    from tqdm import tqdm

    import sys
    sys.path.append('./Processus-Wishart-513/')

    import wishart

    def char_MC_N(gen, T, v, x=None, lst_N=[1], num=500, method='exact', is_cf=False, **kwargs):
        lst_char = []
        confiance = np.zeros((len(lst_N), 2))

        for i, N in enumerate(tqdm(lst_N)):
            XT = gen(T=T, N=N, num=num, x=x, method=method, num_int=5000, **kwargs) # of shape (num, d, d).
            tmp = np.matmul(v, XT)
            exp_trace = np.exp(np.trace(tmp, axis1=1, axis2=2))
            char = np.mean(exp_trace)
            lst_char.append(char)
            if is_cf:
                sub, top = st.t.interval(0.95, len(lst_N) - 1, loc=np.real(char), scale=st.sem(np.real(exp_trace)))
                confiance[i] = np.array([sub, top])
        if is_cf:
            return np.array(lst_char), confiance
        else:
            return np.array(lst_char)

    T = 10

    x = 0.4 * np.eye(3)
    a = np.eye(3)
    b = np.zeros((3, 3))
    alpha = 4.5

    num = 10000
    lst_N = np.array([1, 2, 4, 8, 16, 32, 48, 64])

    v = np.eye(3) * 0.05 * 1j

    lst_v = np.array([v])
    w_gen = wishart.Wishart(x, alpha, b=b, a=a)
    char_true = w_gen.character(T=T, v=lst_v, num_int=5000)[0]
    print(f'True value is {char_true}.')
    print('Calculating exact...')
    char_exact_N, cf_ext = char_MC_N(w_gen, T=T, v=v, lst_N=lst_N, num=num, is_cf=True, method='exact')
    print('Calculating 2nd order scheme...')
    char_2, cf_2 = char_MC_N(w_gen, T=T, v=v, lst_N=lst_N, num=num, is_cf=True, method='2')
    print('Calculating 3rd order scheme...')
    char_3, cf_3 = char_MC_N(w_gen, T=T, v=v, lst_N=lst_N, num=num, is_cf=True, method='3')
    print('Calculating euler scheme...')
    char_e, cf_ext = char_MC_N(w_gen, T=T, v=v, lst_N=lst_N, num=num, is_cf=True, method='euler')

    plt.axhline(y=np.real(char_true), color='r', label='True value')
    # plt.axhline(y=np.abs(char_exact), label='exact', alpha=.8, color='y')
    plt.plot(np.log(1/lst_N), np.real(char_2), label='2', color='b', alpha=.8)
    plt.plot(np.log(1/lst_N), np.real(char_3), label='3', color='orange', alpha=.8)
    plt.plot(np.log(1/lst_N), np.real(char_exact_N), label='exact', color='g', alpha=.8)
    plt.fill_between(np.log(1 / lst_N), cf_2[:, 0], cf_2[:, 1], color='b', alpha=0.2)
    plt.fill_between(np.log(1 / lst_N), cf_3[:, 0], cf_3[:, 1], color='orange', alpha=0.2)
    plt.fill_between(np.log(1 / lst_N), cf_ext[:, 0], cf_ext[:, 1], color='g', alpha=0.2)
    # plt.plot(lst_N, np.real(char_e), label='euler', alpha=.8)
    plt.legend()
    plt.xlabel('log(1/N)')
    plt.title('Convergence of Wishart simulation methods')
    # plt.savefig('./wishart_cov.png')
    plt.show()


def test_cholesky():
    import numpy as np
    from wishart import utils

    a = np.array([[1,2,3],[2,5,6],[3,6,9]])
    c, k, p, r = utils.decompose_cholesky(a)
    print(c)
    print(k)
    print(p)
    print(r)
    b = np.zeros(a.shape)
    b[:r, :r] = c
    b[r:, :r] = k
    print(a)
    print(p.T.dot(b.dot(b.T)).dot(p))


def test_gs():
    import numpy as np
    import scipy.stats as st
    import matplotlib.pyplot as plt
    from tqdm import tqdm

    import sys
    sys.path.append('..')

    from application import GS_model

    def price_mc(model, num, r, T, K, N, method):
        S, X = model(num=num, N=N, T=T, ret_vol=True, method=method, num_int=5000)
        ST = S[:, -1]
        ST_M = np.max(ST, axis=1)
        prix = (K-ST_M).clip(0) * np.exp(-r*T)
        prix_mean = prix.mean()
        sub, top = st.t.interval(0.95, len(lst_N) - 1, loc=prix_mean, scale=st.sem(prix))
        confiance = np.array([sub, top])

        return prix_mean, confiance

    S0 = np.array([100, 100])
    r = .02
    X0 = np.array([[.04, .02], [.02, .04]])
    alpha = 4.5
    a = np.eye(2) * 0.2
    b = np.eye(2) * 0.5
    T = 1
    K = 120
    num = 100000
    lst_N = np.array([1, 2, 4, 8, 16, 32, 64])

    model = GS_model(S0, r, X0, alpha, a=a, b=b)
    lst_prix_2 = np.zeros_like(lst_N, dtype=float)
    lst_prix_e = np.zeros_like(lst_N, dtype=float)

    it_lst = tqdm(range(len(lst_N)))
    cf_2 = np.zeros((len(lst_N), 2))
    cf_euler = np.zeros((len(lst_N), 2))

    for i in it_lst:
        N = lst_N[i]
        it_lst.set_postfix({'calculating': 'scheme 2...'})
        prix, cf_2[i] = price_mc(model, num=num, T=T, K=K, N=N, r=r, method='2')
        lst_prix_2[i] = prix
        it_lst.set_postfix({'calculating': 'scheme euler...'})
        prix, cf_euler[i] = price_mc(model, num=num, T=T, K=K, N=N, r=r, method='euler')
        lst_prix_e[i] = prix

    plt.plot(np.log(1/lst_N), lst_prix_2, color='b', label='2')
    plt.fill_between(np.log(1 / lst_N), cf_2[:, 0], cf_2[:, 1], color='b', alpha=0.2)
    plt.plot(np.log(1/lst_N), lst_prix_e, color='g', label='euler')
    plt.fill_between(np.log(1 / lst_N), cf_euler[:, 0], cf_euler[:, 1], color='g', alpha=0.2)
    # plt.plot(lst_N, lst_prix_e, label='euler')
    plt.xlabel('log(1/N)')
    plt.title('Convergence of Sufana model simulation')
    plt.legend()
    plt.show()
