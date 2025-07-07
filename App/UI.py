# ✅ app.py — giao diện chính sử dụng Phase 1 và Phase 2 (method 3)

import streamlit as st
import pandas as pd
import os
import shutil
import sys; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import matplotlib.pyplot as plt
import networkx as nx
from Simulate.Phase1_Find_Target_And_Driver_Nodes import find_driver_target_pairs
from Simulate.Phase2_Multi_Beta_Simulate_Pair import simulate_from_driver_target_file, import_network
from functions.Compare import match_with_oncokb_pubmed

st.set_page_config(page_title="🎯 Multi-agent OCDM", layout="wide")
st.title("🔬 Multi-agent Outside Competitive Dynamics Model (Method 3)")

st.sidebar.header("⚙️ Simulation Settings")
uploaded_file = st.sidebar.file_uploader("📤 Upload a .txt network file", type=["txt"])

ratio_target = st.sidebar.slider("🎯 % Target Nodes", 1, 50, 20, step=1) / 100
EPSILON = st.sidebar.slider("Epsilon", 0.01, 1.0, 0.1, step=0.01)
DELTA = st.sidebar.slider("Delta", 0.01, 1.0, 0.2, step=0.01)
MAX_ITER = st.sidebar.number_input("Max Iterations", 10, 500, 50)
TOL = st.sidebar.number_input("Tolerance", 1e-6, 1e-2, 1e-4, format="%e")
N_BETA = st.sidebar.slider("Number of Beta per group", 1, 10, 2)

run_phase1 = st.sidebar.button("🔍 Run Phase 1", disabled=(uploaded_file is None))
run_phase2 = st.sidebar.button("🚀 Run Phase 2", disabled=("pair_path" not in st.session_state))

# --- UPLOAD FILE ---
temp_path = None
if uploaded_file:
    st.code(uploaded_file.name)
    os.makedirs("Temp_Upload", exist_ok=True)
    temp_path = os.path.join("Temp_Upload", uploaded_file.name)
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    G = import_network(temp_path)
    st.success(f"✅ Network loaded with {len(G.nodes())} nodes and {len(G.edges())} edges.")
    st.session_state["temp_path"] = temp_path
    st.session_state["graph"] = G
else:
    st.warning("⚠️ Please upload a network file.")

# --- VẼ MẠNG ---
if "graph" in st.session_state and st.button("🧠 Visualize Network"):
    G = st.session_state["graph"]
    pos = nx.spring_layout(G)
    plt.figure(figsize=(6, 4))
    nx.draw(G, pos, with_labels=True, node_size=200, font_size=8)
    st.pyplot(plt)

# --- PHASE 1 ---
if run_phase1 and "temp_path" in st.session_state:
    with st.spinner("🔄 Running driver-target pair finding (Phase 1)..."):
        df_pairs = find_driver_target_pairs(
            graph_path=st.session_state["temp_path"], ratio_target=ratio_target
        )
        pair_path = "Temp_Upload/driver_target_pairs.csv"
        df_pairs.to_csv(pair_path, index=False)
        st.session_state["pair_path"] = pair_path
        st.session_state["phase1_df"] = df_pairs

# --- HIỂN THỊ PHASE 1 ---
if "phase1_df" in st.session_state:
    st.subheader("📁 Phase 1 Result: Driver–Target Pairs")
    st.dataframe(st.session_state["phase1_df"])
    st.download_button(
        "💾 Download Phase 1 Result",
        data=st.session_state["phase1_df"].to_csv(index=False),
        file_name="phase1_driver_target.csv",
        mime="text/csv"
    )

# --- PHASE 2 ---
if run_phase2 and "pair_path" in st.session_state:
    with st.spinner("⚙️ Running simulation (Phase 2)..."):
        result_df = simulate_from_driver_target_file(
            graph_path=st.session_state["temp_path"],
            pair_csv_path=st.session_state["pair_path"],
            EPSILON=EPSILON,
            DELTA=DELTA,
            MAX_ITER=MAX_ITER,
            TOL=TOL,
            N_BETA=N_BETA
        )
        st.session_state["result_df"] = result_df

# --- SHOW RESULTS ---
if "result_df" in st.session_state:
    df = st.session_state["result_df"]
    st.success("✅ Simulation completed.")
    st.subheader("📊 Simulation Result")
    st.dataframe(df)
    st.download_button(
        "⬇️ Download Result CSV",
        data=df.to_csv(index=False),
        file_name="simulation_result.csv",
        mime="text/csv"
    )

    if st.button("🔍 Match with OncoKB and PubMed"):
        matched_df = match_with_oncokb_pubmed(df)
        st.session_state["matched_df"] = matched_df

# --- SHOW MATCHED RESULTS ---
if "matched_df" in st.session_state:
    matched_df = st.session_state["matched_df"]
    st.subheader("🧬 Matched Genes (OncoKB / PubMed)")
    st.dataframe(matched_df.sort_values("Total_Support", ascending=False))
    st.download_button(
        "💾 Download Matched Result",
        data=matched_df.to_csv(index=False),
        file_name="matched_genes.csv",
        mime="text/csv"
    )

# ✅ Cleanup Temp Folder on app shutdown
@st.cache_resource(show_spinner=False)
def _cleanup():
    import atexit
    atexit.register(lambda: shutil.rmtree("Temp_Upload", ignore_errors=True))
_cleanup()
