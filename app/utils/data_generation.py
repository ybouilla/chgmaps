
from typing import Sequence, List
from datetime import datetime

import numpy as np

def generate_pareto(
    values: List[int],
    total_size: int = 100,
    alpha: float = 1.5,
    shuffle: bool = True
) -> List[int]:
    """
    Generate a list where:
    - each value appears at least once
    - total length = total_size
    - frequencies follow a Pareto-like distribution
    """

    values = np.asarray(values)
    n = len(values)

    if total_size < n:
        raise ValueError("total_size must be >= number of unique values")

    # Step 1: base allocation (1 per value)
    base_counts = np.ones(n, dtype=int)
    remaining = total_size - n

    # Step 2: Pareto-like weights (vectorized)
    weights = values.astype(float) ** (-alpha)
    weights_sum = weights.sum()

    # Step 3: expected extra counts
    expected_extra = weights / weights_sum * remaining
    extra_counts = np.floor(expected_extra).astype(int)

    # Step 4: distribute remainder (rounding correction)
    remainder = remaining - extra_counts.sum()

    if remainder > 0:
        fractional = expected_extra - extra_counts
        top_indices = np.argsort(-fractional)[:remainder]
        extra_counts[top_indices] += 1

    # Final counts
    counts = base_counts + extra_counts

    # Step 5: build result 
    result = np.repeat(values, counts)

    # Step 6: shuffle
    if shuffle:
        np.random.shuffle(result)

    return result.tolist()


def generate_creation_dates(
    nb_dates: int,
    starting_date: np.datetime64,
    q1_ratio: float = 0.5,
    year_prob: Sequence[float] = None
) -> np.ndarray:
    """
    Generate random weekday dates with constraints on:
    - Q1 ratio
    - yearly distribution

    Parameters
    ----------
    nb_dates : int
        Total number of dates to generate.

    starting_date : np.datetime64
        Start of date range.

    q1_ratio : float, default=0.5
        Proportion of dates coming from Q1 (Jan–Mar).

    year_prob : Sequence or None
        Probability distribution over years starting from `starting_date.year`
        Example:
            (0.3, 0.3, 0.3, 0.1,) → for 2023, 2024, 2025, 2026

    Returns
    -------
    np.ndarray
        Array of dates (numpy datetime64[D])
    """

    if not (0 <= q1_ratio <= 1):
        raise ValueError("q1_ratio must be between 0 and 1")

    end = np.datetime64('today', 'D')

    # Full date range
    all_dates = np.arange(starting_date, end + np.timedelta64(1, 'D'))

    # Keep weekdays only
    weekdays_mask = (all_dates.astype('datetime64[D]').astype(int) + 4) % 7 < 5
    weekdays = all_dates[weekdays_mask]

    # Extract years
    years = weekdays.astype('datetime64[Y]').astype(int) + 1970
    unique_years = np.unique(years)

    # -----------------------
    # YEAR SAMPLING LOGIC
    # -----------------------
    if year_prob is None:
        year_prob = np.ones(len(unique_years)) / len(unique_years)

    year_prob = np.asarray(year_prob)

    if len(year_prob) != len(unique_years):
        raise ValueError("year_prob must match number of available years")

    # Normalize (safety)
    year_prob = year_prob / year_prob.sum()

    # Assign each date to its year probability
    year_choice = np.random.choice(unique_years, size=nb_dates, p=year_prob)

    result = []

    for y in unique_years:
        # Dates in this year
        year_mask = years == y
        year_dates = weekdays[year_mask]

        if len(year_dates) == 0:
            continue

        # Q1 split
        months = (year_dates.astype('datetime64[M]').astype(int) % 12) + 1
        q1_dates = year_dates[np.isin(months, [1, 2, 3])]

        # how many samples for this year
        n_y = np.sum(year_choice == y)
        q1_count = int(np.round(n_y * q1_ratio))
        other_count = n_y - q1_count

        # sample
        if len(q1_dates) > 0:
            sampled_q1 = np.random.choice(q1_dates, size=q1_count, replace=True)
        else:
            sampled_q1 = np.array([], dtype='datetime64[D]')

        sampled_all = np.random.choice(year_dates, size=other_count, replace=True)

        result.append(np.concatenate([sampled_q1, sampled_all]))

    result = np.concatenate(result)
    # np.random.shuffle(result)

    return result


