
from typing import Sequence
import numpy as np



def simulate_markov_single(dates: Sequence, initial_state: str, transition_matrix: np.ndarray, state_labels: Sequence[str]=None):
    """
    Simulate a single Markov chain trajectory aligned with dates.

    Parameters:
        dates (np.ndarray): shape (k,), dtype datetime64[D]
        initial_state (str)): value in {0,...,N-1}
        transition_matrix (np.ndarray): shape (N,N)
        state_labels (array-like, optional): labels for states

    Returns:
        - main_states: PASS / SUPERVISION / SIM (forward-filled through renew states)
        - renew_flag: True if in any renew_* state
    """
    dates = np.asarray(dates)
    k = len(dates)
    n_states = transition_matrix.shape[0]

    # Validate
    if not np.allclose(transition_matrix.sum(axis=1), 1):
        raise ValueError("Rows of transition_matrix must sum to 1")

    if state_labels is None:
        state_labels = np.array([f"type{i+1}" for i in range(n_states)])

    # Simulate path
    states = np.zeros(k, dtype=int)

    states[0] = int(np.argwhere(state_labels==initial_state).flatten()[0])

    for t in range(1, k):
        states[t] = np.random.choice(
            np.arange(n_states),
            p=transition_matrix[states[t - 1]]
        )

    labeled_states = state_labels[states]

    # Combine with dates
     # --- Output 1: only main states ---
    main_states = labeled_states.copy()
     # --- main state with forward fill ---
    main_states = np.empty(k, dtype=object)

    # --- Output 2: renewal indicator ---
    renew_flag = np.char.startswith(labeled_states.astype(str), "RENEW")
    last_valid = None

    for t in range(k):
        if not renew_flag[t]:
            last_valid = labeled_states[t]
        main_states[t] = last_valid

    
    # trajectory = np.array(
    #     list(zip(dates, labeled_states)),
    #     dtype=[("date", "datetime64[D]"), ("state", "U20")]
    # )

    return main_states, renew_flag

# transition_matrix = np.array([[.2, .6, .1, .1, .0, .0  ],# type:PASS
#                               [.1, .5, .2, .0, .2, .0],#type: SUPERVISION
#                               [.3, .3, .3, .0, .0, .1], # type: SIM
#                               [1., .0, .0, .0,.0 , .0, ], # type : renew_pass
#                               [.0, 1., .0, .0 ,.0, .0, ], # type: renew_supervision
#                               [.0, .0, 1., .0, .0, .0] # type: renew sim
#                               ])

# state_labels = np.array(["PASS", "SUPERVISION", "SIM", "RENEW_PASS", "RENEW_SUPERVISION", "RENEW_SIM",])
# dates = list(range(1,6000))

# print(simulate_markov_single(dates, 0, transition_matrix, state_labels, ))