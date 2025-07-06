# ✅ PHIÊN BẢN CHẠY LẶP QUA CÁC TARGET NODE KHÁC NHAU VÀ LƯU VÀO CÙNG 1 FILE CHO MỖI MẠNG
# ✅ Xử lý nhiều file mạng trong thư mục 'data/' và lưu kết quả vào thư mục 'driver_nodes/'

import networkx as nx
import numpy as np
from tqdm import tqdm
import random
from joblib import Parallel, delayed, cpu_count
import os
import pandas as pd

# ✅ Cố định seed để kết quả nhất quán mỗi lần chạy
random.seed(42)
np.random.seed(42)

def import_network(file_path):
    """
    ✅ Đọc mạng từ file txt, định dạng: Source, Target, Direction, Weight
    Nếu Direction == 1: cạnh thuận chiều.
    Nếu Direction == 0: cạnh hai chiều.
    """
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

def select_target_nodes_non_overlap(G: nx.DiGraph, percent, excluded_nodes):
    nodes = list(set(G.nodes()) - excluded_nodes)
    d = int(percent * len(G.nodes()) / 100)

    # ✅ Nếu số node còn lại < d thì chọn hết phần còn lại
    if len(nodes) <= d:
        return nodes

    # ✅ Ngược lại chọn bình thường nhưng đảm bảo liên thông
    max_trials = 1000  # Tránh lặp vô hạn
    for _ in range(max_trials):
        start = random.choice(nodes)
        reachable = set(nx.descendants(G, start)) | {start}
        reachable = reachable - excluded_nodes
        if len(reachable) >= d:
            selected = list(reachable)[:d]
            return selected

    # ✅ Nếu không tìm được thành phần liên thông đủ lớn thì dừng
    print("⚠️ Không còn thành phần liên thông đủ lớn, dừng việc chọn target node!")
    return []

def _process_single_source(src, G, target_nodes, max_depth):
    lengths = nx.single_source_shortest_path_length(G, src, cutoff=max_depth)
    H_src = {}
    K_update = []
    for tgt in target_nodes:
        if tgt in lengths:
            dist = lengths[tgt]
            H_src.setdefault(dist, set()).add(tgt)
            K_update.append((tgt, src, dist))
    return src, H_src, K_update

def build_H_K_fast(G: nx.DiGraph, target_nodes, max_depth=None):
    nodes = list(G.nodes())
    n_cores = max(1, cpu_count() // 2)
    results = Parallel(n_jobs=n_cores)(
        delayed(_process_single_source)(src, G, target_nodes, max_depth)
        for src in tqdm(nodes, desc="Parallel BFS")
    )
    H = {src: {} for src in nodes}
    K = {t: {src: [] for src in nodes} for t in target_nodes}
    for src, H_src, K_updates in results:
        H[src] = H_src
        for tgt, s, d in K_updates:
            K[tgt][s].append(d)
    return H, K

def compute_Y_fast(H, K):
    Y = {}
    for src in tqdm(H.keys(), desc="Computing Y sets"):
        reached = set()
        for d in H[src]:
            reached.update(H[src][d])
        unique = []
        for t in reached:
            t_key = frozenset(K[t][src])
            if all(frozenset(K[tt][src]) != t_key for tt in unique):
                unique.append(t)
        Y[src] = set(unique)
    return Y

def find_driver_nodes_fast(Y, target_nodes):
    driver = []
    covered = set()
    target_nodes = set(target_nodes)
    candidates = list(Y.items())
    with tqdm(total=len(target_nodes), desc="Selecting drivers") as pbar:
        while not target_nodes <= covered:
            candidates.sort(key=lambda x: len(x[1] - covered), reverse=True)
            node, influence = candidates.pop(0)
            newly_covered = influence - covered
            covered.update(newly_covered)
            driver.append(node)
            pbar.update(len(newly_covered))
    return driver

# --- MAIN ---
if __name__ == "__main__":
    input_folder = "./data_4"
    output_folder = "driver_nodes"
    os.makedirs(output_folder, exist_ok=True)

    for input_path in os.listdir(input_folder):
        if not input_path.endswith(".txt"):
            continue

        full_input_path = os.path.join(input_folder, input_path)
        base_filename = os.path.splitext(os.path.basename(full_input_path))[0]

        print(f"\n📥 Đang xử lý file: {base_filename}...")
        G = import_network(full_input_path)

        percent = 5  # Tỉ lệ phần trăm target nodes
        all_nodes = set(G.nodes())
        excluded_nodes = set()
        round_idx = 1

        all_pairs = []

        while excluded_nodes < all_nodes:
            print(f"\n🚀 Vòng lặp {round_idx}: chọn target node...")
            target_nodes = select_target_nodes_non_overlap(G, percent, excluded_nodes)
            if not target_nodes:
                break  # ✅ Dừng nếu không còn thành phần liên thông đủ lớn
            excluded_nodes.update(target_nodes)

            H, K = build_H_K_fast(G, target_nodes)
            Y = compute_Y_fast(H, K)
            drivers = find_driver_nodes_fast(Y, target_nodes)

            all_pairs.append((drivers, target_nodes))
            print(f"✅ Vòng {round_idx}: {len(drivers)} driver nodes cho {len(target_nodes)} target nodes.")

            round_idx += 1

        # Lưu kết quả cho từng file mạng
        paired_results = pd.DataFrame([
            {'Driver_Nodes': drivers, 'Target_Nodes': target_nodes} for drivers, target_nodes in all_pairs
        ])
        if os.path.exists(f"{output_folder}/{base_filename}_pairs.csv"):
            paired_results.to_csv(f"{output_folder}/{base_filename}_pairs.csv", mode='a', header=False, index=False)
        else:
            paired_results.to_csv(f"{output_folder}/{base_filename}_pairs.csv", index=False)
        print(f"🎯 Đã lưu cặp driver-target cho {base_filename} vòng {round_idx - 1} với percent ={percent}!")
