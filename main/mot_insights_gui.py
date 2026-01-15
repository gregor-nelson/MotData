#!/usr/bin/env python3
"""
MOT Insights GUI
================
A simple GUI wrapper for MOT insight generation scripts.
Allows easy generation of make insights and exploration of article opportunities.

Requirements: Python 3.8+ (uses built-in tkinter)
Usage: python mot_insights_gui.py
"""

import json
import sqlite3
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
from pathlib import Path
from datetime import datetime
import sys
import io


# Paths
SCRIPT_DIR = Path(__file__).parent
DB_PATH = SCRIPT_DIR / "mot_insights.db"
DATA_DIR = SCRIPT_DIR / "data"
LOG_DIR = SCRIPT_DIR / "logs"


class MOTInsightsGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("MOT Insights Generator")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)

        # Ensure directories exist
        DATA_DIR.mkdir(exist_ok=True)
        LOG_DIR.mkdir(exist_ok=True)

        # Load makes from database
        self.makes = self._load_makes()

        # Setup UI
        self._setup_styles()
        self._create_widgets()

        # Log startup
        self.log("MOT Insights GUI started")
        self.log(f"Database: {DB_PATH}")
        self.log(f"Found {len(self.makes)} manufacturers")
        self.log("-" * 50)

    def _load_makes(self):
        """Load all makes from database."""
        try:
            conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
            conn.row_factory = sqlite3.Row
            cur = conn.execute("""
                SELECT make, total_tests, avg_pass_rate, rank
                FROM manufacturer_rankings
                ORDER BY total_tests DESC
            """)
            makes = [dict(row) for row in cur.fetchall()]
            conn.close()
            return makes
        except Exception as e:
            messagebox.showerror("Database Error", f"Could not load database:\n{e}")
            return []

    def _setup_styles(self):
        """Configure ttk styles."""
        style = ttk.Style()
        style.configure("Header.TLabel", font=("Segoe UI", 12, "bold"))
        style.configure("Info.TLabel", font=("Segoe UI", 9))
        style.configure("Action.TButton", padding=(10, 5))

    def _create_widgets(self):
        """Create all GUI widgets."""
        # Main container with padding
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        # Create notebook (tabs)
        self.notebook = ttk.Notebook(main)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Generate Make Insights
        self._create_generate_tab()

        # Tab 2: Explore Data
        self._create_explore_tab()

        # Tab 3: Batch Generate
        self._create_batch_tab()

        # Tab 4: View JSON
        self._create_viewer_tab()

        # Bottom: Log output
        self._create_log_panel(main)

    def _create_generate_tab(self):
        """Create the Generate Make Insights tab."""
        tab = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(tab, text="  Generate Insights  ")

        # Header
        ttk.Label(tab, text="Generate Make Insights", style="Header.TLabel").pack(anchor=tk.W)
        ttk.Label(tab, text="Generate comprehensive JSON insights for a specific vehicle manufacturer.",
                  style="Info.TLabel", foreground="gray").pack(anchor=tk.W, pady=(0, 15))

        # Make selection frame
        select_frame = ttk.LabelFrame(tab, text="Select Manufacturer", padding=10)
        select_frame.pack(fill=tk.X, pady=(0, 10))

        # Make dropdown with search
        ttk.Label(select_frame, text="Manufacturer:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))

        self.make_var = tk.StringVar()
        make_values = [f"{m['make']} ({m['total_tests']:,} tests, {m['avg_pass_rate']:.1f}%)"
                       for m in self.makes]
        self.make_combo = ttk.Combobox(select_frame, textvariable=self.make_var,
                                        values=make_values, width=50, state="readonly")
        self.make_combo.grid(row=0, column=1, sticky=tk.W)
        if make_values:
            self.make_combo.current(0)

        # Quick select buttons
        quick_frame = ttk.Frame(select_frame)
        quick_frame.grid(row=1, column=0, columnspan=2, pady=(10, 0), sticky=tk.W)

        ttk.Label(quick_frame, text="Quick select:", foreground="gray").pack(side=tk.LEFT, padx=(0, 10))
        for make in ["TOYOTA", "HONDA", "BMW", "FORD", "VOLKSWAGEN"]:
            btn = ttk.Button(quick_frame, text=make, width=12,
                            command=lambda m=make: self._quick_select_make(m))
            btn.pack(side=tk.LEFT, padx=2)

        # Output options
        output_frame = ttk.LabelFrame(tab, text="Output Options", padding=10)
        output_frame.pack(fill=tk.X, pady=(0, 10))

        self.pretty_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(output_frame, text="Pretty print JSON (human readable)",
                        variable=self.pretty_var).pack(anchor=tk.W)

        self.auto_open_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(output_frame, text="Open output folder after generation",
                        variable=self.auto_open_var).pack(anchor=tk.W)

        # Generate button
        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill=tk.X, pady=10)

        self.generate_btn = ttk.Button(btn_frame, text="Generate Insights",
                                        style="Action.TButton",
                                        command=self._generate_insights)
        self.generate_btn.pack(side=tk.LEFT)

        self.generate_status = ttk.Label(btn_frame, text="", foreground="gray")
        self.generate_status.pack(side=tk.LEFT, padx=15)

        # Info box
        info_frame = ttk.LabelFrame(tab, text="What This Generates", padding=10)
        info_frame.pack(fill=tk.BOTH, expand=True)

        info_text = """The generated JSON includes:

• Overview: Manufacturer rank, total tests, pass rate vs national average
• Competitors: Comparison with similar brands (Toyota vs Honda vs Mazda, etc.)
• Core Models: All models aggregated by family (e.g., all Civic variants combined)
• Year Breakdowns: Year-by-year pass rates for each major model
• Fuel Analysis: Hybrid vs Petrol vs Diesel comparison
• Best/Worst Models: Top 15 best and bottom 10 worst performing variants
• Failure Data: Common failure categories, specific defects, dangerous issues
• Mileage Impact: How pass rate changes with vehicle mileage

Output: data/{make}_insights.json"""

        ttk.Label(info_frame, text=info_text, justify=tk.LEFT).pack(anchor=tk.W)

    def _create_explore_tab(self):
        """Create the Explore Data tab."""
        tab = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(tab, text="  Explore Data  ")

        # Header
        ttk.Label(tab, text="Explore Article Opportunities", style="Header.TLabel").pack(anchor=tk.W)
        ttk.Label(tab, text="Discover interesting data patterns for potential articles.",
                  style="Info.TLabel", foreground="gray").pack(anchor=tk.W, pady=(0, 15))

        # Exploration options
        options_frame = ttk.LabelFrame(tab, text="Select Analysis", padding=10)
        options_frame.pack(fill=tk.X, pady=(0, 10))

        self.explore_analyses = [
            ("best_manufacturers", "Best Manufacturers", "Top 15 most reliable brands by pass rate"),
            ("worst_manufacturers", "Worst Manufacturers", "Bottom 15 least reliable brands"),
            ("best_vehicles", "Best Vehicles", "Top 25 most reliable specific models"),
            ("worst_vehicles", "Worst Vehicles", "Bottom 25 least reliable models (avoid list)"),
            ("hybrid_advantage", "Hybrid Advantage", "Compare hybrid vs petrol vs diesel by brand"),
            ("worst_diesels", "Worst Diesels", "Diesel models with highest failure rates"),
            ("best_first_cars", "Best First Cars", "Reliable small cars for new drivers"),
            ("ev_reliability", "EV Reliability", "Electric vehicle pass rates"),
            ("year_trends", "Year Trends", "Pass rates by model year"),
        ]

        self.explore_var = tk.StringVar(value="best_manufacturers")

        for i, (value, label, desc) in enumerate(self.explore_analyses):
            row = i // 3
            col = i % 3
            frame = ttk.Frame(options_frame)
            frame.grid(row=row, column=col, sticky=tk.W, padx=10, pady=5)
            ttk.Radiobutton(frame, text=label, variable=self.explore_var, value=value).pack(anchor=tk.W)
            ttk.Label(frame, text=desc, font=("Segoe UI", 8), foreground="gray").pack(anchor=tk.W)

        # Run button
        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill=tk.X, pady=10)

        ttk.Button(btn_frame, text="Run Analysis", style="Action.TButton",
                   command=self._run_exploration).pack(side=tk.LEFT)

        ttk.Button(btn_frame, text="Run All Analyses",
                   command=self._run_all_explorations).pack(side=tk.LEFT, padx=10)

        # Results display
        results_frame = ttk.LabelFrame(tab, text="Results", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True)

        self.explore_results = scrolledtext.ScrolledText(results_frame, height=15,
                                                          font=("Consolas", 9))
        self.explore_results.pack(fill=tk.BOTH, expand=True)

    def _create_batch_tab(self):
        """Create the Batch Generate tab."""
        tab = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(tab, text="  Batch Generate  ")

        # Header
        ttk.Label(tab, text="Batch Generate All Priority Makes", style="Header.TLabel").pack(anchor=tk.W)
        ttk.Label(tab, text="Generate insights for multiple high-priority manufacturers at once.",
                  style="Info.TLabel", foreground="gray").pack(anchor=tk.W, pady=(0, 15))

        # Priority makes list
        list_frame = ttk.LabelFrame(tab, text="Priority Makes (select to include)", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Create scrollable checkbox list
        canvas = tk.Canvas(list_frame, height=250)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        self.batch_frame = ttk.Frame(canvas)

        self.batch_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.batch_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Priority makes with checkboxes
        priority_makes = [
            "TOYOTA", "HONDA", "BMW", "FORD", "VOLKSWAGEN", "AUDI", "MERCEDES-BENZ",
            "MAZDA", "KIA", "HYUNDAI", "NISSAN", "VAUXHALL", "MINI", "VOLVO",
            "SUZUKI", "SKODA", "LAND ROVER", "JAGUAR", "LEXUS", "PORSCHE"
        ]

        self.batch_vars = {}
        for i, make in enumerate(priority_makes):
            var = tk.BooleanVar(value=True)
            self.batch_vars[make] = var

            # Find make stats
            stats = next((m for m in self.makes if m['make'] == make), None)
            if stats:
                label = f"{make} ({stats['total_tests']:,} tests, {stats['avg_pass_rate']:.1f}%)"
            else:
                label = make

            row = i // 4
            col = i % 4
            ttk.Checkbutton(self.batch_frame, text=label, variable=var).grid(
                row=row, column=col, sticky=tk.W, padx=10, pady=2)

        # Select all/none buttons
        sel_frame = ttk.Frame(tab)
        sel_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(sel_frame, text="Select All", command=self._select_all_batch).pack(side=tk.LEFT)
        ttk.Button(sel_frame, text="Select None", command=self._select_none_batch).pack(side=tk.LEFT, padx=5)

        # Generate button
        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill=tk.X)

        self.batch_btn = ttk.Button(btn_frame, text="Generate All Selected",
                                     style="Action.TButton", command=self._run_batch)
        self.batch_btn.pack(side=tk.LEFT)

        self.batch_progress = ttk.Progressbar(btn_frame, length=300, mode='determinate')
        self.batch_progress.pack(side=tk.LEFT, padx=15)

        self.batch_status = ttk.Label(btn_frame, text="", foreground="gray")
        self.batch_status.pack(side=tk.LEFT)

    def _create_viewer_tab(self):
        """Create the JSON Viewer tab."""
        tab = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(tab, text="  View JSON  ")

        # Header
        ttk.Label(tab, text="View Generated Insights", style="Header.TLabel").pack(anchor=tk.W)
        ttk.Label(tab, text="Load and preview generated JSON insight files.",
                  style="Info.TLabel", foreground="gray").pack(anchor=tk.W, pady=(0, 15))

        # File selection
        file_frame = ttk.Frame(tab)
        file_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(file_frame, text="Open JSON File", command=self._open_json_file).pack(side=tk.LEFT)
        ttk.Button(file_frame, text="Refresh File List", command=self._refresh_json_list).pack(side=tk.LEFT, padx=5)

        self.json_file_var = tk.StringVar()
        self.json_file_combo = ttk.Combobox(file_frame, textvariable=self.json_file_var,
                                             width=50, state="readonly")
        self.json_file_combo.pack(side=tk.LEFT, padx=10)
        self.json_file_combo.bind("<<ComboboxSelected>>", self._load_selected_json)

        # Summary panel
        summary_frame = ttk.LabelFrame(tab, text="Summary", padding=10)
        summary_frame.pack(fill=tk.X, pady=(0, 10))

        self.json_summary = ttk.Label(summary_frame, text="No file loaded", foreground="gray")
        self.json_summary.pack(anchor=tk.W)

        # JSON content viewer
        content_frame = ttk.LabelFrame(tab, text="JSON Content", padding=10)
        content_frame.pack(fill=tk.BOTH, expand=True)

        self.json_viewer = scrolledtext.ScrolledText(content_frame, height=15,
                                                      font=("Consolas", 9))
        self.json_viewer.pack(fill=tk.BOTH, expand=True)

        # Refresh on tab open
        self._refresh_json_list()

    def _create_log_panel(self, parent):
        """Create the log output panel."""
        log_frame = ttk.LabelFrame(parent, text="Log Output", padding=5)
        log_frame.pack(fill=tk.X, pady=(10, 0))

        # Log text area
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, font=("Consolas", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        # Log buttons
        btn_frame = ttk.Frame(log_frame)
        btn_frame.pack(side=tk.RIGHT, padx=(10, 0), fill=tk.Y)

        ttk.Button(btn_frame, text="Clear", command=self._clear_log, width=8).pack(pady=2)
        ttk.Button(btn_frame, text="Save", command=self._save_log, width=8).pack(pady=2)
        ttk.Button(btn_frame, text="Copy", command=self._copy_log, width=8).pack(pady=2)

    # ========== Actions ==========

    def log(self, message):
        """Add message to log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def _clear_log(self):
        self.log_text.delete(1.0, tk.END)

    def _save_log(self):
        log_file = LOG_DIR / f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(log_file, 'w') as f:
            f.write(self.log_text.get(1.0, tk.END))
        self.log(f"Log saved to {log_file}")

    def _copy_log(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.log_text.get(1.0, tk.END))
        self.log("Log copied to clipboard")

    def _quick_select_make(self, make):
        """Quick select a make from buttons."""
        for i, m in enumerate(self.makes):
            if m['make'] == make:
                self.make_combo.current(i)
                break

    def _get_selected_make(self):
        """Get the currently selected make name."""
        selection = self.make_var.get()
        if selection:
            return selection.split(" (")[0]
        return None

    def _generate_insights(self):
        """Generate insights for selected make."""
        make = self._get_selected_make()
        if not make:
            messagebox.showwarning("No Selection", "Please select a manufacturer.")
            return

        self.generate_btn.config(state=tk.DISABLED)
        self.generate_status.config(text="Generating...")
        self.log(f"Generating insights for {make}...")

        # Run in thread to keep UI responsive
        thread = threading.Thread(target=self._generate_insights_thread, args=(make,))
        thread.start()

    def _generate_insights_thread(self, make):
        """Generate insights in background thread."""
        try:
            from scripts.generate_make_insights import generate_make_insights

            insights = generate_make_insights(make)

            if "error" in insights:
                self.root.after(0, lambda: self.log(f"Error: {insights['error']}"))
                return

            # Save JSON
            output_file = DATA_DIR / f"{make.lower()}_insights.json"
            indent = 2 if self.pretty_var.get() else None

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(insights, f, indent=indent, ensure_ascii=False)

            # Log results
            summary = insights['summary']
            self.root.after(0, lambda: self.log(f"Generated: {output_file.name}"))
            self.root.after(0, lambda: self.log(f"  Tests: {summary['total_tests']:,}"))
            self.root.after(0, lambda: self.log(f"  Pass Rate: {summary['avg_pass_rate']:.1f}%"))
            self.root.after(0, lambda: self.log(f"  Rank: #{summary['rank']} of {summary['rank_total']}"))
            self.root.after(0, lambda: self.log(f"  File size: {output_file.stat().st_size:,} bytes"))

            if self.auto_open_var.get():
                import os
                os.startfile(DATA_DIR)

            self.root.after(0, lambda: self._refresh_json_list())

        except Exception as e:
            self.root.after(0, lambda: self.log(f"Error: {e}"))

        finally:
            self.root.after(0, lambda: self.generate_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.generate_status.config(text="Done"))

    def _run_exploration(self):
        """Run selected exploration analysis."""
        analysis = self.explore_var.get()
        self.log(f"Running analysis: {analysis}")

        # Clear results
        self.explore_results.delete(1.0, tk.END)

        # Run analysis
        result = self._execute_exploration(analysis)
        self.explore_results.insert(tk.END, result)

    def _run_all_explorations(self):
        """Run all exploration analyses."""
        self.log("Running all analyses...")
        self.explore_results.delete(1.0, tk.END)

        for value, label, _ in self.explore_analyses:
            self.explore_results.insert(tk.END, f"\n{'='*60}\n")
            self.explore_results.insert(tk.END, f"  {label.upper()}\n")
            self.explore_results.insert(tk.END, f"{'='*60}\n\n")
            result = self._execute_exploration(value)
            self.explore_results.insert(tk.END, result + "\n")
            self.root.update_idletasks()

        self.log("All analyses complete")

    def _execute_exploration(self, analysis):
        """Execute a specific exploration analysis."""
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row

        output = io.StringIO()

        try:
            if analysis == "best_manufacturers":
                cur = conn.execute("""
                    SELECT make, avg_pass_rate, total_tests, rank, best_model
                    FROM manufacturer_rankings WHERE total_tests >= 50000
                    ORDER BY avg_pass_rate DESC LIMIT 15
                """)
                output.write(f"{'Make':<18} {'Pass %':>8} {'Tests':>12} {'Rank':>6}  Best Model\n")
                output.write("-"*70 + "\n")
                for row in cur:
                    output.write(f"{row['make']:<18} {row['avg_pass_rate']:>7.1f}% {row['total_tests']:>11,} #{row['rank']:>4}  {row['best_model'][:18]}\n")

            elif analysis == "worst_manufacturers":
                cur = conn.execute("""
                    SELECT make, avg_pass_rate, total_tests, rank, worst_model
                    FROM manufacturer_rankings WHERE total_tests >= 10000
                    ORDER BY avg_pass_rate ASC LIMIT 15
                """)
                output.write(f"{'Make':<18} {'Pass %':>8} {'Tests':>12} {'Rank':>6}  Worst Model\n")
                output.write("-"*70 + "\n")
                for row in cur:
                    output.write(f"{row['make']:<18} {row['avg_pass_rate']:>7.1f}% {row['total_tests']:>11,} #{row['rank']:>4}  {row['worst_model'][:18]}\n")

            elif analysis == "best_vehicles":
                cur = conn.execute("""
                    SELECT make, model, model_year, fuel_type, pass_rate, total_tests
                    FROM vehicle_insights WHERE total_tests >= 1000
                    ORDER BY pass_rate DESC LIMIT 25
                """)
                output.write(f"{'Make':<12} {'Model':<20} {'Year':>5} {'Fuel':>4} {'Pass %':>8} {'Tests':>10}\n")
                output.write("-"*70 + "\n")
                for row in cur:
                    output.write(f"{row['make']:<12} {row['model'][:20]:<20} {row['model_year']:>5} {row['fuel_type']:>4} {row['pass_rate']:>7.1f}% {row['total_tests']:>9,}\n")

            elif analysis == "worst_vehicles":
                cur = conn.execute("""
                    SELECT make, model, model_year, fuel_type, pass_rate, total_tests
                    FROM vehicle_insights WHERE total_tests >= 1000
                    ORDER BY pass_rate ASC LIMIT 25
                """)
                output.write(f"{'Make':<12} {'Model':<20} {'Year':>5} {'Fuel':>4} {'Pass %':>8} {'Tests':>10}\n")
                output.write("-"*70 + "\n")
                for row in cur:
                    output.write(f"{row['make']:<12} {row['model'][:20]:<20} {row['model_year']:>5} {row['fuel_type']:>4} {row['pass_rate']:>7.1f}% {row['total_tests']:>9,}\n")

            elif analysis == "hybrid_advantage":
                cur = conn.execute("""
                    SELECT make,
                        SUM(CASE WHEN fuel_type = 'HY' THEN total_tests ELSE 0 END) as hy_tests,
                        ROUND(SUM(CASE WHEN fuel_type = 'HY' THEN total_passes ELSE 0 END) * 100.0 /
                              NULLIF(SUM(CASE WHEN fuel_type = 'HY' THEN total_tests ELSE 0 END), 0), 1) as hy_rate,
                        ROUND(SUM(CASE WHEN fuel_type = 'PE' THEN total_passes ELSE 0 END) * 100.0 /
                              NULLIF(SUM(CASE WHEN fuel_type = 'PE' THEN total_tests ELSE 0 END), 0), 1) as pe_rate,
                        ROUND(SUM(CASE WHEN fuel_type = 'DI' THEN total_passes ELSE 0 END) * 100.0 /
                              NULLIF(SUM(CASE WHEN fuel_type = 'DI' THEN total_tests ELSE 0 END), 0), 1) as di_rate
                    FROM vehicle_insights GROUP BY make HAVING hy_tests >= 1000
                    ORDER BY hy_rate DESC
                """)
                output.write(f"{'Make':<18} {'Hybrid %':>10} {'Petrol %':>10} {'Diesel %':>10} {'Advantage':>10}\n")
                output.write("-"*62 + "\n")
                for row in cur:
                    hy = row['hy_rate'] or 0
                    pe = row['pe_rate'] or 0
                    adv = hy - pe if pe else 0
                    output.write(f"{row['make']:<18} {hy:>9.1f}% {pe:>9.1f}% {row['di_rate'] or 0:>9.1f}% {adv:>+9.1f}%\n")

            elif analysis == "worst_diesels":
                cur = conn.execute("""
                    SELECT make, model, model_year, pass_rate, total_tests
                    FROM vehicle_insights WHERE fuel_type = 'DI' AND total_tests >= 2000
                    ORDER BY pass_rate ASC LIMIT 20
                """)
                output.write(f"{'Make':<12} {'Model':<22} {'Year':>5} {'Pass %':>8} {'Tests':>10}\n")
                output.write("-"*62 + "\n")
                for row in cur:
                    output.write(f"{row['make']:<12} {row['model'][:22]:<22} {row['model_year']:>5} {row['pass_rate']:>7.1f}% {row['total_tests']:>9,}\n")

            elif analysis == "best_first_cars":
                first_cars = [
                    ('FORD', 'FIESTA'), ('VAUXHALL', 'CORSA'), ('VOLKSWAGEN', 'POLO'),
                    ('TOYOTA', 'YARIS'), ('HONDA', 'JAZZ'), ('PEUGEOT', '208'),
                    ('HYUNDAI', 'I10'), ('KIA', 'PICANTO'), ('SUZUKI', 'SWIFT'),
                    ('FIAT', '500'), ('SEAT', 'IBIZA'), ('SKODA', 'FABIA')
                ]
                output.write(f"{'Make':<12} {'Model':<15} {'Year':>5} {'Pass %':>8} {'Tests':>10}\n")
                output.write("-"*55 + "\n")
                for make, model in first_cars:
                    cur = conn.execute("""
                        SELECT model_year, pass_rate, total_tests FROM vehicle_insights
                        WHERE make = ? AND model = ? AND fuel_type = 'PE'
                        AND model_year >= 2015 AND total_tests >= 1000
                        ORDER BY pass_rate DESC LIMIT 1
                    """, (make, model))
                    row = cur.fetchone()
                    if row:
                        output.write(f"{make:<12} {model:<15} {row['model_year']:>5} {row['pass_rate']:>7.1f}% {row['total_tests']:>9,}\n")

            elif analysis == "ev_reliability":
                cur = conn.execute("""
                    SELECT make, model, model_year, pass_rate, total_tests
                    FROM vehicle_insights WHERE fuel_type = 'EL' AND total_tests >= 100
                    ORDER BY pass_rate DESC LIMIT 20
                """)
                output.write(f"{'Make':<12} {'Model':<25} {'Year':>5} {'Pass %':>8} {'Tests':>8}\n")
                output.write("-"*62 + "\n")
                for row in cur:
                    output.write(f"{row['make']:<12} {row['model'][:25]:<25} {row['model_year']:>5} {row['pass_rate']:>7.1f}% {row['total_tests']:>7,}\n")

            elif analysis == "year_trends":
                cur = conn.execute("""
                    SELECT model_year, SUM(total_tests) as tests,
                           ROUND(SUM(total_passes) * 100.0 / SUM(total_tests), 1) as pass_rate
                    FROM vehicle_insights GROUP BY model_year ORDER BY model_year DESC
                """)
                output.write(f"{'Year':>6} {'Pass Rate':>10} {'Tests':>14}\n")
                output.write("-"*35 + "\n")
                for row in cur:
                    bar = "#" * int(row['pass_rate'] / 5)
                    output.write(f"{row['model_year']:>6} {row['pass_rate']:>9.1f}% {row['tests']:>13,}  {bar}\n")

        finally:
            conn.close()

        return output.getvalue()

    def _select_all_batch(self):
        for var in self.batch_vars.values():
            var.set(True)

    def _select_none_batch(self):
        for var in self.batch_vars.values():
            var.set(False)

    def _run_batch(self):
        """Run batch generation for selected makes."""
        selected = [make for make, var in self.batch_vars.items() if var.get()]

        if not selected:
            messagebox.showwarning("No Selection", "Please select at least one manufacturer.")
            return

        self.batch_btn.config(state=tk.DISABLED)
        self.batch_progress['value'] = 0
        self.batch_progress['maximum'] = len(selected)

        self.log(f"Batch generating {len(selected)} makes...")

        thread = threading.Thread(target=self._run_batch_thread, args=(selected,))
        thread.start()

    def _run_batch_thread(self, makes):
        """Run batch generation in background thread."""
        try:
            from scripts.generate_make_insights import generate_make_insights

            success = 0
            failed = []

            for i, make in enumerate(makes):
                self.root.after(0, lambda m=make: self.batch_status.config(text=f"Generating {m}..."))
                self.root.after(0, lambda m=make: self.log(f"  Generating {m}..."))

                try:
                    insights = generate_make_insights(make)

                    if "error" not in insights:
                        output_file = DATA_DIR / f"{make.lower().replace('-', '_')}_insights.json"
                        with open(output_file, 'w', encoding='utf-8') as f:
                            json.dump(insights, f, indent=2, ensure_ascii=False)
                        success += 1
                    else:
                        failed.append(make)

                except Exception as e:
                    failed.append(make)
                    self.root.after(0, lambda e=e: self.log(f"    Error: {e}"))

                self.root.after(0, lambda v=i+1: self.batch_progress.config(value=v))

            self.root.after(0, lambda: self.log(f"Batch complete: {success} success, {len(failed)} failed"))
            if failed:
                self.root.after(0, lambda: self.log(f"  Failed: {', '.join(failed)}"))

            self.root.after(0, lambda: self._refresh_json_list())

        finally:
            self.root.after(0, lambda: self.batch_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.batch_status.config(text="Done"))

    def _refresh_json_list(self):
        """Refresh list of available JSON files."""
        json_files = list(DATA_DIR.glob("*_insights.json"))
        json_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

        file_names = [f.name for f in json_files]
        self.json_file_combo['values'] = file_names

        if file_names:
            self.json_file_combo.current(0)

    def _open_json_file(self):
        """Open a JSON file via file dialog."""
        file_path = filedialog.askopenfilename(
            initialdir=DATA_DIR,
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            self._load_json_file(Path(file_path))

    def _load_selected_json(self, event=None):
        """Load the selected JSON file from dropdown."""
        filename = self.json_file_var.get()
        if filename:
            self._load_json_file(DATA_DIR / filename)

    def _load_json_file(self, file_path):
        """Load and display a JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Update summary
            if 'summary' in data:
                s = data['summary']
                summary = f"{data['meta']['make']}: {s['total_tests']:,} tests, {s['avg_pass_rate']:.1f}% pass rate, Rank #{s['rank']}"
                self.json_summary.config(text=summary, foreground="black")
            else:
                self.json_summary.config(text=file_path.name, foreground="black")

            # Display JSON
            self.json_viewer.delete(1.0, tk.END)
            self.json_viewer.insert(tk.END, json.dumps(data, indent=2, ensure_ascii=False))

            self.log(f"Loaded: {file_path.name}")

        except Exception as e:
            self.json_summary.config(text=f"Error: {e}", foreground="red")
            self.log(f"Error loading {file_path}: {e}")


def main():
    root = tk.Tk()
    app = MOTInsightsGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
