# config_manager.py
"""
Configuration management and file I/O for bridge calculator
"""

import json
import base64
from pathlib import Path
from typing import Optional
from input_data import BridgeInputs, HeaderInfo, VerticalCurveData, SubstructureData, BridgeInfo, SpanConfig, DebondConfig, HarpConfig

class ConfigManager:
    def __init__(self):
        self.current_config: Optional[BridgeInputs] = None
    
    def save_config(self, inputs: BridgeInputs, filepath: str) -> bool:
        """Save configuration to JSON file"""
        try:
            config_dict = self._inputs_to_dict(inputs)
            with open(filepath, 'w') as f:
                json.dump(config_dict, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False
    
    def load_config(self, filepath: str) -> Optional[BridgeInputs]:
        """Load configuration from JSON file"""
        try:
            with open(filepath, 'r') as f:
                config_dict = json.load(f)
            inputs = self._dict_to_inputs(config_dict)
            self.current_config = inputs
            return inputs
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return None
    
    def _inputs_to_dict(self, inputs: BridgeInputs) -> dict:
        """Convert BridgeInputs to dictionary for JSON serialization"""
        return {
            'header': {
                'structure_number': inputs.header.structure_number,
                'route_name': inputs.header.route_name,
                'feature_crossed': inputs.header.feature_crossed,
                'designer_name': inputs.header.designer_name,
                'designer_date': inputs.header.designer_date,
                'reviewer_name': inputs.header.reviewer_name,
                'reviewer_date': inputs.header.reviewer_date
            },
            'vertical_curve': {
                'sta_VPI': inputs.vertical_curve.sta_VPI,
                'elev_VPI': inputs.vertical_curve.elev_VPI,
                'grade_1': inputs.vertical_curve.grade_1,
                'grade_2': inputs.vertical_curve.grade_2,
                'L_v_curve': inputs.vertical_curve.L_v_curve
            },
            'substructure': {
                'sta_CL_sub': inputs.substructure.sta_CL_sub
            },
            'bridge_info': {
                'skew': inputs.bridge_info.skew,
                'deck_width': inputs.bridge_info.deck_width,
                'rdwy_width': inputs.bridge_info.rdwy_width,
                'PGL_loc': inputs.bridge_info.PGL_loc,
                'beam_spa': inputs.bridge_info.beam_spa,
                'n_beams': inputs.bridge_info.n_beams,
                'rdwy_slope': inputs.bridge_info.rdwy_slope,
                'deck_thick': inputs.bridge_info.deck_thick,
                'sacrificial_ws': inputs.bridge_info.sacrificial_ws,
                'turn_width': inputs.bridge_info.turn_width,
                'brg_thick': inputs.bridge_info.brg_thick,
                'beam_shape': inputs.bridge_info.beam_shape,
                'rail_shape': inputs.bridge_info.rail_shape,
                'f_c_beam': inputs.bridge_info.f_c_beam,
                'ws': inputs.bridge_info.ws,
                'staged': inputs.bridge_info.staged,
                'stage_start': inputs.bridge_info.stage_start,
                'stg_line_rt': inputs.bridge_info.stg_line_rt,
                'stg_line_lt': inputs.bridge_info.stg_line_lt
            },
            'span_configs': [
                {
                    'straight_strands': span.straight_strands,
                    'strand_dist_bot': span.strand_dist_bot,
                    'debond_config': [
                        {
                            'row': debond.row,
                            'strands': debond.strands,
                            'lengths': debond.lengths
                        } for debond in span.debond_config
                    ],
                    'harp_config': {
                        'strands': span.harp_config.strands,
                        'harped_depths': span.harp_config.harped_depths,
                        'harping_length_factor': span.harp_config.harping_length_factor
                    }
                } for span in inputs.span_configs
            ]
        }
    
    def _dict_to_inputs(self, config_dict: dict) -> BridgeInputs:
        """Convert dictionary to BridgeInputs object"""
        header = HeaderInfo(**config_dict['header'])
        vertical_curve = VerticalCurveData(**config_dict['vertical_curve'])
        substructure = SubstructureData(**config_dict['substructure'])
        bridge_info = BridgeInfo(**config_dict['bridge_info'])
        
        span_configs = []
        for span_dict in config_dict['span_configs']:
            debond_configs = [
                DebondConfig(**debond) for debond in span_dict['debond_config']
            ]
            harp_config = HarpConfig(**span_dict['harp_config'])
            
            span_config = SpanConfig(
                straight_strands=span_dict['straight_strands'],
                strand_dist_bot=span_dict['strand_dist_bot'],
                debond_config=debond_configs,
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

def get_logo_data() -> bytes:
    """Get NDOT logo data from embedded base64 string"""
    # Embedded NDOT logo as base64 - replace with actual logo data
    NDOT_LOGO_BASE64 = """
iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==
"""
    return base64.b64decode(NDOT_LOGO_BASE64.strip())

def save_logo_temp(temp_dir: str = None) -> str:
    """Save logo to temporary file and return path"""
    import tempfile
    import os
    
    if temp_dir is None:
        temp_dir = tempfile.gettempdir()
    
    logo_path = os.path.join(temp_dir, "NDOT_logo.png")
    
    with open(logo_path, 'wb') as f:
        f.write(get_logo_data())
    
    return logo_path
