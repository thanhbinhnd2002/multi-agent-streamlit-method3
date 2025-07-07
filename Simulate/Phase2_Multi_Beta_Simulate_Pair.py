# ✅ Phase2_Multi_Beta_Simulate_Pair.py — Bổ sung chạy song song bằng joblib cho phase 2

import networkx as nx
import numpy as np
import pandas as pd
from joblib import Parallel, delayed  # ✅ Thêm joblib để chạy song song
from multiprocessing import cpu_count

# ✅ Hàm đọc mạng từ file .txt
def import_network(file_path):
    with open(file_path, "r") as f:
        data = f.readlines()[1:]
    G = nx.DiGraph()
    for line in data:
        from_node, to_node, direction, weight = line.strip().split("\t")
        direction = int(direction)
        weight = float(weight)
        G.add_edge(from_node, to_node, weight=float(weight))
        if direction == 0:
            G.add_edge(to_node, from_node, weight=float(weight))
    return G

# ✅ Tạo ma trận kề và danh sách hàng xóm
def build_adjacency(G, node_order):
    n = len(node_order)
    idx = {node: i for i, node in enumerate(node_order)}
    A = np.zeros((n, n))
    neighbors = {i: [] for i in range(n)}
    for u, v, d in G.edges(data=True):
        i, j = idx[u], idx[v]
        A[i, j] += d.get("weight", 1.0)
        neighbors[j].append(i)
    return A, neighbors, idx

# ✅ Cập nhật trạng thái tại mỗi bước
def update_states(x, A, neighbors, beta_indices, beta_weights, fixed_nodes, EPSILON, DELTA):
    x_new = x.copy()
    for u in range(len(x)):
        if u in fixed_nodes:
            continue
        influence = EPSILON * sum(A[v, u] * (x[v] - x[u]) for v in neighbors[u])
        beta_infl = DELTA * sum(w * (x[b] - x[u]) for b, w in zip(beta_indices, beta_weights[u]))
        x_new[u] = x[u] + influence + beta_infl
    return np.clip(x_new, -1000, 1000)

# ✅ Mô phỏng 1 lượt gán beta vào driver
def simulate_one_round(G, beta_nodes, alpha_node, x_prev, EPSILON, DELTA, MAX_ITER, TOL):
    node_order = list(G.nodes())
    extended = node_order + [f"Beta{i}" for i in range(len(beta_nodes))]
    A, neighbors, node_index = build_adjacency(G, extended)

    x = np.pad(x_prev, (0, len(extended) - len(x_prev)), mode='constant')
    beta_indices = []
    fixed_nodes = set()
    beta_weights = [[0] * len(beta_nodes) for _ in range(len(extended))]

    for i, b in enumerate(beta_nodes):
        bname = f"Beta{i}"
        bidx = node_index[bname]
        A[bidx, node_index[b]] = 1.0
        neighbors[node_index[b]].append(bidx)
        x[bidx] = -1
        beta_indices.append(bidx)
        fixed_nodes.add(bidx)
        beta_weights[node_index[b]][i] = 1.0

    for _ in range(MAX_ITER):
        x_new = update_states(x, A, neighbors, beta_indices, beta_weights, fixed_nodes, EPSILON, DELTA)
        if np.linalg.norm(x_new - x) < TOL:
            break
        x = x_new

    return x[:len(node_order)]

# ✅ Tổng hỗ trợ

def compute_total_support(x_state, alpha_idx):
    return sum(1 if x > 0 else -1 if x < 0 else 0 for i, x in enumerate(x_state) if i != alpha_idx)

# ✅ Mô phỏng cho 1 alpha node

def simulate_one_alpha(alpha_node, G, drivers, node_order, EPSILON, DELTA, MAX_ITER, TOL, N_BETA):
    if alpha_node not in node_order:
        return None
    node_index = {node: i for i, node in enumerate(node_order)}
    alpha_idx = node_index[alpha_node]
    x_state = np.zeros(len(node_order))
    x_state[alpha_idx] = 1

    for i in range(0, len(drivers), N_BETA):
        beta_group = drivers[i:i + N_BETA]
        if alpha_node in beta_group:
            continue
        x_state = simulate_one_round(G, beta_group, alpha_node, x_state, EPSILON, DELTA, MAX_ITER, TOL)

    support = compute_total_support(x_state, alpha_idx)
    return {"Alpha_Node": alpha_node, "Total_Support": support}

# ✅ Gọi từ file driver-target

def simulate_from_driver_target_file(graph_path, pair_csv_path, EPSILON, DELTA, MAX_ITER, TOL, N_BETA):
    G = import_network(graph_path)
    node_order = list(G.nodes())
    pair_df = pd.read_csv(pair_csv_path)

    all_results = []
    for _, row in pair_df.iterrows():
        drivers = row['Driver_Nodes'].split(',')
        targets = row['Target_Nodes'].split(',')

        # ✅ Chạy song song các alpha_node
        results = Parallel(n_jobs=cpu_count() // 2)(
            delayed(simulate_one_alpha)(alpha_node, G, drivers, node_order,
                                        EPSILON, DELTA, MAX_ITER, TOL, N_BETA)
            for alpha_node in targets
        )
        all_results.extend([r for r in results if r is not None])

    return pd.DataFrame(all_results)
