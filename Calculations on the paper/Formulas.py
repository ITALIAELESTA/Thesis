import numpy as np

pi = np.pi
floor_search =  0
ceiling_search = 350
threshold = -1e-60
tol = 1e-9


def bound_on_Dx(value, Zeta, Omega, Tau):
    m = np.exp(Zeta*value)
    return m * np.exp(-np.power(m, 1 - Tau) / (3 * (Zeta*value)** Omega))


def bound_on_Fx(value, Zeta): #value is log n
    return np.exp(-np.exp(value * (1 - Zeta))  / 4 + value*Zeta) #this last term is m = n^\zeta


def binary_entropy(p):
    if p <= 0 or p >= 1:
        return 0.0
    # np.log2 works on floats; if using arrays, use np.log2
    return -(p * np.log(p) + (1 - p) * np.log(1 - p))



def C_epsilon(Epsilon): #H(ε) + H(ε')(1-ε) + ˜ε log ˜ε − ˜ε
    Epsilon_prime = Epsilon/(1-Epsilon)
    return binary_entropy(Epsilon) + binary_entropy(Epsilon_prime)*(1-Epsilon) + Epsilon*np.log(Epsilon) - Epsilon

def L_for_eps_delta(Delta,Zeta,high=ceiling_search,low=0):

    Epsilon = 0.25
    Epsilon_prime = Epsilon / (1 - Epsilon)
    L_term = 3 * Epsilon + 4 * Zeta * (Delta - Epsilon) - 2 * Delta
    # print(L_term)
    feasible_on_left = L_term >0
    # print(feasible_on_left)
    # linear term is 3ε + 4ζ(δ − ε) -2δ
    log_alpha = Delta * np.log(3 / 2) + (Epsilon - Delta) * np.log(3 * Delta)
    constant_term = 2 * Delta + 2 * log_alpha + C_epsilon(Epsilon)

    # print(constant_term)
    # C = 2πδc = (2π)^3/2 δε sqrt[(1 − ε)(1 − ε′)].
    C = np.pow(2 * pi, 3 / 2) * Delta * Epsilon * np.sqrt((1 - Epsilon) * (1 - Epsilon_prime))
     # + 1/(12*Epsilon)*np.exp(-2*value)
    # this result is then multiplied by n, and exponentiated, so value becomes negligible
    # print(L_term,constant_term,exp_term,result)


    while (high - low) > tol:
        mid = (low + high) / 2
        exp_term = -3 * mid / 2 - np.log(C)
        result = constant_term + mid * L_term + np.exp(-mid) * exp_term


        feasible = result < threshold

        if feasible:
            best_L = mid
            if feasible_on_left:
                low = mid  # Feasible! Let's push higher to find the *largest* valid L
            else:
                high = mid  # Feasible! Let's push lower to find the *least* valid L
        else:
            if feasible_on_left:
                high = mid  # Not feasible (too high), look lower
            else:
                low = mid  # Not feasible (too low), look higher

    try:
        return best_L
    except NameError:
        return 2e9


def least_L_for_A_exp(Zeta, Delta,  Omega, Tau, K, Eta,Epsilon=0.25,high=ceiling_search,low=floor_search):
    C_k = 2 * np.exp(2) * (4 * K + 2) * (2 * K + 1)  # + 2*np.exp(2)
    # C_k = 2*np.exp(2)*(4*K)*(2*K)
    # coupled with e^L
    # term1_prime = Gamma/(C_k*np.power(M1,2*Tau)*np.power(log_M,2*Eta+2*Omega)) * np.power(1-1/log_M**Omega,4*K*log_M**Eta)
    Term2 = C_epsilon(Epsilon)
    # constant term

    # c=ε sqrt[2π(1 − ε)(1 − ε′)].
    Epsilon_prime = Epsilon / (1 - Epsilon)
    c = Epsilon * np.sqrt(2 * pi * (1 - Epsilon) * (1 - Epsilon_prime))
    # coupled with e^-L
    Term4 = Epsilon
    # coupled with L


    while (high - low) > tol:
        L = (low + high) / 2


        log_M = Zeta * L
        M = np.exp(log_M)

        Gamma = Delta ** 2 / 4 - Delta / (4 * np.exp(L)) - 16 * np.power(M, 1 - 2 * Tau) / np.power(log_M, 2 * Omega)
        log_M_omega = np.power(log_M, -Omega)
        Term1 = Gamma / (C_k * np.power(M, 2 * Tau) * np.power(log_M, 2 * Eta)) * np.log(
            1 - log_M_omega ** 2 * np.power(1 - log_M_omega, 4 * K * log_M ** Eta))
        Term3 = -L / 2 - np.log(c)


        feasible = Term1*np.exp(L) +Term2+Term3*np.exp(-L)+ Term4*L < threshold
        # print(Term1,Term2,Term3,Term4)
        if feasible:
            # print(f"Passes here")
            best_L = L
            high = L  # Try to find a smaller L in the lower half
        else:
            low = L  # Need a larger L, look in the upper half

    try:
        return best_L
    except NameError:
        return 3e9


