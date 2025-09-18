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

DEFAULT_STRAND_DISTANCES = [2, 4, 6, 8, 10, 12, 14]
STRAND_CONSTRAINTS = {
    1: list(range(0, 19, 2)),
    2: list(range(0, 19, 2)),
    3: list(range(0, 13, 2)),
    4: list(range(0, 7, 2)),
    5: list(range(0, 3, 2)),
    6: list(range(0, 3, 2)),
    7: list(range(0, 3, 2)),
}

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
        self.widget_registry = {}
    
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
            ("Profile Grade Line (ft)", "PGL_loc", "float"),
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
                       variable=self.bridge_vars["staged"], onvalue="yes", offvalue="no", 
                        command=self._update_stage_var_display).grid(row=0, column=0, sticky=tk.W)
        
            # Stage Start
        ttk.Label(staging_frame, text="Stage Start:").grid(row=1, column=0, sticky=tk.W, pady=3)
        self.bridge_vars["stage_start"] = tk.StringVar()
        self.stage_start_combo = ttk.Combobox(staging_frame, textvariable=self.bridge_vars["stage_start"], 
                     values=['left', 'right'], width=15, state='disabled')
        self.stage_start_combo.grid(row=1, column=1, padx=10, pady=3)
        ttk.Label(staging_frame, text="(Looking in Direction of Increasing Stations)").grid(row=1, column=2, sticky=tk.W, pady=3)
            
            # Left Stage Line
        ttk.Label(staging_frame, text="Leftmost Stage Line:").grid(row=2, column=0, sticky=tk.W, pady=3)
        self.bridge_vars["stg_line_lt"] = tk.DoubleVar()
        self.stg_line_lt_entry = ttk.Entry(staging_frame, textvariable=self.bridge_vars["stg_line_lt"], width=15, state='disabled')
        self.stg_line_lt_entry.grid(row=2, column=1, padx=10, pady=3)
        ttk.Label(staging_frame, text="(Measured from Left Edge of Deck)").grid(row=2, column=2, sticky=tk.W, pady=3)
            
            # Right Stage Line
        ttk.Label(staging_frame, text="Rightmost Stage Line:").grid(row=3, column=0, sticky=tk.W, pady=3)
        self.bridge_vars["stg_line_rt"] = tk.DoubleVar()
        self.stg_line_rt_entry = ttk.Entry(staging_frame, textvariable=self.bridge_vars["stg_line_rt"], width=15, state='disabled')
        self.stg_line_rt_entry.grid(row=3, column=1, padx=10, pady=3)
        ttk.Label(staging_frame, text="(Measured from Left Edge of Deck)").grid(row=3, column=2, sticky=tk.W, pady=3)
        
        # Update canvas scroll region
        scrollable_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))

    def _update_stage_var_display(self):
        is_staged = self.bridge_vars["staged"].get() == "yes"
        state = 'normal' if is_staged else 'disabled'

        self.stage_start_combo.config(state=state)
        self.stg_line_lt_entry.config(state=state)
        self.stg_line_rt_entry.config(state=state)

        if not is_staged:
            self.bridge_vars["stage_start"].set("")
            self.bridge_vars["stg_line_lt"].set(0.0)
            self.bridge_vars["stg_line_rt"].set(0.0)
                    
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
        
        #span_config_update_btn = ttk.Button(frame, text="Update Prestressing Configuration", 
        #                                    command=self._update_prestressing_spans)
        #span_config_update_btn.pack(side=tk.TOP, fill=tk.X, expand=False, padx=10, pady=10)
        
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
            'midspan_strands': [tk.IntVar(value=0) for _ in range(7)],
            'row_enabled': [tk.BooleanVar(value=False) for _ in range(7)],
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
            },
            'widget_refs': {
                'strand_dropdowns': {},
                'debond_entries': {},
                'harp_checkboxes': {},
                'harp_depth_entries': {}
            }
        }
    
    def _create_span_config_interface(self, span_idx):
        """Create interface for individual span prestressing configuration"""
        span_frame = ttk.LabelFrame(self.prestressing_frame, text=f"Span {span_idx + 1}")
        span_frame.pack(fill=tk.X, pady=10)

        # Create notebook for organized sections
        span_notebook = ttk.Notebook(span_frame)
        span_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Midspan Strands Tab
        midspan_frame = ttk.Frame(span_notebook)
        span_notebook.add(midspan_frame, text="Midspan Strands")
        
        content_frame = ttk.Frame(midspan_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Headers
        ttk.Label(content_frame, text="Row", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=5, sticky=tk.W)
        ttk.Label(content_frame, text="Distance from Bottom (in)", font=("Arial", 10, "bold")).grid(row=0, column=1, padx=5, sticky=tk.W)
        ttk.Label(content_frame, text="Midspan Strands", font=("Arial", 10, "bold")).grid(row=0, column=2, padx=5, sticky=tk.W)
        ttk.Label(content_frame, text="Enable Row", font=("Arial", 10, "bold")).grid(row=0, column=3, padx=5, sticky=tk.W)
        
        widget_refs = self.span_config_vars[span_idx]['widget_refs']
        
        # Create row entries with dropdowns
        for i in range(7):
            row_num = i + 1
            
            # Row Label
            ttk.Label(content_frame, text=f"R{row_num}:").grid(row=row_num, column=0, padx=5, sticky=tk.W)
            
            # Distance (constant, display only)
            ttk.Label(content_frame, text=f"{DEFAULT_STRAND_DISTANCES[i]}").grid(row=row_num, column=1, padx=5, sticky=tk.W)
            
            # Strand count dropdown
            strand_var = self.span_config_vars[span_idx]['midspan_strands'][i]
            strand_dropdown = ttk.Combobox(content_frame, textvariable=strand_var, 
                                           values=STRAND_CONSTRAINTS[row_num], 
                                           width=8, state='disabled')
            strand_dropdown.grid(row=row_num, column=2, padx=5, sticky=tk.W)
            widget_refs['strand_dropdowns'][i] = strand_dropdown

            # Enable checkbox
            enable_var = self.span_config_vars[span_idx]['row_enabled'][i]
            enable_checkbox = ttk.Checkbutton(content_frame, variable=enable_var, 
                                              command=lambda si=span_idx,ri=i:self._on_row_enable_toggle(si,ri))
            enable_checkbox.grid(row=row_num, column=3, padx=5, sticky=tk.W)
        
        self._create_debond_section_with_refs(span_notebook, span_idx)
        self._create_harp_section_with_refs(span_notebook, span_idx)
        
    def _create_debond_section_with_refs(self, notebook, span_idx):
        debond_frame = ttk.Frame(notebook)
        notebook.add(debond_frame, text="Debonded Strands")

        ttk.Label(debond_frame, text="Debond Strand Configuration", font=("Arial", 12, "bold")).pack(pady=(10,5))
        ttk.Label(debond_frame, text="Multiple debond configurations can be added per row", font=("Arial", 10, "italic")).pack(pady=(0,10))

        canvas = tk.Canvas(debond_frame, height=400)
        scrollbar = ttk.Scrollbar(debond_frame, orient=tk.VERTICAL, command=canvas.yview)
        content_frame = ttk.Frame(canvas)

        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.create_window((0,0), window=content_frame, anchor=tk.NW)

        # Headers
        header_frame = ttk.Frame(content_frame)
        header_frame.pack(fill=tk.X, pady=(0,10))
        ttk.Label(header_frame, text="Row", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=5, sticky=tk.W)
        ttk.Label(header_frame, text="Strands", font=("Arial", 10, "bold")).grid(row=0, column=1, padx=5, sticky=tk.W)
        ttk.Label(header_frame, text="Length (ft)", font=("Arial", 10, "bold")).grid(row=0, column=2, padx=5, sticky=tk.W)
        ttk.Label(header_frame, text="Add", font=("Arial", 10, "bold")).grid(row=0, column=3, padx=5, sticky=tk.W)
        ttk.Label(header_frame, text="Remove", font=("Arial", 10, "bold")).grid(row=0, column=3, padx=5, sticky=tk.W)

        # Store references for direct access
        widget_refs = self.span_config_vars[span_idx]['widget_refs']
        widget_refs['debond_entries'] = {}
        widget_refs['debond_frames'] = {}
        
        for row_idx in range(7):
            self._create_debond_row_interface(content_frame, span_idx, row_idx)

        def update_scroll_region():
            content_frame.update_idletasks()
            canvas.configure(scrollregion=canvas.bbox("all"))

        content_frame.bind('<Configure>', lambda e: update_scroll_region())
        self.root.after(100, update_scroll_region)
    
    def _create_debond_row_interface(self, parent, span_idx, row_idx):
        row_main_frame = ttk.Frame(parent)
        row_main_frame.pack(fill=tk.X, pady=5)

        widget_refs = self.span_config_vars[span_idx]['widget_refs']
        widget_refs['debond_frames'][row_idx] = row_main_frame

        self._update_debond_row_interface(span_idx, row_idx)
        
    def _update_debond_row_interface(self, span_idx, row_idx):
        widget_refs = self.span_config_vars[span_idx]['widget_refs']
        row_main_frame = widget_refs['debond_frames'][row_idx]

        for widget in row_main_frame.winfo_children():
            widget.destroy()

        row_key = f'row_{row_idx+1}'
        debond_configs = self.span_config_vars[span_idx]['debond_vars'][row_key]['configs']

        row_enabled = self.span_config_vars[span_idx]['row_enabled'][row_idx].get()

        widget_refs['debond_entries'][row_idx] = []

        for config_idx, config in enumerate(debond_configs):
            config_frame = ttk.Frame(row_main_frame)
            config_frame.pack(fill=tk.X, pady=1)
            if config_idx == 0:
                row_label = ttk.Label(config_frame, text=f"R{row_idx+1}:")
                row_label.grid(row=0, column=0, padx=5, sticky=tk.W, rowspan=len(debond_configs))
            else:
                ttk.Label(config_frame, text="").grid(row=0, column=0, padx=5, sticky=tk.W)

            strands_entry = ttk.Entry(config_frame, textvariable=config['strands'],
                                      width=8, state='normal' if row_enabled else 'disabled')
            strands_entry.grid(row=0, column=1, padx=5, sticky=tk.W)
            length_entry = ttk.Entry(config_frame, textvariable=config['lengths'],
                                     width=8, state='normal' if row_enabled else 'disabled')
            length_entry.grid(row=0, column=2, padx=5, sticky=tk.W)

            widget_refs['debond_entries'][row_idx].extend([strands_entry, length_entry])
            if config_idx == len(debond_configs) - 1:
                add_btn = ttk.Button(config_frame, text="Add Row", width=8, 
                                     command=lambda si=span_idx, ri=row_idx,: self_add_debond_config(si, ri), 
                                     state='normal' if row_enabled else 'disabled')
                add_btn.grid(row=0, column=3, padx=5, sticky=tk.W)
            else:
                ttk.Label(config_frame, text="").grid(row=0, column=3, padx=5, sticky=tk.W)
            if len(debond_configs) > 1:
                remove_btn = ttk.Button(config_frame, text="Remove", width=8,
                           command=lambda si=span_idx, ri=row_idx, ci=config_idx: self._remove_debond_config(si, ri, ci),
                           state='normal' if row_enabled else 'disabled')
                remove_btn.grid(row=0, column=4, padx=5, sticky=tk.W)
            else:
                ttk.Label(config_frame, text="").grid(row=0, column=4, padx=5, sticky=tk.W)
    
    def _add_debond_config(self, span_idx, row_idx):
        row_key = f'row_{row_idx+1}'
        debond_configs = self.span_config_vars[span_idx]['debond_vars'][row_key]['configs']
        new_config = {
            'strands': tk.IntVar(value=0),
            'lengths': tk.Double(value=0.0)
        }
        debond_configs.append(new_config)
        self._update_debond_row_interface(span_idx, row_idx)
        self._update_debond_scroll_region(span_idx)

    def _remove_debond_config(self, span_idx, row_idx, config_idx):
        row_key = f'row_{row_idx+1}'
        debond_configs = self.span_config_vars[span_idx]['debond_vars'][row_key]['configs']
        if len(debond_configs) > 1:
            debond_configs.pop(config_idx)
            self._update_debond_row_interface(span_idx, row_idx)
            self._update_debond_scroll_region(span_idx)

    def _update_debond_scroll_region(self, span_idx):
        widget_refs = self.span_config_vars[span_idx]['widget_refs']
        if 'debond_frames' in widget_refs and widget_refs['debond_frames']:
            first_frame = widget_refs['debond_frames'][0]
            parent = first_frame
            while parent and not isinstance(parent, tk.Canvas):
                parent = parent.winfo_parent()
                if parent:
                    parent = first_frame.nametowidget(parent)
            if parent and isinstance(parent, tk.Canvas):
                parent.update_idletasks()
                content_frame = None
                for child in parent.winfo_children():
                    if isinstance(child, ttk.Frame):
                        content_frame = child
                        break
                if content_frame:
                    content_frame.update_idletasks()
                    parent.configure(scrollregion=parent.bbox("all"))
    
    def _create_harp_section_with_refs(self, notebook, span_idx):
        harp_frame = ttk.Frame(notebook)
        notebook.add(harp_frame, text="Harped Strands")

        ttk.Label(harp_frame, text="Harped Strand Configuration", font=("Arial", 12, "bold")).pack(pady=(10,5))
        
        factor_frame = ttk.Frame(harp_frame)
        factor_frame.pack(pady=5)
        ttk.Label(factor_frame, text="Harping Length Factor:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(factor_frame, textvariable=self.span_config_vars[span_idx]['harp_length_factor'], 
                  width=10).pack(side=tk.LEFT, padx=5)
        content_frame = ttk.Frame(harp_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        ttk.Label(content_frame, text="Row", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=5, sticky=tk.W)
        ttk.Label(content_frame, text="Depth (in)", font=("Arial", 10, "bold")).grid(row=0, column=1, padx=5, sticky=tk.W)
        ttk.Label(content_frame, text="Harped?", font=("Arial", 10, "bold")).grid(row=0, column=2, padx=5, sticky=tk.W)
        widget_refs = self.span_config_vars[span_idx]['widget_refs']
        widget_refs['harp_checkboxes'] = {}
        widget_refs['harp_depth_entries'] = {}
        for row_idx in range(7):
            ttk.Label(content_frame, text=f"R{row_idx + 1}:").grid(row=row_idx+1,column=0, padx=5, sticky=tk.W)
            depth_var = self.span_config_vars[span_idx]['harp_vars'][f'row_{row_idx+1}']['depth']
            depth_entry = ttk.Entry(content_frame, textvariable=depth_var, width=10, state='disabled')
            depth_entry.grid(row=row_idx+1, column=1, padx=5, sticky=tk.W)
            widget_refs['harp_depth_entries'][row_idx] = depth_entry
            
            harp_var = self.span_config_vars[span_idx]['harp_vars'][f'row_{row_idx+1}']['harped']
            harp_checkbox = ttk.Checkbutton(content_frame, variable=harp_var, state='disabled', 
                                    command=lambda si=span_idx, ri=row_idx: self._update_harp_depth_state(si, ri))
            harp_checkbox.grid(row=row_idx+1, column=2, padx=5, sticky=tk.W)
            widget_refs['harp_checkboxes'][row_idx] = harp_checkbox
    
    def _on_row_enable_toggle(self, span_idx, row_idx):
        try:
            enabled = self.span_config_vars[span_idx]['row_enabled'][row_idx].get()
            widget_refs = self.span_config_vars[span_idx]['widget_refs']
            
            strand_dropdown = widget_refs['strand_dropdowns'].get(row_idx)
            if strand_dropdown and strand_dropdown.winfo_exists():
                strand_dropdown.configure(state='readonly' if enabled else 'disabled')
                if not enabled:
                    self.span_config_vars[span_idx]['midspan_strands'][row_idx].set(0)
            
            if not enabled:
                row_key = f'row_{row_idx+1}'
                debond_configs = self.span_config_vars[span_idx]['debond_vars'][row_key]['configs']
                debond_configs.clear()
                debond_configs.append({
                    'strands': tk.IntVar(value=0),
                    'lengths': tk.DoubleVar(value=0.0)
                })
                self._update_debond_row_interface(span_idx, row_idx)
            else:
                self._update_debond_row_interface(span_idx, row_idx)
            
            harp_checkbox = widget_refs['harp_checkboxes'].get(row_idx)
            if harp_checkbox and harp_checkbox.winfo_exists():
                harp_checkbox.configure(state='normal' if enabled else 'disabled')
                if not enabled:
                    self.span_config_vars[span_idx]['harp_vars'][f'row_{row_idx+1}']['harped'].set(False)
            self._update_harp_depth_state(span_idx, row_idx)
        except Exception as e:
            messagebox.showerror(f"Error", "Toggle Error: {e}")

    def _update_harp_depth_state(self, span_idx, row_idx):
        """Update the state of harp row components"""
        try:
            row_enabled = self.span_config_vars[span_idx]['row_enabled'][row_idx].get()
            harp_checked = self.span_config_vars[span_idx]['harp_vars'][f'row_{row_idx+1}']['harped'].get()
            depth_enabled = row_enabled and harp_checked
            depth_entry = self.span_config_vars[span_idx]['widget_refs']['harp_depth_entries'].get(row_idx)
            if depth_entry and depth_entry.winfo_exists():
                depth_entry.configure(state='normal' if depth_enabled else 'disabled')
                if not depth_enabled:
                    depth_entry.delete(0, tk.END)
                    depth_entry.insert(0, '0')
                    
        except Exception as e:
            messagebox.showerror(f"Error", "{e}")
    
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
            deck_width=self.bridge_vars["deck_width"].get(),
            rdwy_width=self.bridge_vars["rdwy_width"].get(),
            PGL_loc=self.bridge_vars["PGL_loc"].get(),
            beam_spa=self.bridge_vars["beam_spa"].get(),
            n_beams=self.bridge_vars["n_beams"].get(),
            rdwy_slope=self.bridge_vars["rdwy_slope"].get(),
            deck_thick=self.bridge_vars["deck_thick"].get(),
            sacrificial_ws=self.bridge_vars["sacrificial_ws"].get(),
            turn_width=self.bridge_vars["turn_width"].get(),
            brg_thick=self.bridge_vars["brg_thick"].get(),
            beam_shape=self.bridge_vars["beam_shape"].get(),
            rail_shape=self.bridge_vars["rail_shape"].get(),
            f_c_beam=self.bridge_vars["f_c_beam"].get(),
            ws=self.bridge_vars["ws"].get(),
            staged=self.bridge_vars["staged"].get(),
            stage_start=self.bridge_vars["stage_start"].get(),
            stg_line_lt=self.bridge_vars["stg_line_lt"].get(),
            stg_line_rt=self.bridge_vars["stg_line_rt"].get()
        )
        
        # Extract prestressing configurations
        span_configs = []
        for i, span_vars in enumerate(self.span_config_vars):
            debond_config, harp_config = self._extract_debond_harp_configs(i)
            
            span_config = SpanConfig(
                midspan_strands=[var.get() for var in span_vars['midspan_strands']],
                strand_dist_bot=DEFAULT_STRAND_DISTANCES,
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
        if not hasattr(self, 'current_inputs'):
            from input_data import create_default_inputs
            self.current_inputs = create_default_inputs()
            
        inputs = self.current_inputs
        
        # Load header information
        for key, var in self.header_vars.items():
            var.set(getattr(inputs.header, key))
        
        # Load vertical curve data
        for key, var in self.vc_vars.items():
            var.set(getattr(inputs.vertical_curve, key))
        
        # Load substructure stations
        self.station_vars = [tk.DoubleVar(value=station) for station in inputs.substructure.sta_CL_sub]
        self._update_substructure_display()
        self._update_prestressing_spans()
        
        # Load bridge information
        for key, var in self.bridge_vars.items():
            var.set(getattr(inputs.bridge_info, key))
        
        for span_idx, span_config in enumerate(inputs.span_configs):
            if span_idx < len(self.span_config_vars):
                # Load midspan strands and distances
                for i, val in enumerate(span_config.midspan_strands):
                    self.span_config_vars[span_idx]['midspan_strands'][i].set(val)
                    self.span_config_vars[span_idx]['row_enabled'][i].set(val > 0)
                
                for i in range(7):
                    self._on_row_enable_toggle(span_idx, i)

                # Load debond configurations
                debond_vars = self.span_config_vars[span_idx]['debond_vars']
                for row_idx in range(7):
                    row_key = f'row_{row_idx + 1}'
                    # Find matching debond config for this row
                    row_debond = next((dc for dc in span_config.debond_config if dc.row == row_idx + 1), None)
                    if row_debond and len(row_debond.strands) > 0:
                        # Clear existing configs and create new ones
                        debond_vars[row_key]['configs'] = []
                        for strand_val, length_val in zip(row_debond.strands, row_debond.lengths):
                            debond_vars[row_key]['configs'].append({
                                'strands': tk.IntVar(value=strand_val),
                                'lengths': tk.DoubleVar(value=length_val)
                            })
                    else:
                        # set default single config with zeros
                        debond_vars[row_key]['configs'] = [{
                            'strands': tk.IntVar(value=0),
                            'lengths': tk.DoubleVar(value=0)
                        }]

                # Load harp configurations
                harp_config = span_config.harp_config
                self.span_config_vars[span_idx]['harp_length_factor'].set(harp_config.harping_length_factor)
                for row_idx in range(7):
                    row_key = f'row_{row_idx + 1}'
                    harp_vars = self.span_config_vars[span_idx]['harp_vars'][row_key]
                    harp_vars['depth'].set(harp_config.harped_depths[row_idx])
                    harp_vars['harped'].set(harp_config.strands[row_idx] > 0)

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
                messagebox.showerror("Error", f"Failed to load project file:\n{str(e)}\n\nOpen error details: {traceback.format_exc()}")
    
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
            messagebox.showerror("Error", f"Failed to save project:\n{str(e)}, Save error details: {traceback.format_exc()}")
    
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
            error_msg = f"Analysis failed due to calculation error:\n\n{str(e)}\n\nAnalysis error details: {traceback.format_exc()}\n\nPlease check input parameters and try again."
            messagebox.showerror("Analysis Error", error_msg)
            self.update_status("Analysis failed - check inputs and try again")
    
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
                error_msg = f"PDF generation failed:\n\n{str(e)}\n\nPDF error details: {traceback.format_exc()}\n\nPlease try again or contact support."
                messagebox.showerror("PDF Generation Error", error_msg)
                self.update_status("PDF generation failed")
    
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
            print(f"Application error details: {traceback.format_exc()}")  # For debugging

if __name__ == "__main__":
    app = BridgeCalculatorApp()
    app.run()
