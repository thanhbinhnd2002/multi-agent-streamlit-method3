# ✅ MÔ HÌNH CẠNH TRANH NGOÀI VỚI NHIỀU BETA - CPU (NumPy)
# ✅ Gán alpha là target node, beta là driver node (đọc từ file driver-target)

import os
import numpy as np
import pandas as pd
import networkx as nx
from tqdm import tqdm
from joblib import Parallel, delayed, cpu_count
from ast import literal_eval

INF = 10000
EPSILON = 0.1
DELTA = 0.2
MAX_ITER = 10
TOL = 1e-3

# ✅ B1: Đọc mạng từ file
def import_network(file_path):
    with open(file_path, "r") as f:
        data = f.readlines()[1:]
    G = nx.DiGraph()
    for line in data:
        from_node, to_node, direction, weight = line.strip().split("\t")
        direction = int(direction)
        weight = float(weight)
        G.add_edge(from_node, to_node, weight=weight)
        if direction == 0:
            G.add_edge(to_node, from_node, weight=weight)
    return G

# ✅ B2: Ma trận kề và hàng xóm
def build_adjacency(G, node_order):
    n = len(node_order)
    node_index = {node: i for i, node in enumerate(node_order)}
    A = np.zeros((n, n))
    neighbors = {i: [] for i in range(n)}
    for u, v, data in G.edges(data=True):
        i, j = node_index[u], node_index[v]
        A[i, j] += data.get("weight", 1.0)
        neighbors[j].append(i)
    return A, neighbors, node_index

# ✅ B3: Cập nhật trạng thái
def update_states_multi_beta(x, A, neighbors, beta_indices, beta_weights, fixed_nodes):
    n = len(x)
    x_new = x.copy()
    for u in range(n):
        if u in fixed_nodes:
            continue
        influence = EPSILON * sum(A[v, u] * (x[v] - x[u]) for v in neighbors[u])
        beta_influence = DELTA * sum(w * (x[b] - x[u]) for b, w in zip(beta_indices, beta_weights[u]))
        x_new[u] = x[u] + influence + beta_influence
    return x_new

# ✅ B4: Mô phỏng cạnh tranh ngoài
def simulate_competition(G, alpha_nodes, beta_nodes):
    node_order = list(G.nodes()) + [f"Beta{i}" for i in range(len(beta_nodes))]
    A, neighbors, node_index = build_adjacency(G, node_order)
    n = len(node_order)

    x = np.zeros(n)
    alpha_indices = [node_index[a] for a in alpha_nodes]
    for idx in alpha_indices:
        x[idx] = 1  # Alpha cố định +1

    beta_indices = []
    fixed_nodes = set()
    beta_weights = [[0] * len(beta_nodes) for _ in range(n)]

    for i, attach_node in enumerate(beta_nodes):
        beta_name = f"Beta{i}"
        beta_idx = node_index[beta_name]
        A[beta_idx, node_index[attach_node]] = 1.0
        neighbors[node_index[attach_node]].append(beta_idx)
        x[beta_idx] = -1
        beta_indices.append(beta_idx)
        fixed_nodes.add(beta_idx)
        beta_weights[node_index[attach_node]][i] = 1.0

    for _ in range(MAX_ITER):
        x_new = update_states_multi_beta(x, A, neighbors, beta_indices, beta_weights, fixed_nodes)
        if np.linalg.norm(x_new - x) < TOL:
            break
        x = x_new

    return x[:len(G.nodes())]

# ✅ B5: Tính tổng hỗ trợ
def compute_total_support(x_state, alpha_indices):
    support_dict = {}
    for alpha_idx in alpha_indices:
        support = 0
        for j in range(len(x_state)):
            if j == alpha_idx:
                continue
            if x_state[j] > 0:
                support += 1
            elif x_state[j] < 0:
                support -= 1
        support_dict[alpha_idx] = support
    return support_dict

# ✅ B6: Xử lý từng dòng driver-target (target là alpha)
def process_target_driver(G, targets, drivers):
    node_order = list(G.nodes())
    results = []

    for alpha in targets:
        x_state = simulate_competition(G, [alpha], drivers)
        alpha_idx = node_order.index(alpha)
        support = compute_total_support(x_state, [alpha_idx])
        results.append({"Alpha_Node": alpha, "Total_Support": support[alpha_idx]})

    return results

# ✅ B7: Main
if __name__ == "__main__":
    input_folder = "data_2"
    pair_folder = "driver_nodes_2"
    output_folder = "output_multi_beta_pair_cpu"
    os.makedirs(output_folder, exist_ok=True)

    for file in os.listdir(input_folder):
        if not file.endswith(".txt"):
            continue
        path = os.path.join(input_folder, file)
        base = os.path.splitext(file)[0]

        G = import_network(path)
        pair_file = os.path.join(pair_folder, f"{base}_pairs.csv")
        pairs_df = pd.read_csv(pair_file)

        results = Parallel(n_jobs=cpu_count() // 2)(
            delayed(process_target_driver)(
                G,
                literal_eval(row["Target_Nodes"]),
                literal_eval(row["Driver_Nodes"])
            ) for _, row in tqdm(pairs_df.iterrows(), total=len(pairs_df), desc=f"🔁 {base}")
        )

        all_results = [item for sublist in results for item in sublist]
        df = pd.DataFrame(all_results)
        df.to_csv(os.path.join(output_folder, base + "_cpu_result.csv"), index=False)
        print(f"✅ Đã lưu kết quả vào {output_folder}/{base}_cpu_result.csv")
