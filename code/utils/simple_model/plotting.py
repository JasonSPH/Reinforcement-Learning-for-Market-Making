import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from environments.simple_model.simple_model_mm import SimpleEnv
from collections import defaultdict
import pickle


def plot_optimal_depth(D, bid=True, discrete=True):
    """
    plots the optimal depths based on D

    Parameters
    ----------
    D : np.array
        a numpy array (2Q+1) x (T+1) with the optimal depths for all levels of q at all time steps
    bid : bool
        whether or not the data is for bid or ask
    discrete : bool
        whether or not the data is rounded or not

    Returns
    -------
    None
    """

    LO_type = "bid" if bid else "ask"

    n_levels = D.shape[0]

    if discrete:
        D = D[:, 0:(D.shape[1]-1)]

    plt.figure()
    for level in range(n_levels):
        plt.plot(D[level], ('-o' if discrete else '-'), label="q = " + str(int(level + (1 - n_levels) / 2)))

    plt.title("Optimal (" + ("discrete" if discrete else "continuous") + ") " + LO_type + " depths as a function of t")
    plt.ylabel(LO_type + " depth")
    plt.xlabel("time (t)")
    plt.ylim([-0.001, 0.021])
    plt.yticks(np.arange(3) * 0.010)
    if discrete and D.shape[1] < 10:
        plt.xticks(np.arange(0, D.shape[1]))
    # plt.yticks(np.arange(0, 0.025, 0.005))
    plt.legend()
    plt.show()


def generate_optimal_depth(T=30, Q=3, dp=0.01, phi=1e-5, bid=True, discrete=True):
    """
    generates the optimal depths for bid or ask

    Parameters
    ----------
    T : int
        the length of the episodes
    Q : int
        the maximal absolute allowed volume to hold
    dp : float
        the tick size
    phi : float
        the running inventory penalty
    bid : bool
        whether or not the data is for bid or ask
    discrete : bool
        whether or not the data is rounded or not

    Returns
    -------
    data : np.array
        a numpy array (2Q+1) x (T+1) with the optimal depths for all levels of q at all time steps
    """

    env = SimpleEnv(T, Q=Q, dp=dp, phi=phi)

    data = []

    q_s = np.arange(start=-env.Q, stop=env.Q + 1)

    for q in q_s:
        data_q = []
        for t in range(T + 1):
            env.t = t
            env.Q_t = q
            if discrete:
                depth = env.transform_action(env.discrete_analytically_optimal())[1 - bid] * (1 - 2 * bid)
            else:
                depth = env.calc_analytically_optimal()[1 - bid]

            data_q.append(depth)

        data.append(data_q)

    data = np.array(data)

    return data


def heatmap_Q(Q_tab, file_path = None):
    """
    generates a heatmap based on Q_tab

    Parameters
    ----------
    Q_tab : dictionary
        a dictionary with values for all state-action pairs

    Returns
    -------
    None
    """

    optimal_bid = dict()
    optimal_ask = dict()

    plt.figure()
    for state in list(Q_tab.keys()):
        optimal_action = np.unravel_index(Q_tab[state].argmax(), Q_tab[state].shape)
        optimal_bid[state] = optimal_action[0]
        optimal_ask[state] = optimal_action[1]
        # optimal_bid[state] = optimal_action[0] + 1
        # optimal_ask[state] = optimal_action[1] + 1

    for state in list(Q_tab.keys()):
        if state[0] == 3:
            optimal_bid.pop(state, None)
        if state[0] == -3:
            optimal_ask.pop(state, None)

    ser = pd.Series(list(optimal_bid.values()),
                    index=pd.MultiIndex.from_tuples(optimal_bid.keys()))
    df = ser.unstack().fillna(0)
    fig = sns.heatmap(df, vmin=0, vmax=3)
    fig.set_title("Optimal bid depth")
    fig.set_xlabel("time (t)")
    fig.set_ylabel("inventory (q)")

    if file_path == None:
        plt.show()
    else:
        plt.savefig(file_path + "opt_bid_heat")
        plt.close()

    plt.figure()
    ser = pd.Series(list(optimal_ask.values()),
                    index=pd.MultiIndex.from_tuples(optimal_ask.keys()))
    df = ser.unstack().fillna(0)
    fig = sns.heatmap(df, vmin=0, vmax=3)
    fig.set_title("Optimal ask depth")
    fig.set_xlabel("time (t)")
    fig.set_ylabel("inventory (q)")

    if file_path == None:
        plt.show()
    else:
        plt.savefig(file_path + "opt_ask_heat")
        plt.close()


