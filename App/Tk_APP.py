# ✅ Tk_APP.py — Unified GUI for Method 3 using tkinter (step-by-step flow with popups)

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import pandas as pd
import sys
sys.path.append(os.path.abspath(".."))
from Simulate.Phase1_Find_Target_And_Driver_Nodes import find_driver_target_pairs
from Simulate.Phase2_Multi_Beta_Simulate_Pair import simulate_from_driver_target_file, import_network
from functions.Compare import match_with_oncokb_pubmed

FONT = ("Segoe UI", 10)
BTN_STYLE = {"font": FONT, "bg": "#E0E0E0", "activebackground": "#D0D0D0", "relief": "raised"}

class Method3App:
    def __init__(self, root):
        self.root = root
        self.root.title("Method 3 — Outside Competitive Dynamics")
        self.root.geometry("1150x700")

        self.graph_path = None
        self.driver_target_path = None
        self.result_df = None
        self.matched_df = None

        self.status_var = tk.StringVar(value="No graph selected")

        self.build_main_ui()

    def build_main_ui(self):
        control_frame = tk.Frame(self.root, padx=15, pady=15, bg="#F5F5F5")
        control_frame.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(control_frame, text="Step-by-step actions", font=("Segoe UI", 11, "bold"), bg="#F5F5F5").pack(anchor="w", pady=(0, 6))

        tk.Button(control_frame, text="📂 Select network file", command=self.choose_graph, **BTN_STYLE).pack(fill="x", pady=4)
        tk.Label(control_frame, textvariable=self.status_var, font=("Segoe UI", 9), fg="blue", bg="#F5F5F5").pack(anchor="w", pady=(0, 10))

        tk.Button(control_frame, text="🔍 Find driver–target pairs", command=self.open_driver_target_window, **BTN_STYLE).pack(fill="x", pady=4)
        tk.Button(control_frame, text="💾 Save result CSV", command=self.save_result, **BTN_STYLE).pack(fill="x", pady=4)
        tk.Button(control_frame, text="🚀 Run simulation", command=self.run_simulation, **BTN_STYLE).pack(fill="x", pady=4)
        tk.Button(control_frame, text="🔁 Match with OncoKB / PubMed", command=self.match_results, **BTN_STYLE).pack(fill="x", pady=4)
        tk.Button(control_frame, text="📥 Save matched results", command=self.save_matched, **BTN_STYLE).pack(fill="x", pady=4)

        self.result_table = ttk.Treeview(self.root, show="headings")
        self.result_table.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    def choose_graph(self):
        path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if path:
            self.graph_path = path
            self.status_var.set(f"Selected: {os.path.basename(path)}")
            messagebox.showinfo("Selected", f"Graph file selected:\n{os.path.basename(path)}")

    def open_driver_target_window(self):
        if not self.graph_path:
            messagebox.showwarning("Missing file", "Please select a graph file first.")
            return

        popup = tk.Toplevel(self.root)
        popup.title("Find Driver–Target Pairs")
        popup.geometry("480x380")

        tk.Label(popup, text="Target ratio (e.g. 0.2):", font=FONT).pack(pady=(10, 3))
        ratio_entry = tk.Entry(popup, font=FONT)
        ratio_entry.insert(0, "0.2")
        ratio_entry.pack(pady=(0, 10))

        tree = ttk.Treeview(popup, show="headings")
        tree.pack(fill=tk.BOTH, expand=True)

        def run_find():
            try:
                ratio = float(ratio_entry.get())
                df = find_driver_target_pairs(self.graph_path, ratio_target=ratio)
                self.driver_target_df = df

                tree.delete(*tree.get_children())
                tree["columns"] = list(df.columns)
                for col in df.columns:
                    tree.heading(col, text=col)
                    tree.column(col, width=220)
                for _, row in df.iterrows():
                    tree.insert("", tk.END, values=list(row))

                if messagebox.askyesno("Save file", "Do you want to save this result to a CSV file?"):
                    self.driver_target_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
                    if self.driver_target_path:
                        df.to_csv(self.driver_target_path, index=False)
                        messagebox.showinfo("Done", f"Saved to:\n{self.driver_target_path}")

            except Exception as e:
                messagebox.showerror("Error", str(e))

        tk.Button(popup, text="Find", command=run_find, **BTN_STYLE).pack(pady=8)

    def run_simulation(self):
        if not self.graph_path or not self.driver_target_path:
            messagebox.showwarning("Missing input", "Please select graph and driver-target file first.")
            return

        popup = tk.Toplevel(self.root)
        popup.title("Simulation Parameters")
        popup.geometry("300x320")

        params = {}
        fields = ["Epsilon", "Delta", "Max Iter", "Tolerance", "N_Beta"]
        defaults = [0.1, 0.2, 50, 1e-4, 2]

        for i, field in enumerate(fields):
            tk.Label(popup, text=field, font=FONT).pack()
            entry = tk.Entry(popup, font=FONT)
            entry.insert(0, str(defaults[i]))
            entry.pack()
            params[field] = entry

        def run():
            try:
                e = float(params["Epsilon"].get())
                d = float(params["Delta"].get())
                mi = int(params["Max Iter"].get())
                tol = float(params["Tolerance"].get())
                nb = int(params["N_Beta"].get())
                df = simulate_from_driver_target_file(self.graph_path, self.driver_target_path, e, d, mi, tol, nb)
                self.result_df = df
                self.display_result(df)
                popup.destroy()
            except Exception as ex:
                messagebox.showerror("Error", str(ex))

        tk.Button(popup, text="Run", command=run, **BTN_STYLE).pack(pady=10)

    def display_result(self, df):
        self.result_table.delete(*self.result_table.get_children())
        self.result_table["columns"] = list(df.columns)
        for col in df.columns:
            self.result_table.heading(col, text=col)
            self.result_table.column(col, width=140)
        for _, row in df.iterrows():
            self.result_table.insert("", tk.END, values=list(row))

    def match_results(self):
        if self.result_df is None:
            messagebox.showwarning("No results", "Please run simulation first.")
            return
        try:
            matched = match_with_oncokb_pubmed(self.result_df)
            matched = matched.sort_values(by="Total_Support", ascending=False)
            self.matched_df = matched
            self.display_result(matched)
        except Exception as e:
            messagebox.showerror("Matching error", str(e))

    def save_result(self):
        if self.result_df is None:
            messagebox.showwarning("No data", "Please run simulation first.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv")
        if path:
            self.result_df.to_csv(path, index=False)
            messagebox.showinfo("Saved", f"Saved results to:\n{path}")

    def save_matched(self):
        if self.matched_df is None:
            messagebox.showwarning("No matched data", "Please run matching first.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv")
        if path:
            self.matched_df.to_csv(path, index=False)
            messagebox.showinfo("Saved", f"Saved matched results to:\n{path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = Method3App(root)
    root.mainloop()
