# ✅ multi_Beta_Simulate_Pair.py — Pha 2 của phương pháp 3: Mô phỏng từ driver–target pairs
# ✅ Dùng cho giao diện tkinter — không dùng joblib, trả về DataFrame kết quả

import networkx as nx
import numpy as np
import pandas as pd

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

# ✅ Chạy mô phỏng cho một cặp (driver list, target list)
def simulate_from_pair(G, drivers, targets, EPSILON, DELTA, MAX_ITER, TOL, N_BETA):
    node_order = list(G.nodes())
    A, neighbors, node_index = build_adjacency(G, node_order)
    results = []

    for alpha_node in targets:
        if alpha_node not in node_index:
            continue
        alpha_idx = node_index[alpha_node]
        x_state = np.zeros(len(node_order))
        x_state[alpha_idx] = 1

        for i in range(0, len(drivers), N_BETA):
            beta_group = drivers[i:i + N_BETA]
            if alpha_node in beta_group:
                continue
            x_state = simulate_one_round(G, beta_group, alpha_node, x_state, EPSILON, DELTA, MAX_ITER, TOL)

        support = compute_total_support(x_state, alpha_idx)
        results.append({"Alpha_Node": alpha_node, "Total_Support": support})

    return pd.DataFrame(results)

# ✅ Dạng chuẩn hóa cho mô phỏng từng lượt

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

# ✅ Tính tổng hỗ trợ sau mô phỏng

def compute_total_support(x_state, alpha_idx):
    return sum(1 if x > 0 else -1 if x < 0 else 0 for i, x in enumerate(x_state) if i != alpha_idx)

# ✅ Hàm gọi từ giao diện tkinter

def simulate_from_driver_target_file(graph_path, pair_csv_path, EPSILON, DELTA, MAX_ITER, TOL, N_BETA):
    G = import_network(graph_path)
    pair_df = pd.read_csv(pair_csv_path)
    all_results = []

    for _, row in pair_df.iterrows():
        drivers = row['Driver_Nodes'].split(',')
        targets = row['Target_Nodes'].split(',')
        df = simulate_from_pair(G, drivers, targets, EPSILON, DELTA, MAX_ITER, TOL, N_BETA)
        all_results.append(df)

    return pd.concat(all_results, ignore_index=True)