def heatmap_Q_std(Q_std, file_path = None):
    """
    Plots a heatmap of the standard deviation of the q-value of the optimal actions

    Parameters
    ----------
    Q_std : defaultdict
        a defaultdict with states as keys and standard deviations as values

    Returns
    -------
    None
    """

    plt.figure()

    ser = pd.Series(list(Q_std.values()),
                    index=pd.MultiIndex.from_tuples(Q_std.keys()))
    df = ser.unstack().fillna(0)
    fig = sns.heatmap(df)
    fig.set_title("Standard deviation of optimal actions")
    fig.set_xlabel("time (t)")
    fig.set_ylabel("inventory (q)")

    if file_path == None:
        plt.show()
    else:
        plt.savefig(file_path + "heatmap_of_std")
        plt.close()


def heatmap_Q_n_errors(Q_mean, Q_tables, n_unique = True, file_path = None):
    """
    Plots a heatmap of the difference in optimal actions between runs. Can show number of
    unique actions or number of actions not agreeing with mean optimal.

    Parameters
    ----------
    Q_mean : defaultdict
        a defaultdict with states as keys and mean q-values as values
    Q_tables : list
        a list with defaultdicts with states as keys and q-values as values
    n_unique : bool
        whether or not number of unique actions should be used or not. If False,
        errors compared to mean optimal will be used

    Returns
    -------
    None
    """

    Q_n_errors = Q_mean

    if n_unique:
        # ----- CALCULATE THE NUMBER OF UNIQUE ACTIONS -----
        title = "Number of unique of optimal actions"
        vmin = 1
        for state in list(Q_mean.keys()):
            opt_action_array = []

            for Q_tab in Q_tables:
                opt_action = np.unravel_index(Q_tab[state].argmax(), Q_tab[state].shape)
                opt_action_array.append(opt_action)

            n_unique_opt_actions = len(set(opt_action_array))

            Q_n_errors[state] = n_unique_opt_actions

    else:
        # ----- CALCULATE THE NUMBER ERROS COMPARED TO MEAN OPTIMAL -----
        title = "Number of actions not agreeing with mean optimal action"
        vmin = 0
        for state in list(Q_mean.keys()):
            num_errors = 0

            for Q_tab in Q_tables:
                error = np.unravel_index(Q_tab[state].argmax(), Q_tab[state].shape) != np.unravel_index(Q_mean[state].argmax(), Q_mean[state].shape)
                num_errors += error

            Q_n_errors[state] = num_errors

    plt.figure()

    ser = pd.Series(list(Q_n_errors.values()),
                index=pd.MultiIndex.from_tuples(Q_n_errors.keys()))
    df = ser.unstack().fillna(0)
    fig = sns.heatmap(df, vmin=vmin, vmax=len(Q_tables))
    fig.set_title(title)
    fig.set_xlabel("time (t)")
    fig.set_ylabel("inventory (q)")

    if file_path == None:
        plt.show()

    else:
        if n_unique:
            plt.savefig(file_path + "n_unique_opt_actions")
            plt.close()
        else:
            plt.savefig(file_path + "n_errors_compared_to_mean")
            plt.close()
    

def remove_last_t(Q_tab, T = 5):
    for state in list(Q_tab.keys()):
        if state[1] == T:
            Q_tab.pop(state, None)

    return Q_tab


def Q_table_to_array(Q_tab, env):
    optimal_bid = dict()
    optimal_ask = dict()

    for state in list(Q_tab.keys()):
        optimal_action = np.array(np.unravel_index(Q_tab[state].argmax(), Q_tab[state].shape))
        [optimal_bid[state], optimal_ask[state]] = (optimal_action + env.min_dp) * env.dp
    
    for state in list(Q_tab.keys()):
        if state[0] == 3:
            optimal_bid[state] = np.inf
        if state[0] == -3:
            optimal_ask[state] = np.inf  
    
    # ===== BID =====

    ser = pd.Series(list(optimal_bid.values()),
                    index=pd.MultiIndex.from_tuples(optimal_bid.keys()))
    df = ser.unstack()

    df = df.to_numpy()

    array_bid = df[0:(df.shape[0]-1), 0:(df.shape[1]-1)]

    # ===== ASK =====
    ser = pd.Series(list(optimal_ask.values()),
                    index=pd.MultiIndex.from_tuples(optimal_ask.keys()))
    df = ser.unstack()

    df = df.to_numpy()

    array_ask = df[1:(df.shape[0]), 0:(df.shape[1]-1)]

    return array_bid, array_ask

