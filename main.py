# main.py
"""
Main entry point for Bridge Haunch Calculator GUI application
Designed for civil engineers to calculate prestressed concrete girder bridge haunches
"""

import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import traceback
from pathlib import Path

from input_data import BridgeInputs, create_default_inputs
from bridge_haunch_calculator import run_analysis
from create_pdf import master_create_PDF
from config_manager import ConfigManager

class BridgeCalculatorApp:
    def __init__(self):
        """Initialize the Bridge Haunch Calculator application"""
        self.root = tk.Tk()
        self.root.title("NDOT Bridge Haunch Calculator v1.0")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
        # Initialize data managers
        self.config_manager = ConfigManager()
        self.current_inputs = create_default_inputs()
        self.analysis_results = None
        self.current_project_file = None
        
        # Create GUI interface
        self._create_main_interface()
        
        # Setup application components
        self._setup_menu()
        self._setup_status_bar()
        
        # Initialize with default project
        self._load_inputs_to_gui()
    
    def _create_main_interface(self):
        """Create the main tabbed interface for data input"""
        # Create notebook for tabbed input
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create input tabs
        self._create_header_tab()
        self._create_vertical_curve_tab()
        self._create_substructure_tab()
        self._create_bridge_info_tab()
        self._create_prestressing_tab()
    
    def _create_header_tab(self):
        """Create header information input tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Project Info")
        
        # Header input fields
        ttk.Label(frame, text="Project Header Information", font=("Arial", 14, "bold")).pack(pady=10)
        
        input_frame = ttk.Frame(frame)
        input_frame.pack(padx=20, pady=10, fill=tk.BOTH)
        
        self.header_vars = {}
        fields = [
            ("Structure Number:", "structure_number"),
            ("Route Name:", "route_name"), 
            ("Feature Crossed:", "feature_crossed"),
            ("Designer Name:", "designer_name"),
            ("Designer Date:", "designer_date"),
            ("Reviewer Name:", "reviewer_name"),
            ("Reviewer Date:", "reviewer_date")
        ]
        
        for i, (label, var_name) in enumerate(fields):
            ttk.Label(input_frame, text=label).grid(row=i, column=0, sticky=tk.W, pady=5)
            self.header_vars[var_name] = tk.StringVar()
            ttk.Entry(input_frame, textvariable=self.header_vars[var_name], width=30).grid(row=i, column=1, padx=10, pady=5)
    
    def _create_vertical_curve_tab(self):
        """Create vertical curve data input tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Vertical Curve")
        
        ttk.Label(frame, text="Vertical Curve Parameters", font=("Arial", 14, "bold")).pack(pady=10)
        
        input_frame = ttk.Frame(frame)
        input_frame.pack(padx=20, pady=10)
        
        self.vc_vars = {}
        fields = [
            ("VPI Station (ft):", "sta_VPI", "float"),
            ("VPI Elevation (ft):", "elev_VPI", "float"),
            ("Grade 1 (%):", "grade_1", "float"),
            ("Grade 2 (%):", "grade_2", "float"),
            ("Curve Length (ft):", "L_v_curve", "float")
        ]
        
        for i, (label, var_name, data_type) in enumerate(fields):
            ttk.Label(input_frame, text=label).grid(row=i, column=0, sticky=tk.W, pady=5)
            if data_type == "float":
                self.vc_vars[var_name] = tk.DoubleVar()
            else:
                self.vc_vars[var_name] = tk.StringVar()
            ttk.Entry(input_frame, textvariable=self.vc_vars[var_name], width=20).grid(row=i, column=1, padx=10, pady=5)
    
    def _create_substructure_tab(self):
        """Create substructure stations input tab with dynamic span handling"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Substructure")
        
        ttk.Label(frame, text="Substructure Centerline Stations", font=("Arial", 14, "bold")).pack(pady=10)
        
        # Control frame for adding/removing stations
        control_frame = ttk.Frame(frame)
        control_frame.pack(pady=10)
        
        ttk.Button(control_frame, text="Add Station", command=self._add_substructure_station).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Remove Station", command=self._remove_substructure_station).pack(side=tk.LEFT, padx=5)
        
        # Scrollable frame for stations
        canvas = tk.Canvas(frame, height=300)
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=canvas.yview)
        self.sub_frame = ttk.Frame(canvas)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.create_window((0, 0), window=self.sub_frame, anchor=tk.NW)
        
        self.station_vars = []
        self._update_substructure_display()
    
    def _create_bridge_info_tab(self):
        """Create bridge information input tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Bridge Info")
        
        # Create scrollable frame
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.create_window((0, 0), window=scrollable_frame, anchor=tk.NW)
        
        ttk.Label(scrollable_frame, text="Bridge Geometry & Properties", font=("Arial", 14, "bold")).pack(pady=10)
        
        self.bridge_vars = {}
        
        # Bridge geometry section
        geom_frame = ttk.LabelFrame(scrollable_frame, text="Geometry")
        geom_frame.pack(fill=tk.X, padx=20, pady=10)
        
        geom_fields = [
            ("Bridge Skew (deg):", "skew", "float"),
            ("Deck Width (ft):", "deck_width", "float"),
            ("Roadway Width (ft):", "rdwy_width", "float"),
            ("Profile Grade Line", "PGL_line", "float"),
            ("Beam Spacing (ft):", "beam_spa", "float"),
            ("Number of Beams:", "n_beams", "int"),
            ("Roadway Slope:", "rdwy_slope", "float"),
            ("Deck Thickness (in):", "deck_thick", "float"),
            ("Sacrificial Wearing Surface (in):", "sacrificial_ws", "float"),
            ("Turn Width (ft):", "turn_width", "float"),
            ("Bearing Thickness (in):", "brg_thick", "float")
        ]
        
        for i, (label, var_name, data_type) in enumerate(geom_fields):
            ttk.Label(geom_frame, text=label).grid(row=i, column=0, sticky=tk.W, pady=3)
            if data_type == "float":
                self.bridge_vars[var_name] = tk.DoubleVar()
            elif data_type == "int":
                self.bridge_vars[var_name] = tk.IntVar()
            ttk.Entry(geom_frame, textvariable=self.bridge_vars[var_name], width=15).grid(row=i, column=1, padx=10, pady=3)
        
        # Materials section
        materials_frame = ttk.LabelFrame(scrollable_frame, text="Materials")
        materials_frame.pack(fill=tk.X, padx=20, pady=10)
        
            # Beam shape dropdown
        ttk.Label(materials_frame, text="Beam Shape:").grid(row=0, column=0, sticky=tk.W, pady=3)
        self.bridge_vars["beam_shape"] = tk.StringVar()
        beam_shapes = ['NU35', 'NU43', 'NU53', 'NU63', 'NU70', 'NU78']
        ttk.Combobox(materials_frame, textvariable=self.bridge_vars["beam_shape"], 
                    values=beam_shapes, width=12).grid(row=0, column=1, padx=10, pady=3)
        
            # Rail shape dropdown  
        ttk.Label(materials_frame, text="Rail Shape:").grid(row=1, column=0, sticky=tk.W, pady=3)
        self.bridge_vars["rail_shape"] = tk.StringVar()
        rail_shapes = ['39_SSCR', '39_OCR', '42_NU_O', '42_NU_C', '42_NU_M', '34_NU_O', '34_NU_C']
        ttk.Combobox(materials_frame, textvariable=self.bridge_vars["rail_shape"],
                    values=rail_shapes, width=12).grid(row=1, column=1, padx=10, pady=3)
        
            # Concrete Beam Strength Dropdown  
        ttk.Label(materials_frame, text="Beam Strength (fc'):").grid(row=2, column=0, sticky=tk.W, pady=3)
        self.bridge_vars["f_c_beam"] = tk.IntVar()
        f_c_beam_vals = [8, 10]
        ttk.Combobox(materials_frame, textvariable=self.bridge_vars["f_c_beam"],
                    values=f_c_beam_vals, width=12).grid(row=2, column=1, padx=10, pady=3)
        
        ttk.Label(materials_frame, text="Wearing Surface (k/sf):").grid(row=3, column=0, sticky=tk.W, pady=3)
        self.bridge_vars["ws"] = tk.DoubleVar()
        ttk.Entry(materials_frame, textvariable=self.bridge_vars["ws"], width=15).grid(row=3, column=1, padx=10, pady=3)
        
        # Staging section
        staging_frame = ttk.LabelFrame(scrollable_frame, text="Construction Staging")
        staging_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.bridge_vars["staged"] = tk.StringVar()
        ttk.Checkbutton(staging_frame, text="Staged Construction", 
                       variable=self.bridge_vars["staged"], onvalue="yes", offvalue="no").grid(row=0, column=0, sticky=tk.W)
        
            # Stage Start
        ttk.Label(staging_frame, text="Stage Start:").grid(row=1, column=0, sticky=tk.W, pady=3)
        self.bridge_vars["stage_start"] = tk.StringVar()
        ttk.Entry(staging_frame, textvariable=self.bridge_vars["stage_start"], width=15).grid(row=1, column=1, padx=10, pady=3)
        ttk.Label(staging_frame, text="(Looking in Direction of Increasing Stations)").grid(row=1, column=2, sticky=tk.W, pady=3)

        ttk.Label(staging_frame, text="Leftmost Stage Line:").grid(row=2, column=0, sticky=tk.W, pady=3)
        self.bridge_vars["stg_line_lt"] = tk.DoubleVar()
        ttk.Entry(staging_frame, textvariable=self.bridge_vars["stg_line_lt"], width=15).grid(row=2, column=1, padx=10, pady=3)
        ttk.Label(staging_frame, text="(Starting at Left Edge of Deck)").grid(row=2, column=2, sticky=tk.W, pady=3)

        ttk.Label(staging_frame, text="Rightmost Stage Line:").grid(row=3, column=0, sticky=tk.W, pady=3)
        self.bridge_vars["stg_line_rt"] = tk.DoubleVar()
        ttk.Entry(staging_frame, textvariable=self.bridge_vars["stg_line_rt"], width=15).grid(row=3, column=1, padx=10, pady=3)
        ttk.Label(staging_frame, text="(Starting at Left Edge of Deck)").grid(row=3, column=2, sticky=tk.W, pady=3)
        
        # Update canvas scroll region
        scrollable_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
    
    def _create_prestressing_tab(self):
        """Create prestressing configuration tab with dynamic span handling"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Prestressing")
        
        ttk.Label(frame, text="Prestressing Configuration", font=("Arial", 14, "bold")).pack(pady=10)
        ttk.Label(frame, text="Note: Span configurations automatically adjust based on number of substructures", 
                 style="TLabel").pack(pady=5)
        
        # Create scrollable frame for all prestressing configurations
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=canvas.yview)
        self.prestressing_frame = ttk.Frame(canvas)

        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT,fill=tk.Y)
        canvas.create_window((0,0), window=self.prestressing_frame, anchor=tk.NW)

        self.span_config_vars = []

        # Bind scroll region update
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        self.prestressing_frame.bind('<Configure>', on_frame_configure)
    
    def _add_substructure_station(self):
        """Add a new substructure station"""
        self.station_vars.append(tk.DoubleVar())
        self._update_substructure_display()
        self._update_prestressing_spans()
    
    def _remove_substructure_station(self):
        """Remove the last substructure station"""
        if len(self.station_vars) > 2:  # Must have at least 2 stations
            self.station_vars.pop()
            self._update_substructure_display()
            self._update_prestressing_spans()
    
    def _update_substructure_display(self):
        """Update the substructure stations display"""
        # Clear existing widgets
        for widget in self.sub_frame.winfo_children():
            widget.destroy()
        
        # Create station input fields
        for i, var in enumerate(self.station_vars):
            station_type = "Abutment 1" if i == 0 else f"Pier {i}" if i < len(self.station_vars) - 1 else "Abutment 2"
            ttk.Label(self.sub_frame, text=f"{station_type} Station (ft):").grid(row=i, column=0, sticky=tk.W, pady=3)
            ttk.Entry(self.sub_frame, textvariable=var, width=15).grid(row=i, column=1, padx=10, pady=3)
        
        self.sub_frame.update_idletasks()
    
    def _update_prestressing_spans(self):
        """Update prestressing configuration based on number of spans"""
        num_spans = len(self.station_vars) - 1
        
        # Clear existing prestressing configuration
        for widget in self.prestressing_frame.winfo_children():
            widget.destroy()
        
        # Adjust span configuration variables
        while len(self.span_config_vars) < num_spans:
            self.span_config_vars.append(self._create_default_span_vars())
        while len(self.span_config_vars) > num_spans:
            self.span_config_vars.pop()
        
        # Create span configuration interfaces
        for i in range(num_spans):
            self._create_span_config_interface(i)
    
    def _create_default_span_vars(self):
        """Create default variables for a span configuration"""
        return {
            'straight_strands': [tk.IntVar(value=val) for val in [0, 0, 0, 0, 0, 0, 0]],
            'strand_dist_bot': [tk.DoubleVar(value=val) for val in [2, 4, 6, 8, 10, 12, 14]],
            'debond_vars': {
                f'row_{i+1}': {
                    'configs': [{'strands': tk.IntVar(value=0), 'lengths': tk.DoubleVar(value=0)}]
                } for i in range(7)
            },
            'harp_length_factor': tk.DoubleVar(value=0.4),
            'harp_vars': {
                f'row_{i+1}': {
                    'depth': tk.DoubleVar(value=0),
                    'harped': tk.BooleanVar(value=False)
                } for i in range(7)
            }
        }
    
    def _create_span_config_interface(self, span_idx):
        """Create interface for individual span prestressing configuration"""
        span_frame = ttk.LabelFrame(self.prestressing_frame, text=f"Span {span_idx + 1}")
        span_frame.pack(fill=tk.X, pady=10)

        # Create notebook for organized sections
        span_notebook = ttk.Notebook(span_frame)
        span_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Straight Strands Tab
        straight_frame = ttk.Frame(span_notebook)
        span_notebook.add(straight_frame, text="Straight Strands")

        ttk.Label(straight_frame, text="Straight Strands per Row:").grid(row=0, column=0, sticky=tk.W, pady=5)
        strand_frame = ttk.Frame(straight_frame)
        strand_frame.grid(row=0, column=1, padx=10, sticky=tk.W)
        
        strand_entries = []
        for i, var in enumerate(self.span_config_vars[span_idx]['straight_strands']):
            entry = ttk.Entry(strand_frame, textvariable=var, width=5)
            entry.pack(side=tk.LEFT, padx=2)
            entry.bind('<KeyRelease>', lambda e, si=span_idx: self.update_strand_dependencies(si))
            strand_entries.append(entry)

        # Strand distances
        ttk.Label(straight_frame, text="Distance from Bottom (in):").grid(row=1, column=0, sticky=tk.W, pady=5)
        dist_frame = ttk.Frame(straight_frame)
        dist_frame.grid(row=1, column=1, padx=10, sticky=tk.W)

        for i, var in enumerate(self.span_config_vars[span_idx]['strand_dist_bot']):
            ttk.Entry(dist_frame, textvariable=var, width=5).pack(side=tk.LEFT, padx=2)

        # Debonded Strands Tab
        debond_frame = ttk.Frame(span_notebook)
        span_notebook.add(debond_frame, text="Debonded Strands")
        self._create_debond_section(debond_frame, span_idx)
        
        # Harped Strands Tab
        harp_frame = ttk.Frame(span_notebook)
        span_notebook.add(harp_frame, text="Harped Strands")
        self._create_harp_section(harp_frame, span_idx)
    
    def _create_debond_section(self, parent, span_idx):
        """Create debonded strands configuration section"""
        # Header
        ttk.Label(parent, text="Debond Strand Configuration", font=("Arial", 12, "bold")).pack(pady=(10,5))
        ttk.Label(parent, text="Note: Only rows with straight strands can be debonded", 
                  font=("Arial", 9, "italic")).pack(pady=(0,10))

        # Create scrollable frame for debond rows
        canvas = tk.Canvas(parent, height=300)
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=canvas.yview)
        debond_content = ttk.Frame(canvas)

        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.create_window((0,0), window=debond_content, anchor=tk.NW)

        # Column headers
        header_frame = ttk.Frame(debond_content)
        header_frame.pack(fill=tk.X, pady=(0,5))

        ttk.Label(header_frame, text="Row", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=5, sticky=tk.W)
        ttk.Label(header_frame, text="Strands", font=("Arial", 10, "bold")).grid(row=0, column=1, padx=5, sticky=tk.W)
        ttk.Label(header_frame, text="Length (ft)", font=("Arial", 10, "bold")).grid(row=0, column=2, padx=5, sticky=tk.W)
        ttk.Label(header_frame, text="Actions", font=("Arial", 10, "bold")).grid(row=0, column=3, padx=5, sticky=tk.W)

        # Create debond row interfaces
        self.debond_row_frames = {}
        for row_idx in range(7):
            self._create_debond_row(debond_content, span_idx, row_idx)

        # Update canvas scroll region
        debond_content.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
    
    def _create_debond_row(self, parent, span_idx, row_idx):
        """Create interface for a single debond row"""
        row_frame = ttk.Frame(parent)
        row_frame.pack(fill=tk.X, pady=2)

        row_key = f"span_{span_idx}_row_{row_idx}"
        self.debond_row_frames[row_key] = row_frame

        # Row label
        row_label = ttk.Label(row_frame, text=f"R{row_idx + 1}:")
        row_label.grid(row=0, column=0, padx=5, sticky=tk.W)

        # container for debond configurations
        config_frame = ttk.Frame(row_frame)
        config_frame.grid(row=0, column=1, columnspan=3, sticky=tk.W, padx=5)

        self._update_debond_row_display(span_idx, row_idx, config_frame)

    def _update_debond_row_display(self, span_idx, row_idx, config_frame):
        """Update the display of debond configurations for a row"""
        # Clear existing widgets
        for widget in config_frame.winfo_children():
            widget.destroy()

        debond_vars = self.span_config_vars[span_idx]['debond_vars'][f'row_{row_idx + 1}']

        # Check if row has striaght strands
        straight_strands = self.span_config_vars[span_idx]['straight_strands'][row_idx].get()
        row_enabled = straight_strands > 0

        for config_idx, config in enumerate(debond_vars['configs']):
            config_row_frame = ttk.Frame(config_frame)
            config_row_frame.pack(fill=tk.X, pady=1)

            # Strands entry
            strands_entry = ttk.Entry(config_row_frame, textvariable=config['strands'], width=8)
            strands_entry.pack(side=tk.LEFT, padx=2)
            strands_entry.config(state='normal' if row_enabled else 'disabled')

            # Length entry
            length_entry = ttk.Entry(config_row_frame, textvariable=config['lengths'], width=8)
            length_entry.pack(side=tk.LEFT, padx=2)
            length_entry.config(state='normal' if row_enabled else 'disabled')

            # Add button (only show for last config or if this isn't the only one)
            if config_idx == len(debond_vars['configs']) - 1:
                add_btn = ttk.Button(config_row_frame, text="Add Debond", width=12, 
                                     command=lambda si=span_idx, ri=row_idx: self._add_debond_config(si, ri))
                add_btn.pack(side=tk.LEFT, padx=2)
                add_btn.config(state='normal' if row_enabled else 'disabled')

            # Remove button (only show if more than one config)
            if len(debond_vars['configs']) > 1:
                remove_btn = ttk.Button(config_row_frame, text="Remove", width=8, 
                                        command=lambda si=span_idx, ri=row_idx, ci=config_idx: self._remove_debond_config(si, ri, ci))
                remove_btn.pack(side=tk.LEFT, padx=2)
                remove_btn.config(state='normal' if row_enabled else 'disabled')

        # Update row styling based on enabled state
        if not row_enabled:
          config_frame.config(style='Disabled.TFrame')
          for widget in config_frame.winfo_children():
              self._apply_disabled_style(widget)

    def _add_debond_config(self, span_idx, row_idx):
        """Add a new debond configuration to a row"""
        debond_vars = self.span_config_vars[span_idx]['debond_vars'][f'row_{row_idx + 1}']
        debond_vars['configs'].append({
            'strands': tk.IntVar(value=0),
            'lengths': tk.DoubleVar(value=0)
        })

        # Refresh the debond display
        self._refresh_debond_display(span_idx)

    def _remove_debond_config(self, span_idx, row_idx, config_idx):
        """Remove a debond configuration from a row"""
        debond_vars = self.span_config_vars[span_idx]['debond_vars'][f'row_{row_idx+1}']
        if len(debond_vars['configs']) > 1:
            debond_vars['configs'].pop(config_idx)

            # refresh the debond display
            self._refresh_debond_display(span_idx)

    def _refresh_debond_display(self, span_idx):
        """Refresh the entire debond display for a span"""
        # Find the debond frame and recreate it
        for widget in self.prestressing_frame.winfo_children():
            if isinstance(widget, ttk.LabelFrame) and f"Span {span_idx + 1}" in widget.cget('text'):
                # Find the notebook within this span frame
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Notebook):
                        # find the debond tab
                        for tab_id in child.tabs():
                            if child.tab(tab_id, 'text') == 'Debonded Strands':
                                debond_frame = child.nametowidget(tab_id)
                                # clear and recreate
                                for debond_child in debond_frame.winfo_children():
                                    debond_child.destroy()
                                self._create_debond_section(debond_frame, span_idx)
                                break
                        break
                break
    
    def _create_harp_section(self, parent, span_idx):
        """Create harped strands configuration section"""
        # Header and harping length factor
        ttk.Label(parent, text="Harped Strand Configuration", font=("Arial", 12, "bold")).pack(pady=(10, 5))
        ttk.Label(parent, text="Note: Only rows with straight strands can be harped", 
                  font=("Arial", 9, "italic")).pack(pady=(0, 10))
        
        # Harping Length factor
        factor_frame = ttk.Frame(parent)
        factor_frame.pack(pady=5)
        ttk.Label(factor_frame, text="Harping Length Factor:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(factor_frame, textvariable=self.span_config_vars[span_idx]['harp_length_factor'], 
                  width=10).pack(side=tk.LEFT, padx=5)

        # Column headers
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, pady=(20,5))

        ttk.Label(header_frame, text="Row", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=5, sticky=tk.W)
        ttk.Label(header_frame, text="Depth (in)", font=("Arial", 10, "bold")).grid(row=0, column=1, padx=5, sticky=tk.W)
        ttk.Label(header_frame, text="Harped?", font=("Arial", 10, "bold")).grid(row=0, column=2, padx=5, sticky=tk.W)

        # Create harp row interfaces
        content_frame = ttk.Frame(parent)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10)

        for row_idx in range(7):
            self._create_harp_row(content_frame, span_idx, row_idx)

    def _create_harp_row(self, parent, span_idx, row_idx):
        """Create interface for a single harp row"""
        harp_vars = self.span_config_vars[span_idx]['harp_vars'][f'row_{row_idx + 1}']

        # Check if row has striaght strands
        straight_strands = self.span_config_vars[span_idx]['straight_strands'][row_idx].get()
        row_enabled = straight_strands > 0

        row_frame = ttk.Frame(parent)
        row_frame.pack(fill=tk.X, pady=2)

        # Row label
        ttk.Label(row_frame, text=f"R{row_idx + 1}:").grid(row=0, column=0, padx=5, sticky=tk.W)

        # Depth Entry
        depth_entry = ttk.Entry(row_frame, textvariable=harp_vars['depth'], width=10)
        depth_entry.grid(row=0, column=1, padx=5, sticky=tk.W)
        depth_entry.config(state='normal' if row_enabled and harp_vars['harped'].get() else 'disabled')

        # Harped checkbox
        harped_check = ttk.Checkbutton(row_frame, variable=harp_vars['harped'], 
                                       command=lambda si=span_idx, ri=row_idx: self._on_harp_toggle(si, ri))
        harped_check.grid(row=0, column=2, padx=5, sticky=tk.W)
        harped_check.config(state='normal' if row_enabled else 'disabled')

        # Apply disabled styling if needed
        if not row_enabled:
            row_frame.config(style='Disabled.TFrame')
            self._apply_disabled_style(row_frame)

    def _on_harp_toggle(self, span_idx, row_idx):
        """Handle harped checkbox toggle"""
        harp_vars = self.span_config_vars[span_idx]['harp_vars'][f'row_{row_idx + 1}']

        # Find the depth entry and enable/disable it
        for widget in self.prestressing_frame.winfo_children():
            # Navigate to find the specific depth entry and update its state
            self._update_harp_row_state(widget, span_idx, row_idx)
            break

    def _update_harp_row_state(self, span_widget, span_idx, row_idx):
        """Update the state of harp row components"""
        harp_vars = self.span_config_vars[span_idx]['harp_vars'][f'row_{row_idx + 1}']
        straight_strands = self.span_config_vars[span_idx]['straight_strands'][row_idx].get()

        # Navigate through widget hierarchy to find the depth entry
        # This is a simplified version - in practice you'd need more robust widget finding
        depth_enabled = straight_strands > 0 and harp_vars['harped'].get()

        # Update entry state (implementation depends on your specific widget structure)
        # This would need to be implemented based on the actual widget hierarchy
        
    def _refresh_harp_display(self, span_idx):
        """Refresh the harp display for a span"""
        # Similar to refresh_debond_display for for harp section
        for widget in self.prestressing_frame.winfo_children():
            if isinstance(widget, ttk.LabelFrame) and f"Span {span_idx + 1}" in widget.cget('text'):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Notebook):
                        for tab_id in child.tabs():
                            if child.tab(tab_id, 'text') == 'Harped Strands':
                                harp_frame = child.nametowidget(tab_id)
                                # Clear and recreate
                                for harp_child in harp_frame.winfo_children():
                                    harp_child.destroy()
                                self._create_harp_section(harp_frame, span_idx)
                                break
                        break
                break

    def _update_strand_dependencies(self, span_idx):
        """Update debond and harp sections when striaght strands values change"""
        # Refresh debond display
        self._refresh_debond_display(span_idx)

        # Refresh harp display
        self._refresh_harp_display(span_idx)
    
    def _apply_disabled_style(self, widget):
        """Apply disabled styling to a widget and its children"""
        try:
            if hasattr(widget, 'configure'):
                if isinstance(widget, (ttk.Entry, ttk.Button, ttk.Checkbutton)):
                    widget.configure(state='disabled')
                elif isinstance(widget, ttk.Frame):
                    widget.configure(style='Disabled.TFrame')

            # Apply to children recursively
            for child in widget.winfo_children():
                self._apply_disabled_style(child)
        except tk.TclError:
            pass # ignore styling errors
    
    def _setup_menu(self):
        """Create application menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Project", command=self.new_project, accelerator="Ctrl+N")
        file_menu.add_command(label="Open Project...", command=self.open_project, accelerator="Ctrl+O")
        file_menu.add_command(label="Save Project", command=self.save_project, accelerator="Ctrl+S")
        file_menu.add_command(label="Save Project As...", command=self.save_project_as, accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Analysis menu
        analysis_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Analysis", menu=analysis_menu)
        analysis_menu.add_command(label="Run Analysis", command=self.run_analysis, accelerator="F5")
        analysis_menu.add_command(label="Generate PDF Report", command=self.generate_pdf, accelerator="Ctrl+P")
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="User Manual", command=self.show_help)
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self.show_about)
        
        # Keyboard shortcuts
        self.root.bind('<Control-n>', lambda e: self.new_project())
        self.root.bind('<Control-o>', lambda e: self.open_project())
        self.root.bind('<Control-s>', lambda e: self.save_project())
        self.root.bind('<F5>', lambda e: self.run_analysis())
        self.root.bind('<Control-p>', lambda e: self.generate_pdf())
    
    def _setup_status_bar(self):
        """Create status bar with progress indicator"""
        status_frame = ttk.Frame(self.root)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_bar = ttk.Label(
            status_frame, 
            text="Ready - Load or create a bridge project to begin", 
            relief=tk.SUNKEN, 
            anchor=tk.W
        )
        self.status_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.progress_bar = ttk.Progressbar(
            status_frame, 
            mode='indeterminate',
            length=200
        )
        self.progress_bar.pack(side=tk.RIGHT, padx=5)
    
    def update_status(self, message: str, show_progress=False):
        """Update status bar message and optionally show progress"""
        self.status_bar.config(text=message)
        if show_progress:
            self.progress_bar.start()
        else:
            self.progress_bar.stop()
        self.root.update_idletasks()
    
    def _get_inputs_from_gui(self):
        """Extract current inputs from GUI and create BridgeInputs object"""
        from input_data import HeaderInfo, VerticalCurveData, SubstructureData, BridgeInfo, SpanConfig, DebondConfig, HarpConfig
        
        # Extract header information
        header = HeaderInfo(
            structure_number=self.header_vars["structure_number"].get(),
            route_name=self.header_vars["route_name"].get(),
            feature_crossed=self.header_vars["feature_crossed"].get(),
            designer_name=self.header_vars["designer_name"].get(),
            designer_date=self.header_vars["designer_date"].get(),
            reviewer_name=self.header_vars["reviewer_name"].get(),
            reviewer_date=self.header_vars["reviewer_date"].get()
        )
        
        # Extract vertical curve data
        vertical_curve = VerticalCurveData(
            sta_VPI=self.vc_vars["sta_VPI"].get(),
            elev_VPI=self.vc_vars["elev_VPI"].get(),
            grade_1=self.vc_vars["grade_1"].get(),
            grade_2=self.vc_vars["grade_2"].get(),
            L_v_curve=self.vc_vars["L_v_curve"].get()
        )
        
        # Extract substructure stations
        stations = [var.get() for var in self.station_vars]
        substructure = SubstructureData(sta_CL_sub=stations)
        
        # Extract bridge information
        bridge_info = BridgeInfo(
            skew=self.bridge_vars["skew"].get(),
            turn_width=self.bridge_vars["turn_width"].get(),
            deck_width=self.bridge_vars["deck_width"].get(),
            rdwy_width=self.bridge_vars["rdwy_width"].get(),
            beam_spa=self.bridge_vars["beam_spa"].get(),
            n_beams=self.bridge_vars["n_beams"].get(),
            rdwy_slope=self.bridge_vars["rdwy_slope"].get(),
            deck_thick=self.bridge_vars["deck_thick"].get(),
            sacrificial_ws=self.bridge_vars["sacrificial_ws"].get(),
            beam_shape=self.bridge_vars["beam_shape"].get(),
            f_c_beam=self.bridge_vars["f_c_beam"].get(),
            f_c_i_beam=self.bridge_vars["f_c_i_beam"].get(),
            rail_shape=self.bridge_vars["rail_shape"].get(),
            staged=self.bridge_vars["staged"].get(),
            ws=self.bridge_vars["ws"].get()
        )
        
        # Extract prestressing configurations
        span_configs = []
        for span_vars in self.span_config_vars:
            debond_config, harp_config = self._extract_debond_harp_configs(span_vars['span_idx'])
            
            span_config = SpanConfig(
                straight_strands=[var.get() for var in span_vars['straight_strands']],
                strand_dist_bot=[var.get() for var in span_vars['strand_dist_bot']],
                debond_config=debond_config,
                harp_config=harp_config
            )
            span_configs.append(span_config)
        
        return BridgeInputs(
            header=header,
            vertical_curve=vertical_curve,
            substructure=substructure,
            bridge_info=bridge_info,
            span_configs=span_configs
        )
    
    def _extract_debond_harp_configs(self, span_idx):
        """Extract debond and harp configurations for a span"""
        from input_data import DebondConfig, HarpConfig

        span_vars = self.span_config_vars[span_idx]

        # Extract debond configurations
        debond_configs = []
        for row_idx in range(7):
            row_key = f'row_{row_idx + 1}'
            debond_vars = span_vars['debond_vars'][row_key]

            # Check if row has any debond configurations with non-zero values
            strands_list = []
            lengths_list = []

            for config in debond_vars['configs']:
                strands_val = config['strands'].get()
                lengths_val = config['lengths'].get()
                if strands_val > 0 and lengths_val > 0:
                    strands_list.append(strands_val)
                    lengths_list.append(lengths_val)

            if strands_list: # Only add if there are actual debond values
                debond_configs.append(DebondConfig(row=row_idx + 1, strands=strands_list, lengths=lengths_list))

        # If no debond configs, add default
        if not debond_configs:
            debond_configs = [DebondConfig(row=1, strands=[0], lengths=[0]),
                              DebondConfig(row=2, strands=[0], lengths=[0])]

        # Extract harp configurations
        harped_strands = []
        harped_depths = []

        for row_idx in range(7):
            row_key = f'row_{row_idx + 1}'
            harp_vars = span_vars['harp_vars'][row_key]

            if harp_vars['harped'].get():
                harped_strands.append(2)  # Always 2 strands per harped row
                harped_depths.append(harp_vars['depth'].get())
            else:
                harped_strands.append(0)
                harped_depths.append(0)

        harp_config = HarpConfig(
            strands=harped_strands,
            harped_depths=harped_depths,
            harping_length_factor=span_vars['harp_length_factor'].get()
        )

        return debond_configs, harp_config
    
    def _load_inputs_to_gui(self):
        """Load BridgeInputs object data into GUI fields"""
        inputs = self.current_inputs
        
        # Load header information
        self.header_vars["structure_number"].set(inputs.header.structure_number)
        self.header_vars["route_name"].set(inputs.header.route_name)
        self.header_vars["feature_crossed"].set(inputs.header.feature_crossed)
        self.header_vars["designer_name"].set(inputs.header.designer_name)
        self.header_vars["designer_date"].set(inputs.header.designer_date)
        self.header_vars["reviewer_name"].set(inputs.header.reviewer_name)
        self.header_vars["reviewer_date"].set(inputs.header.reviewer_date)
        
        # Load vertical curve data
        self.vc_vars["sta_VPI"].set(inputs.vertical_curve.sta_VPI)
        self.vc_vars["elev_VPI"].set(inputs.vertical_curve.elev_VPI)
        self.vc_vars["grade_1"].set(inputs.vertical_curve.grade_1)
        self.vc_vars["grade_2"].set(inputs.vertical_curve.grade_2)
        self.vc_vars["L_v_curve"].set(inputs.vertical_curve.L_v_curve)
        
        # Load substructure stations
        self.station_vars = [tk.DoubleVar(value=station) for station in inputs.substructure.sta_CL_sub]
        self._update_substructure_display()
        self._update_prestressing_spans()
        
        # Load bridge information
        bridge_info = inputs.bridge_info
        self.bridge_vars["skew"].set(bridge_info.skew)
        self.bridge_vars["deck_width"].set(bridge_info.deck_width)
        self.bridge_vars["rdwy_width"].set(bridge_info.rdwy_width)
        self.bridge_vars["PGL_loc"].set(bridge_info.PGL_loc)
        self.bridge_vars["beam_spa"].set(bridge_info.beam_spa)
        self.bridge_vars["n_beams"].set(bridge_info.n_beams)
        self.bridge_vars["rdwy_slope"].set(bridge_info.rdwy_slope)
        self.bridge_vars["deck_thick"].set(bridge_info.deck_thick)
        self.bridge_vars["sacrificial_ws"].set(bridge_info.sacrificial_ws)
        self.bridge_vars["turn_width"].set(bridge_info.turn_width)
        self.bridge_vars["brg_thick"].set(bridge_info.brg_thick)
        self.bridge_vars["beam_shape"].set(bridge_info.beam_shape)
        self.bridge_vars["rail_shape"].set(bridge_info.rail_shape)
        self.bridge_vars["f_c_beam"].set(bridge_info.f_c_beam)
        self.bridge_vars["ws"].set(bridge_info.ws)
        self.bridge_vars["staged"].set(bridge_info.staged)
        self.bridge_vars["stage_start"].set(bridge_info.stage_start)
        self.bridge_vars["stg_line_lt"].set(bridge_info.stg_line_lt)
        self.bridge_vars["stg_line_rt"].set(bridge_info.stg_line_rt)
    
    def new_project(self):
        """Create new project with default values"""
        if messagebox.askyesno("New Project", "Create new project? Unsaved changes will be lost."):
            self.current_inputs = create_default_inputs()
            self.analysis_results = None
            self.current_project_file = None
            self._load_inputs_to_gui()
            self.update_status("New project created - Enter bridge parameters and run analysis")
    
    def open_project(self):
        """Open project from file"""
        filename = filedialog.askopenfilename(
            title="Open Bridge Project",
            filetypes=[("JSON Project files", "*.json"), ("All files", "*.*")],
            initialdir="."
        )
        
        if filename:
            try:
                inputs = self.config_manager.load_config(filename)
                if inputs:
                    self.current_inputs = inputs
                    self.current_project_file = filename
                    self.analysis_results = None  # Clear previous results
                    self._load_inputs_to_gui()
                    self.update_status(f"Project loaded: {Path(filename).name}")
                else:
                    messagebox.showerror("Error", "Failed to load project file - invalid format")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load project file:\n{str(e)}")
    
    def save_project(self):
        """Save current project"""
        if self.current_project_file:
            self._save_to_file(self.current_project_file)
        else:
            self.save_project_as()
    
    def save_project_as(self):
        """Save project with new filename"""
        filename = filedialog.asksaveasfilename(
            title="Save Bridge Project",
            defaultextension=".json",
            filetypes=[("JSON Project files", "*.json"), ("All files", "*.*")],
            initialdir="."
        )
        
        if filename:
            self._save_to_file(filename)
            self.current_project_file = filename
    
    def _save_to_file(self, filename):
        """Save current inputs to specified file"""
        try:
            # Get current inputs from GUI
            current_inputs = self._get_inputs_from_gui()
            
            if self.config_manager.save_config(current_inputs, filename):
                self.update_status(f"Project saved: {Path(filename).name}")
                messagebox.showinfo("Success", f"Project saved successfully to:\n{filename}")
            else:
                messagebox.showerror("Error", "Failed to save project file")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save project:\n{str(e)}")
    
    def run_analysis(self):
        """Run comprehensive bridge haunch analysis"""
        try:
            self.update_status("Preparing analysis...", show_progress=True)
            
            # Get current inputs from GUI
            current_inputs = self._get_inputs_from_gui()
            
            # Validate inputs
            errors = current_inputs.validate()
            if errors:
                error_msg = "Please correct the following input errors:\n\n" + "\n".join(f"• {error}" for error in errors)
                messagebox.showerror("Input Validation Errors", error_msg)
                self.update_status("Analysis cancelled - input validation failed")
                return
            
            self.update_status("Running structural analysis...", show_progress=True)
            
            # Run analysis using bridge_haunch_calculator
            analysis_results = run_analysis(current_inputs)
            
            # Store results
            self.analysis_results = analysis_results
            self.current_inputs = current_inputs
            
            # Update status
            self.update_status("Analysis completed successfully - Generate PDF for detailed results")
            
            # Show results summary
            self._show_results_summary(analysis_results)
            
        except Exception as e:
            error_msg = f"Analysis failed due to calculation error:\n\n{str(e)}\n\nPlease check input parameters and try again."
            messagebox.showerror("Analysis Error", error_msg)
            self.update_status("Analysis failed - check inputs and try again")
            print(f"Analysis error details: {traceback.format_exc()}")  # For debugging
    
    def generate_pdf(self):
        """Generate comprehensive PDF engineering report"""
        if not hasattr(self, 'analysis_results') or self.analysis_results is None:
            messagebox.showwarning("No Results", "No analysis results available.\n\nPlease run analysis first before generating PDF.")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Save Bridge Analysis Report",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            initialdir="."
        )
        
        if filename:
            try:
                self.update_status("Generating PDF report...", show_progress=True)
                
                # Generate PDF using create_pdf module
                master_create_PDF(self.current_inputs, self.analysis_results)
                
                # Move generated PDF to desired location if different
                import shutil
                generated_pdf = "Bridge Deflections.pdf"  # Default name from create_pdf
                if filename != generated_pdf and Path(generated_pdf).exists():
                    shutil.move(generated_pdf, filename)
                
                self.update_status(f"PDF report generated: {Path(filename).name}")
                
                # Ask user if they want to open the PDF
                if messagebox.askyesno("PDF Generated", 
                                     f"PDF report generated successfully!\n\nLocation: {filename}\n\nWould you like to open it now?"):
                    import os
                    os.startfile(filename)  # Windows
                    # For cross-platform: subprocess.run(['xdg-open', filename])  # Linux
                    # subprocess.run(['open', filename])  # macOS
                
            except Exception as e:
                error_msg = f"PDF generation failed:\n\n{str(e)}\n\nPlease try again or contact support."
                messagebox.showerror("PDF Generation Error", error_msg)
                self.update_status("PDF generation failed")
                print(f"PDF error details: {traceback.format_exc()}")  # For debugging
    
    def _show_results_summary(self, results):
        """Display analysis results summary in popup window"""
        summary_window = tk.Toplevel(self.root)
        summary_window.title("Bridge Analysis Results Summary")
        summary_window.geometry("700x500")
        summary_window.resizable(True, True)
        
        # Create main frame with scrollbar
        main_frame = ttk.Frame(summary_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Results text display
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD, font=("Consolas", 10))
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Format and display results
        summary_text = self._format_results_summary(results)
        text_widget.insert(tk.END, summary_text)
        text_widget.config(state=tk.DISABLED)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Generate PDF Report", 
                  command=lambda: [summary_window.destroy(), self.generate_pdf()]).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", 
                  command=summary_window.destroy).pack(side=tk.RIGHT, padx=5)
    
    def _format_results_summary(self, results) -> str:
        """Format analysis results for display to civil engineers"""
        summary = "BRIDGE HAUNCH ANALYSIS RESULTS\n"
        summary += "=" * 60 + "\n\n"
        
        # Bridge geometry summary
        spans = results.beam_layout_obj.span
        summary += f"Bridge Configuration:\n"
        summary += f"  Number of Spans: {len(spans)}\n"
        for i, span_length in enumerate(spans):
            summary += f"    Span {i+1}: {span_length:.2f} ft\n"
        summary += f"  Beam Type: {self.current_inputs.bridge_info.beam_shape}\n"
        summary += f"  Number of Beams: {self.current_inputs.bridge_info.n_beams}\n"
        summary += f"  Deck Width: {self.current_inputs.bridge_info.deck_width:.1f} ft\n\n"
        
        # Analysis convergence
        final_results = results.final_haunch_obj
        summary += f"Haunch Design Analysis:\n"
        summary += f"  Convergence: {'✓ Converged' if final_results.iter < 50 else '⚠ Max iterations reached'}\n"
        summary += f"  Iterations Required: {final_results.iter}\n"
        
        # Minimum camber check
        min_check = results.min_haunch_check_obj
        summary += f"  Minimum Camber Check: {'✓ Positive' if min_check.check == 'Positive' else '⚠ Negative - Review Design'}\n\n"
        
        # Critical haunch values
        summary += f"Maximum Variable Haunch Heights by Beam:\n"
        for beam in range(self.current_inputs.bridge_info.n_beams):
            max_haunch = 0
            for span in range(len(spans)):
                span_start = int(results.stations_obj.s[:span].sum()) if span > 0 else 0
                span_end = int(results.stations_obj.s[:span+1].sum())
                beam_col = 2 * beam + 1  # Right flange line
                span_max = max(final_results.var_haunch_i[span_start:span_end, beam_col]) * 12  # Convert to inches
                max_haunch = max(max_haunch, span_max)
            summary += f"  Beam {beam+1}: {max_haunch:.2f} inches\n"
        
        # Bearing seat elevations
        summary += f"\nBearing Seat Elevations:\n"
        seat_elevs = results.seat_obj.seat_elev
        for i in range(len(spans)):
            structure_name = "Abutment 1" if i == 0 else f"Pier {i}"
            summary += f"  {structure_name}:\n"
            for beam in range(self.current_inputs.bridge_info.n_beams):
                summary += f"    Beam {beam+1}: {seat_elevs[2*i, beam]:.2f} ft\n"
        
        # Add final structure
        summary += f"  {'Abutment 2' if len(spans) == 1 else f'Pier {len(spans)}' if len(spans) > 1 else 'Abutment 2'}:\n"
        for beam in range(self.current_inputs.bridge_info.n_beams):
            summary += f"    Beam {beam+1}: {seat_elevs[-1, beam]:.2f} ft\n"
        
        summary += "\n" + "=" * 60 + "\n"
        summary += "Analysis completed successfully.\n"
        summary += "Generate PDF report for comprehensive engineering documentation.\n"
        
        return summary
    
    def show_help(self):
        """Display user manual/help information"""
        help_text = """BRIDGE HAUNCH CALCULATOR - USER GUIDE

WORKFLOW:
1. Enter project information in each tab
2. Configure substructure stations (determines number of spans)
3. Set bridge geometry and material properties
4. Configure prestressing for each span
5. Run Analysis (F5)
6. Generate PDF Report (Ctrl+P)

INPUT TABS:
• Project Info: Structure identification and design team
• Vertical Curve: Grade line geometry parameters  
• Substructure: Station locations (controls span count)
• Bridge Info: Beam type, deck dimensions, materials
• Prestressing: Strand configuration per span

KEYBOARD SHORTCUTS:
• Ctrl+N: New Project
• Ctrl+O: Open Project  
• Ctrl+S: Save Project
• F5: Run Analysis
• Ctrl+P: Generate PDF

For technical support, contact NDOT Bridge Division."""
        
        help_window = tk.Toplevel(self.root)
        help_window.title("User Manual")
        help_window.geometry("600x500")
        
        text_widget = tk.Text(help_window, wrap=tk.WORD, padx=10, pady=10)
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert(tk.END, help_text)
        text_widget.config(state=tk.DISABLED)
        
        ttk.Button(help_window, text="Close", command=help_window.destroy).pack(pady=10)
    
    def show_about(self):
        """Show application information dialog"""
        about_text = """NDOT Bridge Haunch Calculator v1.0

A comprehensive tool for designing prestressed concrete 
girder bridge haunches and generating detailed engineering 
reports for NDOT bridge projects.

Calculates:
• Prestressed beam camber and deflections
• Variable haunch requirements  
• Bearing seat elevations
• Construction staging effects

Developed for Nebraska Department of Transportation
Bridge Division structural engineers."""
        
        messagebox.showinfo("About Bridge Haunch Calculator", about_text)
    
    def run(self):
        """Start the application main loop"""
        try:
            # Center window on screen
            self.root.update_idletasks()
            width = self.root.winfo_width()
            height = self.root.winfo_height()
            x = (self.root.winfo_screenwidth() // 2) - (width // 2)
            y = (self.root.winfo_screenheight() // 2) - (height // 2)
            self.root.geometry(f"{width}x{height}+{x}+{y}")
            
            self.root.mainloop()
        except KeyboardInterrupt:
            self.root.quit()
        except Exception as e:
            messagebox.showerror("Application Error", f"Unexpected application error:\n{str(e)}")

if __name__ == "__main__":
    app = BridgeCalculatorApp()
    app.run()
