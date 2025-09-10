# input_data.py
"""
Data structures and validation for bridge input parameters
"""

import numpy as np
from typing import Dict, List, Union, Optional
from dataclasses import dataclass, field

@dataclass
class HeaderInfo:
    structure_number: str = "S080 26369"
    route_name: str = "L-10B"
    feature_crossed: str = "I-80"
    designer_name: str = "AML"
    designer_date: str = "##/##/2025"
    reviewer_name: str = "TBD"
    reviewer_date: str = "TBD"

@dataclass
class VerticalCurveData:
    sta_VPI: float = 11510
    elev_VPI: float = 2242.50
    grade_1: float = 4.9200
    grade_2: float = -5.1800
    L_v_curve: float = 845

@dataclass
class SubstructureData:
    sta_CL_sub: List[float] = field(default_factory=lambda: [11376, 11500, 11624])

@dataclass
class BridgeInfo:
    skew: float
    deck_width: float
    rdwy_width: float
    PGL_loc: float
    beam_spa: float
    n_beams: int
    rdwy_slope: float = 0.02
    deck_thick: float = 7.5
    sacrificial_ws: float = 0.5
    turn_width: float
    brg_thick: float = 1 / 12
    beam_shape: str
    f_c_beam: float
    ws: float = 0.035
    rail_shape: str
    staged: str
    stage_start: str
    stg_line_rt: float
    stg_line_lt: float
    
@dataclass
class DebondConfig:
    row: int
    strands: List[int]
    lengths: List[float]

@dataclass
class HarpConfig:
    strands: List[int]
    harped_depths: List[float]
    harping_length_factor: float

@dataclass
class SpanConfig:
    straight_strands: List[int]
    strand_dist_bot: List[float]
    debond_config: List[DebondConfig]
    harp_config: HarpConfig

@dataclass
class BridgeInputs:
    header: HeaderInfo = field(default_factory=HeaderInfo)
    vertical_curve: VerticalCurveData = field(default_factory=VerticalCurveData)
    substructure: SubstructureData = field(default_factory=SubstructureData)
    bridge_info: BridgeInfo = field(default_factory=BridgeInfo)
    span_configs: List[SpanConfig] = field(default_factory=list)
    
    def __post_init__(self):
        # Set PGL_loc based on deck_width if not explicitly set
        if self.bridge_info.PGL_loc == 21 and self.bridge_info.deck_width != 42:
            self.bridge_info.PGL_loc = self.bridge_info.deck_width / 2
        
        # Set staging lines based on PGL_loc
        if self.bridge_info.stg_line_rt == 20:
            self.bridge_info.stg_line_rt = self.bridge_info.PGL_loc - 1
        if self.bridge_info.stg_line_lt == 16:
            self.bridge_info.stg_line_lt = self.bridge_info.PGL_loc - 5
    
    @property
    def num_spans(self) -> int:
        return len(self.substructure.sta_CL_sub) - 1
    
    def validate(self) -> List[str]:
        """Validate all input data and return list of error messages"""
        errors = []
        
        # Basic validation
        if self.vertical_curve.L_v_curve <= 0:
            errors.append("Curve length must be positive")
        
        if len(self.substructure.sta_CL_sub) < 2:
            errors.append("At least 2 substructure stations required")
        
        # Check if stations are in ascending order
        stations = self.substructure.sta_CL_sub
        if not all(stations[i] <= stations[i+1] for i in range(len(stations)-1)):
            errors.append("Substructure stations must be in ascending order")
        
        # Bridge geometry validation
        if self.bridge_info.n_beams <= 0:
            errors.append("Number of beams must be positive")
        
        if self.bridge_info.beam_spa <= 0:
            errors.append("Beam spacing must be positive")
        
        # Span configuration validation
        if len(self.span_configs) != self.num_spans:
            errors.append(f"Number of span configurations ({len(self.span_configs)}) must match number of spans ({self.num_spans})")
        
        return errors
