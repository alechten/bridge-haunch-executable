# input_data.py
"""
Data structures and validation for bridge input parameters
"""

import numpy as np
from typing import Dict, List, Union, Optional
from dataclasses import dataclass, field

@dataclass
class HeaderInfo:
    structure_number: str
    route_name: str
    feature_crossed: str
    designer_name: str
    designer_date: str
    reviewer_name: str
    reviewer_date: str

@dataclass
class VerticalCurveData:
    sta_VPI: float
    elev_VPI: float
    grade_1: float
    grade_2: float
    L_v_curve: float

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
    turn_width: float
    beam_shape: str
    rail_shape: str
    f_c_beam: float
    staged: str
    stage_start: str
    stg_line_rt: float
    stg_line_lt: float
    
    rdwy_slope: float = 0.02
    deck_thick: float = 7.5
    sacrificial_ws: float = 0.5
    brg_thick: float = 1 / 12
    ws: float = 0.035
    
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

# Default span configuration for easy GUI initialization
def create_default_span_config() -> SpanConfig:
    return SpanConfig(
        straight_strands=[0, 0, 0, 0, 0, 0, 0],
        strand_dist_bot=[2, 4, 6, 8, 10, 12, 14],
        debond_config=[
            DebondConfig(row=1, strands=[0], lengths=[0])
        ],
        harp_config=HarpConfig(
            strands=[0, 0, 0, 0, 0, 0, 0],
            harped_depths=[0, 0, 0, 0, 0, 0, 0],
            harping_length_factor=0.4
        )
    )

def create_default_inputs() -> BridgeInputs:
    """Create default input configuration"""
    inputs = BridgeInputs()
    
    # Create span configs based on number of spans
    inputs.span_configs = [create_default_span_config() for _ in range(inputs.num_spans)]
    
    return inputs