def show_Q(Q_tab, env, file_path = None):
    """
    plotting the optimal depths from Q_tab

    Parameters
    ----------
    Q_tab : dictionary
        a dictionary with values for all state-action pairs
    env : class object
        the environment used to train Q

    Returns
    -------
    None
    """

    optimal_bid = dict()
    optimal_ask = dict()

    for state in list(Q_tab.keys()):
        optimal_action = np.array(np.unravel_index(Q_tab[state].argmax(), Q_tab[state].shape))
        [optimal_bid[state], optimal_ask[state]] = (optimal_action + env.min_dp) * env.dp
    
    for state in list(Q_tab.keys()):
        if state[0] == 3:
            optimal_bid[state] = np.inf
        if state[0] == -3:
            optimal_ask[state] = np.inf  
    
    ser = pd.Series(list(optimal_bid.values()),
                    index=pd.MultiIndex.from_tuples(optimal_bid.keys()))
    df = ser.unstack()
    df = df.T
    df.columns = "q=" + df.columns.map(str)
    df.plot.line(title="Optimal bid depth", style='.-')
    plt.legend(loc="upper right")
    plt.xlabel("time (t)")
    plt.ylabel("depth")
    plt.xticks(np.arange(df.shape[0]))
    plt.yticks(np.arange(3) * 0.010)

    if file_path == None:
        plt.show()
    else:
        plt.savefig(file_path + "opt_bid_strategy")
        plt.close()

    ser = pd.Series(list(optimal_ask.values()),
                    index=pd.MultiIndex.from_tuples(optimal_ask.keys()))
    df = ser.unstack()
    df = df.T
    df.columns = "q=" + df.columns.map(str)
    df.plot.line(title="Optimal ask depth", style='.-')
    plt.legend(loc="upper right")
    plt.xlabel("time (t)")
    plt.ylabel("depth")
    plt.xticks(np.arange(df.shape[0]))
    plt.yticks(np.arange(3) * 0.010)

    if file_path == None:
        plt.show()
    else:
        plt.savefig(file_path + "opt_ask_strategy")
        plt.close()


if __name__ == "__main__":
    if False:
        args = {"d": 3, "T": 30, "dp": 0.01, "min_dp": 0, "alpha": 1e-4, "phi": 1e-5, "use_all_times": True}

        env = SimpleEnv(**args, printing=False, debug=False)

        # Q_tab = load_Q("Q_d3_T30_dp0.01_min_dp0_alpha0.0001_phi1e-05_use_all_timesTrue_n100000")[0]
        # print(Q_tab)
        # heatmap_Q(Q_tab)
        # show_Q(Q_tab, env)

        # ----- PLOTTING THE OPTIMAL DEPTHS -----
        if True:
            bid = True
            phi = 1e-5

            T = 30

            data_discrete = generate_optimal_depth(T=T, bid=bid, phi=phi, discrete=True)
            data_continuous = generate_optimal_depth(T=T, bid=bid, phi=phi, discrete=False)

            plot_optimal_depth(data_discrete, bid=bid, discrete=True)
            plot_optimal_depth(data_continuous, bid=bid, discrete=False)

    # ----- PLOTTING THE FILL RATE AND INVENTORY DRIFT -----
    if True:
        t = 15
        T = 20
        Q = 10
        lambd = 1
        kappa = 100
        phis = [2e-3, 1e-3, 5e-4]

        fills_ask = []
        fills_bid = []

        colors = ["C0", "C1", "C2"]

        qs = np.arange(start=-Q, stop=Q + 1)

        plt.figure()
        for i, phi in enumerate(phis):
            depths_bid = generate_optimal_depth(bid=True, T=T, Q=Q, phi=phi, discrete=False)[:, t]
            fill_rate_bid = lambd * np.exp(- kappa * depths_bid)
            plt.plot(qs, fill_rate_bid, '+', markersize=10, label="Buy - $\phi$ = " + str(phi), color=colors[i])
            fills_bid.append(fill_rate_bid)

        for i, phi in enumerate(phis):
            depths_ask = generate_optimal_depth(bid=False, T=T, Q=Q, phi=phi, discrete=False)[:, t]
            fill_rate_ask = lambd * np.exp(- kappa * depths_ask)
            plt.plot(qs, fill_rate_ask, 'o', label="Sell - $\phi$ = " + str(phi), color=colors[i])
            fills_ask.append(fill_rate_ask)

        plt.ylim([-1, 26])
        plt.xticks(np.arange(-10, 11, 5))
        plt.yticks(np.arange(0, 26, 5))
        plt.title("Fill rates as a function of q")
        plt.ylabel("Fill rate")
        plt.xlabel("Inventory (q)")
        plt.legend()
        plt.show()

        plt.figure()
        drift = np.array(fills_bid) - np.array(fills_ask)

        for phi in range(drift.shape[0]):
            plt.plot(qs, drift[phi, :], 'o', label="$\phi$ = " + str(phis[phi]), color=colors[phi])

        plt.ylim([-31, 31])
        plt.xticks(np.arange(-10, 11, 5))
        plt.yticks(np.arange(-30, 31, 10))
        plt.title("Inventory drift as a function of q")
        plt.ylabel("Inventory drift")
        plt.xlabel("Inventory (q)")
        plt.legend()
        plt.show()
