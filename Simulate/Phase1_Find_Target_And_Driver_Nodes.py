# ✅ Find_target_and_driver_nodes.py — Pha 1 của phương pháp 3 (đã sửa lại logic đúng)
# ✅ Tìm nhiều cặp (Driver_Nodes, Target_Nodes) qua nhiều vòng lặp như code gốc

import networkx as nx
import pandas as pd
import random

# ✅ Hàm đọc mạng từ file .txt
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

# ✅ Hàm chọn tập target mới không giao với các target đã chọn trước đó

def select_target_nodes_non_overlap(G, ratio, excluded_nodes, seed=42):
    random.seed(seed)
    available_nodes = list(set(G.nodes()) - excluded_nodes)
    num_targets = max(1, int(len(G.nodes()) * ratio))
    if len(available_nodes) <= num_targets:
        return available_nodes
    return random.sample(available_nodes, num_targets)

# ✅ Tìm driver nodes đơn giản: tất cả node không thuộc target

def find_driver_nodes(G, target_nodes):
    return [node for node in G.nodes() if node not in target_nodes]

# ✅ Hàm chính: lặp nhiều vòng chọn (D,T) không giao nhau và trả về DataFrame

def find_driver_target_pairs(graph_path, ratio_target=0.2):
    G = import_network(graph_path)
    all_nodes = set(G.nodes())
    excluded_nodes = set()
    round_idx = 1
    all_pairs = []

    while excluded_nodes < all_nodes:
        target_nodes = select_target_nodes_non_overlap(G, ratio_target, excluded_nodes)
        if not target_nodes:
            break
        excluded_nodes.update(target_nodes)
        driver_nodes = find_driver_nodes(G, target_nodes)

        driver_str = ",".join(driver_nodes)
        target_str = ",".join(target_nodes)
        all_pairs.append({"Driver_Nodes": driver_str, "Target_Nodes": target_str})
        round_idx += 1

    df = pd.DataFrame(all_pairs)
    return df

# ✅ Nếu chạy độc lập
if __name__ == "__main__":
    df = find_driver_target_pairs("../Data/HGRN.txt", ratio_target=0.05)
    df.to_csv("../Output/driver_target_pairs.csv", index=False)
    print("✅ Đã lưu driver-target pairs theo nhiều vòng lặp không giao nhau")
