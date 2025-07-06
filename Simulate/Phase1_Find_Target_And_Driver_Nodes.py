# ✅ Find_target_and_driver_nodes.py — Pha 1 của phương pháp 3: Tìm cặp driver–target
# ✅ Đầu ra là DataFrame các cặp (Driver_Nodes, Target_Nodes), có thể lưu CSV hoặc truyền tiếp pha 2

import networkx as nx
import pandas as pd
import os
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

# ✅ Hàm chọn ngẫu nhiên target nodes dựa trên tỷ lệ %
def select_target_nodes(G, ratio=0.2, seed=42):
    nodes = list(G.nodes())
    random.seed(seed)
    num_targets = max(1, int(len(nodes) * ratio))
    return random.sample(nodes, num_targets)

# ✅ Hàm tìm driver nodes điều khiển được target nodes — dùng thuật toán đơn giản hóa (FVS, BFS, v.v.)
def find_driver_nodes(G, target_nodes):
    # Demo: dùng tất cả các node ngoài target làm driver (có thể thay bằng thuật toán khác sau)
    return [node for node in G.nodes() if node not in target_nodes]

# ✅ Hàm chính: xuất ra DataFrame chứa cặp driver-target

def find_driver_target_pairs(graph_path, ratio_target=0.2):
    G = import_network(graph_path)
    target_nodes = select_target_nodes(G, ratio=ratio_target)
    driver_nodes = find_driver_nodes(G, target_nodes)

    # Chuẩn bị output theo định dạng: Driver_Nodes, Target_Nodes (lưu dưới dạng chuỗi node cách nhau bởi dấu ',')
    driver_str = ",".join(driver_nodes)
    target_str = ",".join(target_nodes)

    df = pd.DataFrame([{"Driver_Nodes": driver_str, "Target_Nodes": target_str}])
    return df

# ✅ Nếu chạy độc lập (dùng thử)
if __name__ == "__main__":
    df = find_driver_target_pairs("../Data/HGRN.txt", ratio_target=0.2)
    df.to_csv("../Output/driver_target_pairs.csv", index=False)
    print("✅ Đã lưu driver-target pairs")
