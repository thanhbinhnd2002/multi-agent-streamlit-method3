# 🔬 Multi-agent Outside Competitive Dynamics Model — Streamlit Interface (Method 3)

This project implements **Phase 1 + Phase 2** of the Method 3 pipeline for simulating outside competitive dynamics on biological gene networks. It provides a full-featured **Streamlit-based interface** to select parameters, perform simulations, and validate gene targets against real-world databases.

---

## 📆 Features

* Upload custom gene network `.txt`
* Choose % of target nodes + hyperparameters (`epsilon`, `delta`, `n_beta`, etc.)
* Automatically performs:
  * **Phase 1**: Select target nodes and infer matching driver nodes
  * **Phase 2**: Multi-agent simulation with external Beta nodes
* Match final results with **OncoKB** and **PubMed**
* Download results (raw + matched) as `.csv`

---

## 📁 File Structure

```
App/
├── UI.py                             # Streamlit interface
Simulate/
├── Phase1_Find_Target_And_Driver_Nodes.py   # Phase 1: driver–target finder
├── Phase2_Multi_Beta_Simulate_Pair.py       # Phase 2: simulation from pairs
functions/
├── Compare.py                        # Matching with OncoKB / PubMed
```

---

## ⚙️ Installation

### 📥 Install Anaconda (Recommended)

1. Download from [https://www.anaconda.com/products/distribution](https://www.anaconda.com/products/distribution)
2. On **Windows**, check *Add to PATH* during installation
3. On **Linux/macOS**, follow CLI instructions
4. Verify:

```bash
conda --version
```

### Step 1: Clone the repository

```bash
git clone git@github.com:thanhbinhnd2002/multi-agent-streamlit-method3.git
cd multi-agent-streamlit-method3
```

### Step 2: Setup environment

```bash
conda create -n multi_beta_env python=3.8
conda activate multi_beta_env
```

### Step 3: Install dependencies

```bash
pip install -r requirements.txt
```

> Note: Save `requirements.txt` as UTF-8 with BOM if Unicode errors appear on Windows

---

## 🚀 Run the App

```bash
cd App
streamlit run UI.py
```

Then open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 📄 Input Format

Upload a **tab-separated** `.txt` file with format:

```
source\ttarget\tdirection\tweight
```

* `direction`: 0 = bidirectional, 1 = directed

**Example:**

```
TP53	MDM2	1	0.9
BRCA1	TP53	0	1.0
```

---

## 🧪 Parameters

* **% Target Nodes**: % of nodes selected as targets
* **Epsilon (ε)**: internal update weight
* **Delta (δ)**: Beta influence
* **N_BETA**: number of Beta nodes per group
* **MAX_ITER / TOL**: convergence controls

---

## 🧬 Matching (Biological Validation)

Cross-reference simulation output using:

* **OncoKB**: curated cancer gene database
* **PubMed**: biomedical literature (via symbol + alias matching)

Implemented in `functions/Compare.py`.

---

## 📤 Output

* Simulation results: `(Alpha_Node, Total_Support)`
* Match results: `(Gene, OncoKB matched, PubMedID, etc)`
* Downloadable in `.csv` format from the UI

---

## 👨‍💻 Author

Developed by **Phạm Thành Bình** @HUST — 2025

For academic and research use only.

🔗 GitHub: [https://github.com/thanhbinhnd2002](https://github.com/thanhbinhnd2002)
