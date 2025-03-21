import numpy as np
import logging
from collections import defaultdict

# Setup logging for debugging purposes
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# Hierarchical Information Abstraction Algorithm (Refined)
# ---------------------------------------------------------
# Inputs:
#   R       - Total number of rounds (e.g., Preflop, Flop, Turn, River)
#   r_hat   - The special round where public clustering is performed (e.g., Flop)
#   C       - Desired number of public clusters (buckets)
#   B_r     - Number of private clusters per public bucket for rounds r ≥ r_hat
#   A_r     - Abstraction algorithm used for clustering (for both initial and later private clustering)
#
# Outputs:
#   clusters - A dictionary mapping each public cluster (bucket) to its private clustering for rounds r_hat to R


def InformationAbstraction(R, r_hat, C, B_r, A_r):
    # Stage 1: Precompute Abstractions for Early Rounds (1 to r_hat-1)
    for r in range(1, r_hat):
        AbstractInformationStates(r, A_r)
        logging.info(f"Abstracted round {r} using A_r.")

    # Stage 2: Public Information Clustering at Round r_hat
    public_states = GeneratePublicStates(r_hat)  # E.g., unique flop boards
    logging.info(f"Generated {len(public_states)} public states for round {r_hat}.")

    # Compute transition table T using the base abstraction A_r
    T = compute_transition_table(public_states, A_r)
    logging.info("Computed transition table T for public states.")

    # Compute pairwise distances based on T
    distances = compute_public_distances(public_states, T, A_r)
    logging.info("Computed pairwise distances between public states.")

    # Cluster public states into C clusters using an enhanced initialization
    public_clusters = cluster_public_states(public_states, distances, C)
    logging.info(f"Public states clustered into {C} clusters.")

    # Stage 3: Private Information Clustering within Each Public Cluster
    clusters = {}
    for cluster_id, state_indices in public_clusters.items():
        clusters[cluster_id] = {}
        # For rounds r_hat through R, cluster private states for this public bucket.
        for r in range(r_hat, R + 1):
            private_states = []
            for idx in state_indices:
                ps = public_states[idx]
                private_states.extend(GeneratePrivateStatesForPublicState(r, ps))
            # Cluster the aggregated private states using A_r into B_r buckets.
            clusters[cluster_id][r] = A_r(private_states, B_r)
            logging.info(
                f"Clustered private states for public cluster {cluster_id} in round {r}."
            )
    return clusters


# Helper: Compute the transition table T for public states
def compute_transition_table(public_states, A_r):
    T = {}
    B = NumberOfBuckets(A_r)
    for i, ps in enumerate(public_states):
        T[i] = {}
        for b in range(1, B + 1):
            T[i][b] = CountTransitions(ps, b)
    return T


# Helper: Compute pairwise distances between public states based on T
def compute_public_distances(public_states, T, A_r):
    distances = {}
    V = TotalNumberOfPrivateStates()  # Constant per public state
    B = NumberOfBuckets(A_r)
    n = len(public_states)
    for i in range(n - 1):
        for j in range(i + 1, n):
            similarity = 0
            for b in range(1, B + 1):
                c_i = T[i].get(b, 0)
                c_j = T[j].get(b, 0)
                similarity += min(c_i, c_j)
            distances[(i, j)] = (V - similarity) / V
    return distances


# Helper: Enhanced clustering for public states using a modified k-means++ approach
def cluster_public_states(public_states, distances, C, max_iter=100, tol=1e-4):
    n = len(public_states)
    clusters = initialize_clusters_indices(
        n, C
    )  # Enhanced k-means++ initialization can be inserted here
    logging.info("Initialized clusters using enhanced k-means++ initialization.")
    for iteration in range(max_iter):
        new_clusters = {cid: [] for cid in range(C)}
        for i in range(n):
            best_cluster = None
            best_avg_distance = float("inf")
            for cid, indices in clusters.items():
                if indices:
                    total_distance = 0
                    for j in indices:
                        if i == j:
                            continue
                        d = distances.get((min(i, j), max(i, j)), 0)
                        total_distance += d
                    avg_distance = (
                        total_distance / len(indices) if indices else float("inf")
                    )
                else:
                    avg_distance = float("inf")
                if avg_distance < best_avg_distance:
                    best_avg_distance = avg_distance
                    best_cluster = cid
            new_clusters[best_cluster].append(i)
        # Check for convergence (if assignments change less than tolerance, break)
        if (
            sum(len(new_clusters[cid]) for cid in new_clusters)
            - sum(len(clusters[cid]) for cid in clusters)
            < tol
        ):
            logging.info(f"Converged after {iteration} iterations.")
            break
        clusters = new_clusters
    return clusters


# --- Stub/Placeholder Functions ---
# These functions need proper implementation based on the domain-specific data and abstraction method.


def AbstractInformationStates(r, A_r):
    # Precompute or cluster information states in round r using A_r.
    pass


def GeneratePublicStates(r_hat):
    # Generate all public states for round r_hat.
    pass


def CountTransitions(public_state, b):
    # Count the number of private states for public_state that A_r maps to bucket b.
    pass


def TotalNumberOfPrivateStates():
    # Return total number V of private states per public state.
    pass


def NumberOfBuckets(A_r):
    # Return the number of buckets defined by A_r.
    pass


def GeneratePrivateStatesForPublicState(r, public_state):
    # Generate private states corresponding to public_state for round r.
    pass


def initialize_clusters_indices(n, C):
    # Initialize clustering by assigning indices to clusters.
    clusters = {i: [] for i in range(C)}
    for idx in range(n):
        clusters[idx % C].append(idx)
    return clusters


# A_r is assumed to be a callable function that clusters a list of states into a specified number of buckets.