def least_L_for_H_exp(Zeta, Delta,Omega, Tau, Epsilon=0.25,high=ceiling_search,low=floor_search):
    # C_k = 2 * np.exp(2) * (4 * K + 2) * (2 * K + 1)  # + 2*np.exp(2)
    # C_k = 2*np.exp(2)*(4*K)*(2*K)

    # coupled with e^L
    # term1_prime = Gamma/(C_k*np.power(M1,2*Tau)*np.power(log_M,2*Eta+2*Omega)) * np.power(1-1/log_M**Omega,4*K*log_M**Eta)
    Term2 = C_epsilon(Epsilon)
    # constant term

    # c=ε sqrt[2π(1 − ε)(1 − ε′)].
    Epsilon_prime = Epsilon / (1 - Epsilon)
    c = Epsilon * np.sqrt(2 * pi * (1 - Epsilon) * (1 - Epsilon_prime))
    # coupled with e^-L
    Term4 = Epsilon
    # coupled with L

    while (high - low) > tol:
        L = (low + high) / 2
        log_M = Zeta * L
        M = np.exp(log_M)
        Gamma = Delta ** 2 / 4 - Delta / (4 * np.exp(L)) - 16 * np.power(M, 1 - 2 * Tau) / np.power(log_M, 2 * Omega)
        Constant1= 3/(52*np.exp(2))
        Term1 = -Constant1*Gamma/np.power(M,2*Tau)
        Term3 = -L / 2 - np.log(c)

        feasible = Term1 * np.exp(L) + Term2 + Term3 * np.exp(-L) + Term4 * L < threshold
        if feasible:
            # print(f"Passes here")
            best_L = L
            high = L  # Try to find a smaller L in the lower half
        else:
            low = L  # Need a larger L, look in the upper half

    try:
        return best_L
    except NameError:
        return 4e9

def largest_M_for_Tx(Zeta,K,Tau,Eta,threshold_M,high=ceiling_search,low=0):

    feasible_on_left = True# Tau >= 1/2 #

    while (high - low) > tol:
        mid = (low + high) / 2
        log_M = Zeta * mid
        log_M_eta = np.pow(log_M, Eta-1)
        m_tau = np.exp(log_M * (1 - 2 * Tau))  # - 2/np.exp(log_M*2*Tau)
        # print(f"m^(1-2τ) = {m_tau}")
        # Using np.log and python's native ** power operator
        terms = [
            2 - m_tau/log_M,
            K * log_M_eta,
            -K * np.log(K) * log_M_eta,
            -K * Eta * log_M_eta * np.log(log_M),
            K * log_M_eta * log_M * (1 - 2 * Tau),
        ]
        # print(term1+term2-term3)
        feasible = sum(terms)*log_M < threshold_M and m_tau <= K * log_M ** Eta

        # print(f"L = {mid} and result is {result} ")
        # feasible = result < threshold_M

        if feasible:
            best_L = mid
            if feasible_on_left:
                low = mid  # Feasible! Let's push higher to find the *largest* valid L
            else:
                high = mid  # Feasible! Let's push lower to find the *least* valid L
        else:
            if feasible_on_left:
                high = mid  # Not feasible (too high), look lower
            else:
                low = mid  # Not feasible (too low), look higher

    try:
        return best_L
    except NameError:
        return 5e9

def smallest_L_for_zeta_req(Zeta,Tau,high=ceiling_search,low=floor_search):
    while (high - low) > tol:
        mid = (low + high) / 2


        if Zeta >= (2+np.log(4)/mid) / (2 + Tau):
            best_L = mid
            high = mid  # Try to find a smaller L in the lower half
        else:
            low = mid

    try:
        return best_L
    except NameError:
        return 6e9

def print_parameters(params):
    optimized_zeta, optimized_delta, optimized_omega, optimized_k, optimized_tau, optimized_eta= params
    print(f"ZETA= {optimized_zeta:.20e}")
    # print(f"EPSILON= {optimized_epsilon:.6e}")
    print(f"DELTA = {optimized_delta:.15e}")
    # print(f"GAMMA= {optimized_gamma:.15e}")
    print(f"OMEGA= {optimized_omega:.15f}")
    print(f"k_param={optimized_k:.15f}")
    print(f"TAU={optimized_tau:.15f}")
    print(f"ETA={optimized_eta:.15e}")