def generate_type_licenses(
    subscription_prices: Sequence[float],
    subscription_prob: Sequence[float],
    nb_id: int = 100,
) -> np.ndarray:
    """
    Generate a sample of subscription prices based on a discrete probability distribution.

    Parameters
    ----------
    subscription_prices : Sequence[float]
        Available subscription price points (e.g. [0, 10, 100, 1000, 5000]).

    subscription_prob : Sequence[float]
        Probability of each price. Must have the same length as `subscription_prices`
        and sum to 1 (or close to 1 due to floating-point precision).

    nb_id : int, default=100
        Number of samples to generate.

    Returns
    -------
    np.ndarray
        Array of sampled subscription prices of size `n`.

    Raises
    ------
    ValueError
        If lengths of `subscription_prices` and `subscription_prob` do not match.

    Notes
    -----
    - Sampling is done with replacement using a categorical distribution.
    - Results reflect probabilistic sampling (counts may vary slightly per run).
    - For deterministic exact counts, a different allocation approach is required.

    Example
    -------
    >>> generate_subscription_prices(
    ...     [0, 10, 100, 1000, 5000],
    ...     [0.3, 0.3, 0.3, 0.05, 0.05],
    ...     100
    ... )
    array([  0, 100,  10, ...])
    """

    prices = np.asarray(subscription_prices)
    probs = np.asarray(subscription_prob)

    if len(prices) != len(probs):
        raise ValueError("subscription_prices and subscription_prob must have the same length")

    return np.random.choice(prices, size=nb_id, p=probs)


def generate_boolean_list(
    n: int = 100,
    p_true: float = 0.5,
) -> List[bool]:
    """
    Generate a list of boolean values (True/False) following a Bernoulli distribution.

    Parameters
    ----------
    n : int, default=100
        Number of values to generate.

    p_true : float, default=0.5
        Probability of True. Must be between 0 and 1.


    Returns
    -------
    List[bool]
        List of length `n` containing True/False values.

    Raises
    ------
    ValueError
        If p_true is not in [0, 1].

    Example
    -------
    >>> generate_boolean_list(n=4, p_true=0.7,)
    [True, True, False, True]
    """

    if not (0 <= p_true <= 1):
        raise ValueError("p_true must be between 0 and 1")

    return np.random.rand(n) < p_true

import numpy as np

# def simulate_markov_paths(initial_states, transition_matrix, k):
#     """
#     Simulate multiple Markov chain paths.

#     Parameters:
#         initial_states (array-like): shape (n,), values in {0,1,2}
#         transition_matrix (np.ndarray): shape (3,3), rows sum to 1
#         k (int): number of steps

#     Returns:
#         np.ndarray: shape (n, k) with state indices
#     """
#     initial_states = np.asarray(initial_states, dtype=int)
#     n = len(initial_states)

#     paths = np.zeros((n, k), dtype=int)
#     paths[:, 0] = initial_states

#     for t in range(1, k):
#         prev_states = paths[:, t - 1]

#         # For each trajectory, sample next state based on its current state
#         for s in range(3):
#             mask = (prev_states == s)
#             n_s = np.sum(mask)
#             if n_s > 0:
#                 paths[mask, t] = np.random.choice(
#                     [0, 1, 2],
#                     size=n_s,
#                     p=transition_matrix[s]
#                 )

#     return paths





def generate_dates(start_date, n_dates: int):
    """
    Generate n_dates between start_date and now.
    
    Parameters:
        start_date (str or datetime): starting date (e.g. "2023-01-01")
        n_dates (int): number of dates to generate
    
    Returns:
        numpy.ndarray of np.datetime64 objects
    """
    # Convert start_date to datetime if needed
    if isinstance(start_date, str):
        start_date = datetime.fromisoformat(start_date)
    
    
    start = np.datetime64(start_date, 'D')
    today = np.datetime64('today', 'D')

    # Convert to integer days since epoch
    start_int = start.astype('int64')
    today_int = today.astype('int64')
    
    # Generate random timestamps between start and now
    # Random days (inclusive of both ends)
    random_days = np.random.randint(start_int, today_int + 1, size=n_dates)

    # sort random days
    random_days.sort()
    # Convert back to datetime64[D]
    return random_days.astype('datetime64[D]')
    
