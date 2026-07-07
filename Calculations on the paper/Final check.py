import numpy as np
import csv
from scipy.optimize import minimize
from Formulas import *

def objective_for_minimizer(params):

    ceiling_values = [1e5]
    floor_values = [0]
    Epsilon = 0.25
    zeta, delta, omega, k, tau, eta = params

    A_Cond = least_L_for_A_exp(Zeta=zeta,Delta=delta,Omega=omega,Tau=tau,Eta=eta,K=k)
    floor_values.append(A_Cond)
    H_Cond = least_L_for_H_exp(Zeta=zeta,Delta=delta,Omega=omega,Tau=tau)
    floor_values.append(H_Cond)

    Exp_for_E = L_for_eps_delta(Zeta=zeta,Delta=delta)

    linear_term_E_positive = 3 * Epsilon + 4 * zeta * (delta - Epsilon) - 2 * delta > 0
    if linear_term_E_positive:
        ceiling_values.append(Exp_for_E)
    else:
        floor_values.append(Exp_for_E)

    Exp_for_M = largest_M_for_Tx(Zeta=zeta,K=k,Tau=tau,Eta=eta,threshold_M=-0.7)
    ceiling_values.append(Exp_for_M)

    Zeta_req = smallest_L_for_zeta_req(Zeta=zeta,Tau=tau)
    floor_values.append(Zeta_req)

    L_min = max(floor_values)
    L_max = min(ceiling_values)

    if 2*(bound_on_Dx(L_min, zeta, omega,tau) + bound_on_Fx(L_min,zeta)) < 0.9999-2/np.exp(0.7):
        print("This works")

    if L_max >= L_min:
        return L_min
    #rest is to identify which conditions is not satisfied, each with their own first digit
    elif H_Cond > L_max:
        return 2e4
    elif Exp_for_M < L_min:
        return 3e4
    elif Zeta_req > L_max:
        return 4e4
    elif Exp_for_E < L_min and linear_term_E_positive:
        return 5e4
    elif Exp_for_E > L_max and not linear_term_E_positive:
        return 6e4
    elif A_Cond > L_max:
        return 1e4

bounds = [
    (0.75, 0.9999),  # zeta: 0.8 < zeta < 1
    #(0.0001, 0.25),  # epsilon: typically small positive
    (0.0001,0.25), #delta: small positive
    # (1e-12, 0.1),  # gamma: 0 < gamma < epsilon**4 / 4
    (0.5001, 10.0),  # omega: typically > 1
    (0.001, 50000.0),  # k: k > e
    (0.45,0.99999), # tau: 0.5=< tau < 1
    (0,1), #eta <= 1
    # (-5,-0.00001)#Threshold:M
]
# Initial guess (starting point for the optimizer)
ZETA= 8.00910096854779096631e-01
DELTA = 4.347352393477172e-02
OMEGA= 1.010128830661306
k_param=34.444716156662267
TAU=0.506132565901298
ETA=1.156966084055313e-01
x0 = [ZETA, DELTA, OMEGA, k_param, TAU, ETA]
# x0 = [ZETA, DELTA, OMEGA, k_param, TAU, THRESHOLD_M]

# We use COBYLA or Nelder-Mead because your function is likely not differentiable
res = minimize(objective_for_minimizer,x0,method='Nelder-Mead',bounds=bounds,options={'maxiter': 5000, 'disp': True})

print_parameters(res.x)

# objective_for_minimizer(x0)

print(15*256)



