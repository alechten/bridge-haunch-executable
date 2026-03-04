import math
import numpy as np
import pandas as pd
from typing import Dict, List, Union, Optional
from dataclasses import dataclass, field

class VerticalCurve:
    def __init__(self, inputs):
        self.v_c_data = inputs.vertical_curve # Store vertical_curve_data as an instance attribute

        self.sta_VPC = self.v_c_data.sta_VPI - self.v_c_data.L_v_curve / 2
        self.elev_VPC = self.v_c_data.elev_VPI - (self.v_c_data.grade_1 / 100) * (self.v_c_data.L_v_curve / 2)
        self.sta_VPT = self.v_c_data.sta_VPI + self.v_c_data.L_v_curve / 2
        self.elev_VPT = self.elev_VPC + self.v_c_data.grade_1 / 100 * self.v_c_data.L_v_curve + \
            (self.v_c_data.grade_2 - self.v_c_data.grade_1) / 200 / self.v_c_data.L_v_curve * (self.v_c_data.L_v_curve) ** 2

    def elev(self, sta):
        return np.where(sta < self.sta_VPC, self.elev_VPC - self.v_c_data.grade_1 / 100 * (self.sta_VPC - sta),\
                    np.where(sta > self.sta_VPT, self.elev_VPT + self.v_c_data.grade_2 / 100 * (sta - self.sta_VPT),\
                             self.elev_VPC + self.v_c_data.grade_1 / 100 * (sta - self.sta_VPC) + \
                              (self.v_c_data.grade_2 - self.v_c_data.grade_1) / 200 / self.v_c_data.L_v_curve * (sta - self.sta_VPC) ** 2))

class beam_rail_info:
    def __init__(self, inputs):
        inpb = inputs.bridge_info
        
        self._beam_properties(inpb.beam_shape, inpb.f_c_beam, inpb.n_beams, inpb.skew)
        self._rail_properties(inpb.rail_shape)

    def _beam_properties(self, beam_shape, f_c_beam, n_beams, skew):
        beam_options = {
            'shape': ['NU35', 'NU43', 'NU53', 'NU63', 'NU70', 'NU78', 'IT13','IT17','IT21','IT25','IT29','IT33','IT39'],
            'height': [35.44, 43.31, 53.13, 63, 70.88, 78.75, 13.31, 17.25, 21.19, 25.13, 29.06, 33, 36.94],
            'area': [648.3, 695.1, 753.3, 812, 858.7, 905.5, 178.9, 204, 229.1, 254.2, 279.3, 304.4, 329.5],
            'y_b_nc': [16.13, 19.57, 23.95, 28.43, 32.05, 35.70, 4.5, 5.79, 7.22, 8.76, 10.37, 12.05, 13.77],
            'I_g_nc': [110218, 182262, 301949, 458653, 611646, 791107, 2034, 4472, 8334, 13871, 21300, 30837, 42688],
            'weight (8 ksi)': [0.711, 0.763, 0.827, 0.891, 0.942, 0.994, 0.196, 0.224, 0.251, 0.279, 0.306, 0.334, 0.362],
            'weight (10 ksi)': [0.72, 0.772, 0.837, 0.902, 0.954, 1.006, 0.199, 0.227, 0.255, 0.282, 0.310, 0.338, 0.366]
        }

        beam_df = pd.DataFrame(beam_options)
        beam_df.set_index('shape', inplace=True)

        self.b_height = beam_df.loc[beam_shape, 'height']
        self.area = beam_df.loc[beam_shape, 'area']
        self.y_b_nc = beam_df.loc[beam_shape, 'y_b_nc']
        self.I_g_nc = beam_df.loc[beam_shape, 'I_g_nc']
        self.is_NU = 'NU' in beam_shape
        self.is_IT = 'IT' in beam_shape

        if f_c_beam == 8:
            self.f_c_i_beam = 6
            self.b_weight = beam_df.loc[beam_shape, 'weight (8 ksi)']
            self.E_c_i = 120000 * 0.975 * 0.15 ** 2 * self.f_c_i_beam ** 0.33
            self.E_c = 120000 * 0.975 * 0.15 ** 2 * f_c_beam ** 0.33
        elif f_c_beam == 10:
            self.f_c_i_beam = 7.5
            self.b_weight = beam_df.loc[beam_shape, 'weight (10 ksi)']
            self.E_c_i = 120000 * 0.975 * 0.15 ** 2 * self.f_c_i_beam ** 0.33
            self.E_c = 120000 * 0.975 * 0.15 ** 2 * f_c_beam ** 0.33

        if self.is_NU:
            self.tf_width = 48.25 / 12
            self.no_long_lines = 2 * n_beams
        elif self.is_IT:
            self.tf_width = 4.875 / 12
            self.no_long_lines = n_beams

        self.flng_adjust_skew = self.tf_width / 2 * np.tan(np.deg2rad(skew))

    def _rail_properties(self, rail_shape):
        railing = {
          'shape': ['39_SSCR', '39_OCR', '42_NU_O', '42_NU_C', '42_NU_M', '34_NU_O', '34_NU_C','29_NE_O','29_NE_C','32_NJ','42_NJ'],
          'weight': [   0.365,    0.438,     0.441,     0.524,     0.873,     0.373,     0.455,    0.270,    0.382,  0.345,  0.413],
          'height': [      39,       39,        42,        42,        42,        34,        34,       29,       29,     32,     42],
          'bottom width': [10,       10,      10.5,      10.5,      10.5,      10.5,      10.5,       11,       11,     16,     16],
          'edge distance': [2,        2,         2,         2,         2,         2,         2,        1,        1,      0,      0]
        }

        rail_df = pd.DataFrame(railing)
        rail_df.set_index('shape', inplace=True)

        self.r_weight = rail_df.loc[rail_shape, 'weight']
        self.r_height = rail_df.loc[rail_shape, 'height']
        self.bottom_width = rail_df.loc[rail_shape, 'bottom width']
        self.edge_distance = rail_df.loc[rail_shape, 'edge distance']
        self.is_Open = 'O' in rail_shape

class beam_layout:
    def __init__(self, inputs, beam_rail_obj):
        inpb = inputs.bridge_info
        sta_CL_sub = inputs.substructure.sta_CL_sub
        
        "New Values"
        self.span = np.zeros(len(sta_CL_sub) - 1)
        for i in range(len(sta_CL_sub) - 1):
            self.span[i] = sta_CL_sub[i+1] - sta_CL_sub[i]
        self.ns = len(sta_CL_sub) - 1
        self.offsets = np.zeros((1, beam_rail_obj.no_long_lines))
        self.off = np.zeros((1, beam_rail_obj.no_long_lines))
        self.cant_len = (inpb.deck_width - (inpb.n_beams - 1) * inpb.beam_spa) / 2
        self.beam_pos = self.cant_len + inpb.beam_spa * np.arange(inpb.n_beams)
        for i in range(inpb.n_beams):
            j, k = 2 * i, 2 * i + 1
            self.off[0,j] = inpb.PGL_loc - i * inpb.beam_spa - self.cant_len
            self.off[0,k] = inpb.PGL_loc - i * inpb.beam_spa - self.cant_len
            self.offsets[0,j] = self.off[0,j] - beam_rail_obj.tf_width / 2
            self.offsets[0,k] = self.off[0,k] + beam_rail_obj.tf_width / 2
        self.L_brg_brg = np.zeros(self.ns)
        for i in range(self.ns):
            if self.ns == 1:
                self.L_brg_brg = self.span
            else:
                if (i == 0) | (i == len(self.span) - 1):
                    self.L_brg_brg[i] = self.span[i] + 0.5 - 4 / 12 - 0.5 * 2
                else:
                    self.L_brg_brg[i] = self.span[i] - 2 * 4 / 12 - 0.5 * 2
        self.L_beam = self.L_brg_brg + 0.5 * 2

class stations_locations:
    def __init__(self, inputs, beam_layout_obj, beam_rail_obj):
        b_l = beam_layout_obj
        sta_CL_sub = inputs.substructure.sta_CL_sub
        
        abut_end = 0.5 * np.cos(np.deg2rad(inputs.bridge_info.skew))
        turn_end = inputs.bridge_info.turn_width / 2 * np.cos(np.deg2rad(inputs.bridge_info.skew))

        self.s = np.zeros(b_l.ns)
        #### IF 1 SPAN BRIDGE OR FIRST SPAN OF MULTISPAN USE ABUT END ####
        start_vals = np.where((b_l.ns == 1) | (np.arange(b_l.ns) == 0), abut_end, turn_end) + beam_rail_obj.flng_adjust_skew
        #### IF 1 SPAN BRIDGE OR LAST SPAN OF MULTISPAN USE ABUT END ####
        end_vals = np.where((b_l.ns == 1) | (np.arange(b_l.ns) == b_l.ns - 1), abut_end, turn_end) + beam_rail_obj.flng_adjust_skew
        L_eff = b_l.L_brg_brg - start_vals - end_vals
        #### GET NUMBER OF 10 FT POINTS FOR HALF SPAN THEN DOUBLE THEN ADD 3 FOR BRGS AND MIDPOINT ####
        self.s = np.ceil(L_eff / 20) * 2 + 3

        self.sta_x_10_ft = np.zeros((int(self.s.sum()), 1))
        g = 0
        for i in range(b_l.ns):
            h = (int(self.s[i]) - 3) / 2
            #### DEFINE ARRAY OF OUTPUTS FOR ONE SPAN ####
            #### ELSE SELECTS THE ARRAY BASED ON THE SPAN WITHIN THE NO. OF SPANS ####
            span_offsets = (0, 0, abut_end, abut_end) if b_l.ns == 1\
            else [(0, 10 / 12, abut_end, turn_end), (10 / 12, 10 / 12, turn_end, turn_end), (10 / 12, 0, turn_end, abut_end)][min(i, 2) if i != b_l.ns - 1 else 2]
            start_brg_off, end_brg_off, start, end = span_offsets
            m = sta_CL_sub[i] + start_brg_off + b_l.L_brg_brg[i] / 2 - h * 10
            #### INDEX VALUES BETWEEN START AND END OF SPAN ####
            j_vals = np.arange(int(self.s[i]))
            self.sta_x_10_ft[g:g + len(j_vals)] = np.where(j_vals == 0, sta_CL_sub[i] + start_brg_off,
                                   np.where(j_vals == 1, sta_CL_sub[i] + start + beam_rail_obj.flng_adjust_skew,
                                   np.where(j_vals < self.s[i] - 2, m + 10 * (j_vals - 1),
                                   np.where(j_vals == self.s[i] - 2, sta_CL_sub[i + 1] - end - beam_rail_obj.flng_adjust_skew,
                                           sta_CL_sub[i + 1] - end_brg_off)))).reshape(-1, 1)
            g += len(j_vals)
        self.sta_G = self.sta_x_10_ft + b_l.off * np.tan(np.deg2rad(inputs.bridge_info.skew))

        #### ARRAY OF THE PROGRESSIVE NUMBER OF X POINTS ACROSS SPANS ####
        indices = np.concatenate([[0], self.s.cumsum().astype(int)])
        #### MASKS RETURNS TRUE FOR STATIONS IN GIVEN SPAN ####
        masks = [(self.sta_G >= self.sta_G[indices[i]]) & (self.sta_G <= self.sta_G[indices[i+1]-1]) for i in range(b_l.ns)]
        #### SUM ARRAY FOR EACH SPAN OF STATION DISTANCES FROM FIRST STAION ####
        self.L_span_gen = sum(np.where(mask, self.sta_G - self.sta_G[indices[i]], 0) for i, mask in enumerate(masks))

class section_properties_dead_loads:
    def __init__(self, inputs, beam_layout_obj, beam_rail_obj):
        inpb, b_r, b_l = inputs.bridge_info, beam_rail_obj, beam_layout_obj

        "New Definitions"
        self.over_deck_t = inpb.deck_thick + inpb.sacrificial_ws
        self.min_haunch = 1 / 12 + inpb.rdwy_slope * b_r.tf_width / 2
        self.deck_forms = 0.005
        self.drip_bead = 0.75 * 8 / 144 * 0.15 * b_r.is_Open
        self.ex_bm_ar = np.array([1 if i == 0 or i == inpb.n_beams - 1 else 0 for i in range(inpb.n_beams)])
        self.deck_E_c = 120000 * 0.975 * 0.145 ** 2 * 4 ** 0.33
        self.n_deck = self.deck_E_c / b_r.E_c

        self._calc_stage_widths(inpb, inpb.beam_spa, b_l.beam_pos, b_l.cant_len, inpb.n_beams, b_r.tf_width)
        self._calc_deck_sections(b_r.b_height, b_r.area, b_r.y_b_nc, b_r.I_g_nc)
        self.dist_dead_load(inpb, b_r, b_l)

    def _calc_stage_widths(self, inpb, beam_spa, beam_pos, cant_len, n_beams, beam_tf_width):
        stage_1, stage_2, trib_width_1, trib_width_2 = [np.zeros(n_beams) for _ in range(4)]
        if inpb.staged == True:
            left_cond = (beam_pos <= inpb.stg_line_lt) & (inpb.stage_start == 'left')
            right_cond = (beam_pos >= inpb.stg_line_rt) & (inpb.stage_start == 'left') if inpb.stg_line_rt > 0 else (beam_pos >= inpb.stg_line_lt) & (inpb.stage_start == 'left')
            stage_1[left_cond] = stage_2[right_cond] = 1
            for i in range(n_beams):
                if left_cond[i] or right_cond[i]:
                    #### PICK STAGE LINE ####
                    line = inpb.stg_line_lt if left_cond[i] else (inpb.stg_line_rt if inpb.stg_line_rt > 0 else inpb.stg_line_lt)
                    #### PICK TRIBUTARY WIDTH ARRAY ####
                    arr = trib_width_1 if left_cond[i] else trib_width_2
                    if (left_cond[i] and beam_pos[i] + beam_spa + beam_tf_width / 2 > line) or (right_cond[i] and beam_pos[i] - beam_spa + beam_tf_width / 2 < line):
                        other_half = cant_len if i == 0 or i == n_beams - 1 else beam_spa / 2
                        arr[i] = other_half + abs(beam_pos[i] - line)
                    elif i == 0:
                        arr[i] = beam_pos[i] + beam_spa / 2
                    elif i == n_beams - 1 and right_cond[i]:
                        arr[i] = beam_pos[i] - beam_pos[i-1] - beam_spa / 2 + cant_len
                    else:
                        arr[i] = beam_pos[i] - beam_pos[i-1]
        else:
            stage_1 = stage_2 = np.ones(n_beams)
            trib_width_1 = trib_width_2 = np.where((np.arange(n_beams) == 0) | (np.arange(n_beams) == n_beams - 1),
                            cant_len + beam_spa / 2, beam_spa)

        stage_3 = stage_1 + stage_2
        trib_width_3 = np.where((np.arange(n_beams) == 0) | (np.arange(n_beams) == n_beams - 1),
                        cant_len + beam_spa / 2, beam_spa)

        self.deck = {
            'Stage 1 Width': trib_width_1,
            'Stage 2 Width': trib_width_2,
            'Stage 3 Width': trib_width_3
        }

        self.stage_1, self.stage_2, self.stage_3 = stage_1, stage_2, stage_3
        self.deck_df = pd.DataFrame(self.deck)

        return self

    def _calc_deck_sections(self, beam_ht, A_beam, y_b_nc, I_g_nc):
        over_deck_t = self.over_deck_t
        n_deck = self.n_deck
        deck_df = self.deck_df

        #### (A_beam * y_beam + A_deck * n * y_deck) / (A_beam + A_deck * n)
        deck_df['y_b_c Stage 1'] = (A_beam * y_b_nc + \
            over_deck_t * deck_df['Stage 1 Width'] * 12 * n_deck * (over_deck_t /2 + beam_ht)) \
            / (A_beam + over_deck_t * n_deck * deck_df['Stage 1 Width'] * 12)

        deck_df['y_b_c Stage 2'] = (A_beam * y_b_nc + \
            over_deck_t * deck_df['Stage 2 Width'] * 12 * n_deck * (over_deck_t /2 + beam_ht)) \
            / (A_beam + over_deck_t * n_deck * deck_df['Stage 2 Width'] * 12)

        deck_df['y_b_c Stage 3'] = (A_beam * y_b_nc + \
            over_deck_t * deck_df['Stage 3 Width'] * 12 * n_deck * (over_deck_t /2 + beam_ht)) \
            / (A_beam + over_deck_t * n_deck * deck_df['Stage 3 Width'] * 12)

        #### I_deck * n + A_deck * n * (y_deck - y_cen)^2 + I_beam + A_beam * (y_beam - y_cen)^2
        deck_df['I_c Stage 1'] = deck_df['Stage 1 Width'] * 12 * over_deck_t ** 3 * n_deck / 12 + \
            deck_df['Stage 1 Width'] * 12 * over_deck_t * n_deck * (over_deck_t /2 + beam_ht - deck_df['y_b_c Stage 1']) ** 2 + \
            I_g_nc * self.stage_1 + A_beam * (y_b_nc - deck_df['y_b_c Stage 1']) ** 2

        deck_df['I_c Stage 2'] = deck_df['Stage 2 Width'] * 12 * over_deck_t ** 3 * n_deck / 12 + \
            deck_df['Stage 2 Width'] * 12 * over_deck_t * n_deck * (over_deck_t /2 + beam_ht - deck_df['y_b_c Stage 2']) ** 2 + \
            I_g_nc * self.stage_2 + A_beam * (y_b_nc - deck_df['y_b_c Stage 2']) ** 2

        deck_df['I_c Stage 3'] = deck_df['Stage 3 Width'] * 12 * over_deck_t ** 3 * n_deck / 12 + \
            deck_df['Stage 3 Width'] * 12 * over_deck_t * n_deck * (over_deck_t /2 + beam_ht - deck_df['y_b_c Stage 3']) ** 2 + \
            I_g_nc + A_beam * (y_b_nc - deck_df['y_b_c Stage 3']) ** 2

        self.deck_df = deck_df

        return self

    def dist_dead_load(self, inpb, b_r, b_l):
        over_deck_t, min_haunch, deck_df = self.over_deck_t, self.min_haunch, self.deck_df
        stage_1, stage_2, trib_width_1, trib_width_2 = self.stage_1, self.stage_2, self.deck['Stage 1 Width'], self.deck['Stage 2 Width']
        
        if inpb.staged == True:
            #### STAGE 1 NONCOMPOSITE AND COMPOSITE WEIGHTS ####
            comp_dist_1 = deck_df['Stage 1 Width'] / deck_df['Stage 1 Width'].sum()
            deck_df['Stage 1 NC Wt'] = 0.15 * over_deck_t / 12 * deck_df['Stage 1 Width'] + \
                (0.15 * b_r.tf_width * min_haunch + (deck_df['Stage 1 Width'] - b_r.tf_width) * self.deck_forms) * stage_1 + self.drip_bead * self.ex_bm_ar * stage_1
            deck_df['Stage 1 C Wt'] = b_r.r_weight * comp_dist_1
            if 'stage_1' in inpb.w_super:
                deck_df['Stage 1 C Wt'] += np.sum(inpb.w_super['stage_1']) * comp_dist_1
            if (inpb.median == True) & (inpb.med_st + inpb.med_width < inpb.stg_line_lt) & (inpb.stage_start == "left"):
                comp_dist_med = deck_df['Stage 1 Width'] / deck_df['Stage 1 Width'].sum()
                deck_df['Stage 1 C Wt'] += 0.15 * inpb.med_width * inpb.med_thick / 12 * comp_dist_med

            #### STAGE 2 NONCOMPOSITE AND COMPOSITE WEIGHTS ####
            comp_dist_2 = deck_df['Stage 2 Width'] / deck_df['Stage 2 Width'].sum()
            other_half = np.array([b_l.cant_len if i == 0 or i == inpb.n_beams - 1 else inpb.beam_spa / 2 for i in range(inpb.n_beams)])
            comp_stage_1 = ((deck_df['Stage 2 Width'] < other_half + b_r.tf_width / 2) > 0) * stage_2
            deck_df['Stage 1 C Wt'] += comp_stage_1 * (deck_df['Stage 2 Width'] * 0.15 * over_deck_t / 12 + 0.15 * b_r.tf_width * min_haunch + (deck_df['Stage 2 Width'] - b_r.tf_width) * self.deck_forms)
            deck_df['Stage 2 NC Wt'] = 0.15 * over_deck_t / 12 * deck_df['Stage 2 Width'] + \
                (0.15 * b_r.tf_width * min_haunch + (deck_df['Stage 2 Width'] - b_r.tf_width) * self.deck_forms) * (stage_2 - comp_stage_1) + self.drip_bead * self.ex_bm_ar * stage_2
            deck_df['Stage 2 C Wt'] = b_r.r_weight * comp_dist_2
            if 'stage_2' in inpb.w_super:
                deck_df['Stage 2 C Wt'] += np.sum(inpb.w_super['stage_2']) * comp_dist_2
            if (inpb.median == True) & (inpb.med_st > inpb.stg_line_rt) & (inpb.stage_start == "right"):
                comp_dist_med = deck_df['Stage 2 Width'] / deck_df['Stage 2 Width'].sum()
                deck_df['Stage 2 C Wt'] += 0.15 * inpb.med_width * inpb.med_thick / 12 * comp_dist_med

            #### STAGE 3 PARTIALLY COMPOSITE WEIGHT ####
            if inpb.stg_line_rt > 0:
                self.closure_width = (deck_df['Stage 3 Width'] - deck_df['Stage 2 Width'] - deck_df['Stage 1 Width'])
                clos_stage = (self.closure_width.sum()) / 2
                dist_width_closure_1 = stage_1 / stage_1.sum()
                dist_width_closure_2 = stage_2 / stage_2.sum()
                dist_width_closure = dist_width_closure_1 * clos_stage + dist_width_closure_2 * clos_stage
                deck_df['Stage 3 PC Wt'] = 0.15 * dist_width_closure * over_deck_t / 12 + self.closure_width * self.deck_forms
            else:
                deck_df['Stage 3 PC Wt'] = 0
        else:
            deck_df['Stage 2 NC Wt'], deck_df['Stage 2 C Wt'], deck_df['Stage 3 PC Wt'] = 0, 0, 0
            deck_df['Stage 1 NC Wt'] = 0.15 * over_deck_t / 12 * deck_df['Stage 1 Width'] + 0.15 * b_r.tf_width * min_haunch \
                + (deck_df['Stage 1 Width'] - b_r.tf_width) * self.deck_forms + self.drip_bead * self.ex_bm_ar
            comp_dist_1 = deck_df['Stage 1 Width'] / deck_df['Stage 1 Width'].sum()
            deck_df['Stage 1 C Wt'] = 2 * b_r.r_weight * comp_dist_1
            if 'stage_1' in inpb.w_super:
                deck_df['Stage 1 C Wt'] += np.sum(inpb.w_super['stage_1']) * comp_dist_1

        #### STAGE 3 COMPOSITE WEIGHT ####
        ws_width = deck_df['Stage 3 Width'].copy()
        ws_width.iloc[0] -= (b_r.edge_distance + b_r.bottom_width) / 12
        ws_width.iloc[-1] -= (b_r.edge_distance + b_r.bottom_width) / 12
        deck_df['Stage 3 C Wt'] = inpb.ws * ws_width
        comp_dist_3 = deck_df['Stage 3 Width'] / deck_df['Stage 3 Width'].sum()
        if (inpb.median == True) & (((inpb.med_st + inpb.med_width > inpb.stg_line_lt) & (inpb.med_st < inpb.stg_line_lt)) | ((inpb.med_st + inpb.med_width > inpb.stg_line_rt) & (inpb.med_st < inpb.stg_line_rt))):
            deck_df['Stage 3 C Wt'] += 0.15 * inpb.med_width * inpb.med_thick / 12 * comp_dist_3
        if 'final' in inpb.w_super:
            deck_df['Stage 3 C Wt'] += np.sum(inpb.w_super['final']) * comp_dist_3

        self.deck_df = deck_df
        return self

class PrestressingCamberCalculator:
    def __init__(self, inputs, beam_rail_obj, beam_layout_obj, stations_obj, IL: float = 0.1, TL: float = 0.2):
        #### MATERIAL PROPERTIES AND PRESTRESSING PARAMETERS ####
        b_r, b_l, s = beam_rail_obj, beam_layout_obj, stations_obj
        span_configs = inputs.span_configs

        self.A_strand = 0.217 if beam_rail_obj.is_NU else 0.167
        self.E_ps = 28500
        self.f_pu = 270
        self.f_pei = 0.75 * self.f_pu * (1 - IL)  # Initial effective prestress
        self.f_pe = 0.75 * self.f_pu * (1 - TL)   # Final effective prestress
        
        self._calculate_total_camber(b_r, b_l, s, span_configs)
        
    def validate_inputs(self, span_config: Dict, L_beam) -> None:
        #### INPUT VALIDATION CHECKS ####
        midspan_strands = np.array(span_config.midspan_strands)

        # Check debonding configurations if present
        if span_config.debond_config:
            for debond in span_config.debond_config:
                row_idx = debond.row - 1  # Convert to 0-based indexing
                total_debonded = sum(debond.strands)
                total_in_row = midspan_strands[row_idx] / self.A_strand

                # Check debonded strands don't exceed 45% of row
                if total_debonded / total_in_row > 0.45:
                    raise ValueError(f"Debonded strands in row {debond.row} exceed 45% limit")

                # Check debonding lengths don't exceed 20% of beam length
                for length in debond.lengths:
                    if length > 0.2 * L_beam:
                        raise ValueError(f"Debonding length {length} ft exceeds 20% of beam length")

    def calculate_debonded_strand_camber(self, b_r, debond_config: List[Dict], d_ps: np.ndarray, e_ps: np.ndarray, L_beam) -> float:
        #### DEBONDED STRAND CAMBER CALCULATION ####
        total_camber = 0.0
        for debond in debond_config:
            row_idx = debond.row - 1  # Convert to 0-based indexing
            strands_list = debond.strands
            lengths_list = debond.lengths
            # Calculate contribution for each debonding length group in this row
            for strands, length in zip(strands_list, lengths_list):
                A_debond = strands * self.A_strand
                P_debond = A_debond * self.f_pei
                # Debonding factor from PCI Design Handbook
                debond_factor = 1 - 2 * (length / L_beam) ** 2 - 2 * (length / L_beam) ** 2
                camber_contribution = (P_debond * e_ps[row_idx] * debond_factor * (L_beam * 12) ** 2) / (8 * b_r.E_c_i * b_r.I_g_nc)
                total_camber += camber_contribution
        return total_camber

    def calculate_harped_strand_camber(self, b_r, harp_config: Dict, d_ps: np.ndarray, e_ps: np.ndarray, L_beam) -> float:
        #### HARPED STRAND CAMBER CALCULATION ####
        harped_strands = np.array(harp_config.strands)
        harped_depth = np.array(harp_config.harped_depths)
        harping_length = harp_config.harping_length_factor * L_beam

        A_harp = harped_strands * self.A_strand
        P_harp = A_harp * self.f_pei
        y_ps_harped = d_ps - harped_depth

        # PCI Design Handbook formula for harped strands
        term1 = e_ps * (L_beam * 12) ** 2 / 8
        term2 = y_ps_harped * (harping_length * 12) ** 2 / 6

        return np.sum(P_harp * (term1 - term2)) / b_r.E_c_i / b_r.I_g_nc

    def calculate_span_camber(self, b_r, span_config: Dict, L_beam, L_x) -> np.ndarray:
        #### VALIDATE INPUTS ####
        self.validate_inputs(span_config, L_beam)
        #### SETUP STRAND GEOMETRY ####
        if span_config.harp_config:
            harped_strands = np.array(span_config.harp_config.strands)
        if span_config.debond_config:
            total_debonded = 0
            for debond in span_config.debond_config:
                row_idx = debond.row - 1  # Convert to 0-based indexing
                strands_list = debond.strands
                lengths_list = debond.lengths
                # Calculate contribution for each debonding length group in this row
                for strands, length in zip(strands_list, lengths_list):
                    debonded_strands = np.zeros_like(span_config.midspan_strands)
                    debonded_strands[row_idx] = strands
                    total_debonded += debonded_strands
        straight_strands = np.array(span_config.midspan_strands - harped_strands - total_debonded) * self.A_strand
        straight_strands[straight_strands < 0] = 0
        d_ps_base = b_r.b_height - np.array(span_config.strand_dist_bot)
        e_ps = d_ps_base - (b_r.b_height - b_r.y_b_nc)

        #### CALCULATE CAMBER COMPONENTS ####
        camber_total = 0.0

        # Straight bonded strands
        self.camber_straight = np.sum(straight_strands * self.f_pei * e_ps) * (L_beam * 12) ** 2 / (8 * b_r.E_c_i * b_r.I_g_nc)
        camber_total += self.camber_straight

        # Debonded strands
        if span_config.debond_config:
            self.camber_debonded = self.calculate_debonded_strand_camber(b_r, span_config.debond_config, d_ps_base, e_ps, L_beam)
            camber_total += self.camber_debonded

        # Harped strands
        if span_config.harp_config:
            self.camber_harped = self.calculate_harped_strand_camber(b_r, span_config.harp_config, d_ps_base, e_ps, L_beam)
            camber_total += self.camber_harped

        #### DISTRIBUTE CAMBER ALONG SPAN ####
        return camber_total * (1 - ((L_beam/2 - L_x) / (L_beam/2)) ** 2)

    def _calculate_total_camber(self, b_r, b_l, s, span_configs: List[Dict]) -> np.ndarray:
        #### INITIALIZE CAMBER ARRAY ####
        self.camber = np.zeros_like(s.sta_G)

        #### CALCULATE CAMBER FOR EACH SPAN ####
        for i in range(b_l.ns):
            # Determine station indices for this span
            start_index = int(s.s[:i].sum()) if i > 0 else 0
            end_index = int(s.s[:i+1].sum())
            L_x = s.L_span_gen[start_index:end_index] + 0.5

            # Calculate camber for this span
            span_camber = self.calculate_span_camber(b_r, span_configs[i], b_l.L_beam[i], L_x)

            # Assign to total camber array
            self.camber[start_index:end_index, :] = span_camber

        return self

def gauss(f, a, b, m):
    chi = np.array([-np.sqrt(3/5), 0, np.sqrt(3/5)])
    w = np.array([5/9, 8/9, 5/9])
    h = (b-a)/m # creates a (# x points, # girder lines) matrix

    # Create arrays for all intervals at once
    i_vals = np.arange(m) # creates an m x 1 matrix
    # Create a_temps matrix with shape (# x points, # girder lines, 1, m) by expanding dimensions of a, h, and i_vals for broadcasting
    a_temps = a[:, :, np.newaxis, np.newaxis] + i_vals[np.newaxis, np.newaxis, np.newaxis, :] * h[:, :, np.newaxis, np.newaxis]
    b_temps = a[:, :, np.newaxis, np.newaxis] + (i_vals[np.newaxis, np.newaxis, np.newaxis, :] + 1) * h[:, :, np.newaxis, np.newaxis]

    # Jacobian for each interval
    J_vals = (b_temps - a_temps) / 2 # create an (# x points, # girder lines, 1, m) matrix of the Jacobian

    # Compute x values for all intervals and quadrature points simultaneously
    x_matrix = ((b_temps - a_temps) / 2 * chi[np.newaxis, np.newaxis, :, np.newaxis] + (b_temps + a_temps) / 2)  # create a (# x points, # girder lines, # gauss points, m) matrix

    # Evaluate function at all points (vectorized if f supports it)
    f_matrix = f(x_matrix) # needs to be able to utilize original inputs for "L" and "w" from initial inputs into function passed to gauss function

    # Apply Jacobian and weights, broadcast J_vals across len(chi) and w across len(b[1]), len(b[0]), :, i_vals
    weighted_matrix = f_matrix * J_vals * w[np.newaxis, np.newaxis, :, np.newaxis] # needs to multiply the weights across (# x points, # girder lines, # gauss points, m)

    # Sum over all intervals and quadrature points
    return np.sum(weighted_matrix, axis=(2, 3)) # needs to sum both weights and "m" values into a (# x points, # girder lines) matrix

def gauss_seidel(A, b, tol, max_iter=50):
  iter=0
  x0 = np.ones(A.shape[0])
  r = b - np.dot(A, x0)
  err0 = np.sum(np.abs(r))
  err = tol + 1
  x = x0
  while iter < max_iter and err > tol:
    iter += 1
    for i in range(A.shape[0]):
      if A[i, i] == 0:
        x[i] = 0
      else:
        x[i] = (b[i] - np.dot(A[i, :], x[:]) + A[i, i] * x[i]) / A[i, i]
    r = b - np.dot(A, x)
    if r.any() == 0:
      err = 0
    else:
      err = np.sum(np.abs(r))/err0
  return x

# Moment functions for structural analysis
uniform_M = lambda x, L, w: w / 2 * (x * L - x ** 2)
x_uniform_M = lambda x, L, w: x * uniform_M(x, L, w)
## Profile-Dominated-Haunch-Shape Moment Equation (base equation 1/4-(x-L/2)^2/L^2 is integrated twice)
quad_inv_para_M = lambda x, L, w: w * (-x ** 4 / 12 / L ** 2 + x ** 3 / 6 / L - x * L / 12)
x_quad_inv_para_M = lambda x, L, w: x * quad_inv_para_M(x, L, w)
## Deflection-Dominated-Haunch-Shape Moment Equation (base equation (x-L/2)^2/L^2 is integrated twice)
quad_para_M = lambda x, L, w: w * (x ** 4 / 12 / L ** 2 - x ** 3 / 6 / L + x ** 2 / 8 + x * L / 24)
x_quad_para_M = lambda x, L, w: x * quad_para_M(x, L, w)

class simple_span:
    def __init__(self, inputs, beam_rail_obj, beam_layout_obj, stations_obj, deck_sections_obj):
        b_r, b_l, s = beam_rail_obj, beam_layout_obj, stations_obj
        deck_df = deck_sections_obj.deck_df
        
        "Initialize Section Properties"
        bm_lines = beam_rail_obj.no_long_lines
        self.E_c_i = np.ones((int(s.s.sum()), bm_lines)) * b_r.E_c_i
        self.E_c = np.ones((int(s.s.sum()), bm_lines)) * b_r.E_c
        self.I_g_NC = np.ones((int(s.s.sum()), bm_lines)) * b_r.I_g_nc
        self.I_g_C_S1_S2 = np.ones((int(s.s.sum()), bm_lines)) * np.array(np.repeat(deck_df['I_c Stage 1'] + deck_df['I_c Stage 2'], 2))
        self.I_g_C_S3 = np.ones((int(s.s.sum()), bm_lines))  * np.array(np.repeat(deck_df['I_c Stage 3'], 2))
        
        "Initialize Dead Loads"
        self.w_NC_S1_S2 = np.array(np.repeat(deck_df['Stage 1 NC Wt'] + deck_df['Stage 2 NC Wt'], 2))#[np.newaxis, :, np.newaxis, np.newaxis]
        self.w_C_S1_S2 = np.array(np.repeat(deck_df['Stage 1 C Wt'] + deck_df['Stage 2 C Wt'], 2))#[np.newaxis, :, np.newaxis, np.newaxis]
        self.w_PC_S3 = np.array(np.repeat(deck_df['Stage 3 PC Wt'], 2))#[np.newaxis, :, np.newaxis, np.newaxis]
        self.w_C_S3 = np.array(np.repeat(deck_df['Stage 3 C Wt'], 2))#[np.newaxis, :, np.newaxis, np.newaxis]

        self._calc_deflections(b_r, b_l, s)

    "defl = aA / EI"
    "aA = x / L * ( L * gauss M(L) - gauss xM(L) ) - (x * gauss M(x) - gauss xM(x) )"
    def calc_aA(span, function_1, function_2, L_span, L_x, m):
        return ((L_span * gauss(function_1, np.zeros_like(L_x), L_span, m) -
                gauss(function_2, np.zeros_like(L_x), L_span, m)) * L_x / L_span -
                (L_x * gauss(function_1, np.zeros_like(L_x), L_x, m) -
                gauss(function_2, np.zeros_like(L_x), L_x, m)))

    def _calc_deflections(self, b_r, b_l, s):
        results = [[], [], [], [], []]
        for i in range(b_l.ns):
            start_idx, end_idx = (int(s.s[:i].sum()) if i > 0 else 0), int(s.s[:i+1].sum())
            L_brg_x = s.L_span_gen[start_idx:end_idx]

            #results[0].append(simple_span.calc_aA(i, lambda x: uniform_M(x, b_l.L_beam[i], b_r.b_weight), lambda x: x_uniform_M(x, b_l.L_beam[i], b_r.b_weight), b_l.L_beam[i], L_brg_x + 0.5, 1))
            results[0].append(b_r.b_weight * (L_brg_x + 0.5) / 24 * (b_l.L_beam[i] ** 3 - 2 * b_l.L_beam[i] * (L_brg_x + 0.5) ** 2 + (L_brg_x + 0.5) ** 3))
            for j, w in enumerate([self.w_NC_S1_S2, self.w_C_S1_S2, self.w_PC_S3, self.w_C_S3]):
                results[j+1].append(w * L_brg_x / 24 * (b_l.L_brg_brg[i] ** 3 - 2 * b_l.L_brg_brg[i] * L_brg_x ** 2 + L_brg_x ** 3))
                #results[j+1].append(simple_span.calc_aA(i, lambda x: uniform_M(x, b_l.L_brg_brg[i], w), lambda x: x_uniform_M(x, b_l.L_brg_brg[i], w), b_l.L_brg_brg[i], L_brg_x, 1))

        # Convert to deflections
        factor = 12 ** 3 / b_r.E_c
        self.defl_self_wt = np.concatenate(results[0]) * 12 ** 3 / b_r.E_c_i / b_r.I_g_nc
        self.defl_NC_S1_S2 = np.concatenate(results[1]) * factor / b_r.I_g_nc
        self.defl_C_S1_S2_in, self.defl_PC_S3_in = [np.concatenate(results[i]) * factor / self.I_g_C_S1_S2 for i in [2, 3]]
        self.defl_C_S3_in = np.concatenate(results[4]) * factor / self.I_g_C_S3

        return self

class continuous_deflections:
    def __init__(self, inputs, beam_rail_obj, beam_layout_obj, stations_obj, deck_sections_obj, defl_obj):
        #### INITIALIZE MATRICES ####
        b_r, b_l, s = beam_rail_obj, beam_layout_obj, stations_obj
        
        self.n_sub = len(inputs.substructure.sta_CL_sub)
        self.E_c_span = np.ones((b_l.ns, b_r.no_long_lines)) * beam_rail_obj.E_c
        self._calc_3_moment_method_defl(b_l, b_r.no_long_lines, s.s, s.L_span_gen, deck_sections_obj.deck_df, defl_obj)

    #### THREE-MOMENT METHOD OF COMPUTING INTERIOR SUPPORT MOMENTS FOR CONTINUOUS SPANS
    def calc_b(self, w, I_g_span, i, bm_lines):
        return -sum(w / 12 * (self.L_span[i + j] ** 3 / (4 * self.E_c_span[i + j] * I_g_span[i + j])) for j in range(2))
        #-6 * sum((self.L_span[i + j] * gauss(lambda x: uniform_M(x, self.L_span[i + j], w / 12), np.zeros((1, bm_lines)), self.L_span[i + j], 1).flatten() -
               #      gauss(lambda x: x_uniform_M(x, self.L_span[i + j], w / 12), np.zeros((1, bm_lines)), self.L_span[i + j], 1).flatten()) /
               #     (self.E_c_span[i + j, :] * I_g_span[i + j, :] * self.L_span[i + j]) for j in range(2))

    def calc_stiff(self, I_g_span, j, diff):
        if diff in [-1, 1]: return self.L_span[j] / self.E_c_span[j, :] / I_g_span[j, :]
        elif diff == 0: return 2 * self.L_span[j] / self.E_c_span[j, :] / I_g_span[j, :] + 2 * self.L_span[j + 1] / self.E_c_span[j + 1, :] / I_g_span[j + 1, :]
        else: return 0

    def calc_defl(self, M_matrix, I_g_span, i, L_brg_span):
        return -(M_matrix[i, :] * (L_brg_span ** 2 / 2 - L_brg_span ** 3 / 6 / self.L_span[i] - self.L_span[i] * L_brg_span / 3) +
             M_matrix[i + 1, :] * (L_brg_span ** 3 / 6 / self.L_span[i] - self.L_span[i] * L_brg_span / 6)) / (self.E_c_span[i, :] * I_g_span[i, :])

    def _calc_3_moment_method_defl(self, b_l, bm_lines, s, L_span_gen, deck_df, defl_obj):
        if self.n_sub > 2:
            #### INITIALIZE MATRICES ####
            b_C_S1_S2, b_PC_S3, b_C_S3 = [np.zeros((self.n_sub - 2, bm_lines)) for _ in range(3)]
            C_S1_S2_rot_stiff, PC_S3_rot_stiff, C_S3_rot_stiff = [np.zeros((self.n_sub - 2, self.n_sub - 2, bm_lines)) for _ in range(3)]
            #### INITIALIZE AND DEFINE SPAN LENGTHS AND PROPERTIES ####
            self.L_span = np.zeros(b_l.ns)
            I_g_C_S1_S2_span, I_g_C_S3_span = [np.zeros((b_l.ns, bm_lines)) for _ in range(2)]
            self.L_span[:] = b_l.L_brg_brg * 12
            I_g_C_S1_S2_span[:] = np.repeat(deck_df['I_c Stage 1'] + deck_df['I_c Stage 2'], 2)
            I_g_C_S3_span[:] = np.repeat(deck_df['I_c Stage 3'], 2)
            #### CALCULATE "b" MATRICES ####
            for i in range(self.n_sub - 2):
                b_C_S1_S2[i, :] = self.calc_b(defl_obj.w_C_S1_S2, I_g_C_S1_S2_span, i, bm_lines)
                b_PC_S3[i, :] = self.calc_b(defl_obj.w_PC_S3, I_g_C_S1_S2_span, i, bm_lines)
                b_C_S3[i, :] = self.calc_b(defl_obj.w_C_S3, I_g_C_S3_span, i, bm_lines)
                for j in range(self.n_sub - 2):
                    C_S1_S2_rot_stiff[i, j] = self.calc_stiff(I_g_C_S1_S2_span, j, j - i)
                    PC_S3_rot_stiff[i, j] = self.calc_stiff(I_g_C_S1_S2_span, j, j - i)
                    C_S3_rot_stiff[i, j] = self.calc_stiff(I_g_C_S3_span, j, j - i)
            #### INITIALIZE INTERNAL MOMENT MATRICES ####
            M_C_S1_S2, M_PC_S3, M_C_S3 = [np.zeros_like(b) for b in [b_C_S1_S2, b_PC_S3, b_C_S3]]
            #### SOLVE Ax = b WITH GAUSS-SEIDEL #### (guaranteed to converge when "A" is diagonally dominant by rows)
            for i in range(bm_lines):
                M_C_S1_S2[:, i], M_PC_S3[:, i], M_C_S3[:, i] = [gauss_seidel(A[:, :, i], b[:, i], 1e-6) for A, b in [(C_S1_S2_rot_stiff, b_C_S1_S2), (PC_S3_rot_stiff, b_PC_S3), (C_S3_rot_stiff, b_C_S3)]]
            #### ZERO MOMENTS AT PINNED SUPPORTS AND INITIALIZE DEFLECTIONS ####
            add_zeros = np.zeros((1, bm_lines))
            M_C_S1_S2, M_PC_S3, M_C_S3 = [np.concatenate((add_zeros, M, add_zeros), axis = 0) for M in [M_C_S1_S2, M_PC_S3, M_C_S3]]
            add_M_defl_C_S1_S2_i, add_M_defl_PC_S3_i, add_M_defl_C_S3_i = [], [], []
            #### COMPUTE DEFLECTIONS FROM ONLY INTERNAL MOMENTS ####
            for i in range(b_l.ns):
                start_index, L_brg_span = (0, L_span_gen[:int(s[0].sum())] * 12) if i == 0 else (int(s[:i].sum()), L_span_gen[int(s[:i].sum()):int(s[:i + 1].sum())] * 12)
                for defl_list, M_matrix, I_g_span in [(add_M_defl_C_S1_S2_i, M_C_S1_S2, I_g_C_S1_S2_span), (add_M_defl_PC_S3_i, M_PC_S3, I_g_C_S1_S2_span), (add_M_defl_C_S3_i, M_C_S3, I_g_C_S3_span)]:
                    defl_list.append(self.calc_defl(M_matrix, I_g_span, i, L_brg_span))
            #### SUM DEFLECTIONS FROM INTERNAL MOMENTS WITH SIMPLE SPAN MOMENTS ####
            defl_obj.defl_C_S1_S2 = np.concatenate(add_M_defl_C_S1_S2_i, axis = 0) + defl_obj.defl_C_S1_S2_in
            defl_obj.defl_PC_S3 = np.concatenate(add_M_defl_PC_S3_i, axis = 0) + defl_obj.defl_PC_S3_in
            defl_obj.defl_C_S3 = np.concatenate(add_M_defl_C_S3_i, axis = 0) + defl_obj.defl_C_S3_in
        else:
            defl_obj.defl_C_S1_S2 = defl_obj.defl_C_S1_S2_in
            defl_obj.defl_PC_S3 = defl_obj.defl_PC_S3_in
            defl_obj.defl_C_S3 = defl_obj.defl_C_S3_in
        return defl_obj

class variable_haunch:
    def __init__(self, inputs, vc_obj, beam_rail_obj, beam_layout_obj, stations_obj, deck_sections_obj, prestress_obj, defl_obj):
        inpb, b_r, b_l, s, d = inputs.bridge_info, beam_rail_obj, beam_layout_obj, stations_obj, defl_obj

        "Top of Slab Grade Elevations"
        self.TS_Elev = VerticalCurve.elev(vc_obj, s.sta_G) - abs(b_l.offsets) * inpb.rdwy_slope

        "New Variables used in rest of calculation"
        self.check_control_haunch = np.zeros((b_l.ns, b_r.no_long_lines))
        self.w_hnch = np.zeros((b_l.ns, b_r.no_long_lines))
        self.var_haunch_i = np.ones((int(s.s.sum()), b_r.no_long_lines))
        self.defl_var_haunch = np.zeros((int(s.s.sum()), b_r.no_long_lines))
        self.iter = 0

        "Calculate Deflections from Roadway Profile and Haunches"
        self._profile_deflections(vc_obj, inpb, b_r, b_l, s)
        self._adjust_defl_ends_to_brg(b_l.ns, s.s, prestress_obj.camber, d)
        self._calc_haunch_ht(b_r, b_l, s, d)

    def _profile_deflections(self, vc_obj, inpb, b_r, b_l, s):
        self.profile_deflections = np.zeros((int(s.s.sum()), b_r.no_long_lines))
        for i in range(b_l.ns):
            start, end = int(s.s[:i].sum()) if i > 0 else 0, int(s.s[:i+1].sum())
            #### THE REDUCTION BY 1 IS NEEDED FOR CORRECT INDEXING ####
            slope = (self.TS_Elev[start] - self.TS_Elev[end - 1]) / (s.sta_G[start] - s.sta_G[end - 1])
            self.profile_deflections[start:end] = self.TS_Elev[start:end] - (slope * (s.sta_G[start:end] - s.sta_G[start]) + self.TS_Elev[start])

        #### ADJUST END ELEVATIONS FOR CL BEARING ####
        first_last_indices = np.concatenate([np.array([int(s.s[:i].sum()) if i > 0 else 0, int(s.s[:i+1].sum()) - 1]) for i in range(b_l.ns)])
        s.sta_G[first_last_indices, :] = s.sta_x_10_ft[first_last_indices] + b_l.off * np.tan(np.deg2rad(inpb.skew))
        self.TS_Elev[first_last_indices, :] = VerticalCurve.elev(vc_obj, s.sta_G[first_last_indices, :]) - inpb.rdwy_slope * abs(b_l.off)
        return self

    def _adjust_defl_ends_to_brg(self, ns, s, camber, d):
    #### ADJUST DEFLECTIONS TO START AT THE BRG CENTERLINE ####
        self.camber_adj = np.zeros_like(camber)
        self.defl_self_wt_adj = np.zeros_like(d.defl_self_wt)
        for i in range(ns):
            start_index = int(s[:i].sum()) if i > 0 else 0
            end_index = int(s[:i+1].sum())
            self.camber_adj[start_index:end_index] = camber[start_index:end_index] - camber[start_index]
            self.defl_self_wt_adj[start_index:end_index, :] = d.defl_self_wt[start_index:end_index, :] - d.defl_self_wt[start_index, :]
        return self

    def _calc_haunch_ht(self, b_r, b_l, s, d):
        self.defl_final = 1.0 * (1.8 * self.camber_adj - 1.85 * self.defl_self_wt_adj) - (d.defl_NC_S1_S2 + d.defl_PC_S3) - (d.defl_C_S1_S2 + d.defl_C_S3)
        while self.iter < 50:

            #### INITIALIZE FOR EACH ITERATION ####
            self.iter += 1
            aA_moment_var_haunch = []

            #### DEFINE OLD HAUNCH ####
            var_haunch_prev = self.var_haunch_i.copy()

            for i in range(b_l.ns):
                start_index = int(s.s[:i].sum()) if i > 0 else 0
                end_index = int(s.s[:i+1].sum())
                L_brg_x = s.L_span_gen[start_index:end_index]

                #### SIMPLIFY TERMS, FINAL DEFLECTIONS ADJUSTED FOR OLD HAUNCH DEFLECTIONS ####
                pro_defl = self.profile_deflections[start_index:end_index, :]
                fin_defl = (self.defl_final[start_index:end_index, :] - self.defl_var_haunch[start_index:end_index, :]) / 12

                #### CALCULATE MAX DEFLECTION FROM PROFILE AND TOTAL CAMBER ####
                max_pro_defl = np.max(pro_defl, axis = 0) if np.max(pro_defl) > 0 else np.min(pro_defl, axis = 0)
                max_fin_defl = np.max(fin_defl, axis = 0)

                #### CALCULATE NEW HAUNCHES BASED ON OLD DEFLECTIONS ####
                haunch_thickness = np.where(max_pro_defl > max_fin_defl, pro_defl - fin_defl, (max_fin_defl - max_pro_defl)[np.newaxis, :] + pro_defl - fin_defl)
                self.var_haunch_i[start_index:end_index, :] = haunch_thickness

                #### CALCULATE SHAPE OF NEW HAUNCH WEIGHT ON BEAM ####
                self.check_control_haunch[i, :] = np.where(max_pro_defl > max_fin_defl, 1, 0)
                self.w_hnch[i, :] = np.max(haunch_thickness, axis = 0) / 12 * b_r.tf_width * 0.15

                M_eq_var_haunch = lambda x: np.where(self.check_control_haunch[i, :] == 1,
                                         quad_inv_para_M(x, b_l.L_brg_brg[i], self.w_hnch[i,:]),
                                         quad_para_M(x, b_l.L_brg_brg[i], self.w_hnch[i,:]))
                xM_eq_var_haunch = lambda x: np.where(self.check_control_haunch[i, :] == 1,
                                         x_quad_inv_para_M(x, b_l.L_brg_brg[i], self.w_hnch[i,:]),
                                         x_quad_para_M(x, b_l.L_brg_brg[i], self.w_hnch[i,:]))

                #### CALCULATE NEW DEFLECTIONS FROM NEW HAUNCH WEIGHT ####
                aA_moment_var_haunch.append(simple_span.calc_aA(i, lambda x: M_eq_var_haunch(x), \
                                        lambda x: xM_eq_var_haunch(x), b_l.L_brg_brg[i], L_brg_x, 1))

            self.defl_var_haunch = np.concatenate(aA_moment_var_haunch) * 12 ** 3 / b_r.E_c / b_r.I_g_nc

            #### CALCULATE DIFFERENCE BETWEEN OLD AND NEW HAUNCH THICKNESSES ####
            max_change = np.max(np.abs(self.var_haunch_i - var_haunch_prev))
            #print(f"Iteration {self.iter}: Maximum haunch change = {max_change:.6f}")

            #### IF OLD HAUNCHES ARE NOT TOO DIFFERENT FROM NEW HAUNCHES, STOP ####
            if max_change < 0.0001:
              #print("Haunch Thickness Converged")
              self.defl_final = 1.0 * (1.8 * self.camber_adj - 1.85 * self.defl_self_wt_adj) - (d.defl_NC_S1_S2 + self.defl_var_haunch + d.defl_PC_S3) - (d.defl_C_S1_S2 + d.defl_C_S3)
              break

        #### IF NO CONVERGENCE #########################################################
        #if self.iter >= 50:

            #print(f"Warning: Maximum iterations reached. Final change: {max_change:.6f}")
        return self

class min_camber_check:
    def __init__(self, beam_rail_obj, beam_layout_obj, stations_obj, defl_obj, final_haunch_obj):
        # Initialize
        b_r, b_l, s, d, f = beam_rail_obj, beam_layout_obj, stations_obj, defl_obj, final_haunch_obj
        self.min_camber_additional_haunch = np.zeros((b_l.ns, b_r.no_long_lines))
        self.w_addl = np.zeros((b_l.ns, b_r.no_long_lines))
        # Run
        self._min_camber_check(b_r, b_l, s, d, f)

    def _min_camber_check(self, b_r, b_l, s, d, f):
        aA_moment_min_camb_check = []
        for i in range(b_l.ns):
            start_index = int(s.s[:i].sum()) if i > 0 else 0
            end_index = int(s.s[:i+1].sum())
            L_brg_x = s.L_span_gen[start_index:end_index]
            self.min_camber_additional_haunch[i, :] = 0.6 * np.max(1.8 * f.camber_adj[start_index:end_index, :] - 1.85 * f.defl_self_wt_adj[start_index:end_index, :])
            self.w_addl[i] = self.min_camber_additional_haunch[i, :] / 12 * b_r.tf_width * 0.15

            aA_moment_min_camb_check.append(simple_span.calc_aA(i, lambda x: quad_inv_para_M(x, b_l.L_brg_brg[i], self.w_addl[i]), \
                                          lambda x: x_quad_inv_para_M(x, b_l.L_brg_brg[i], self.w_addl[i]), b_l.L_brg_brg[i], L_brg_x, 1))

        self.defl_min_camb_check = np.concatenate(aA_moment_min_camb_check) * 12 ** 3 / b_r.E_c / b_r.I_g_nc

        #### CHECK WHETHER MINIMUM CAMBER RESULTS IN NET NEGATIVE CAMBER ####
        self.defl_check = 0.7 * (1.8 * f.camber_adj - 1.85 * f.defl_self_wt_adj) - (d.defl_NC_S1_S2 + d.defl_PC_S3) - (d.defl_C_S1_S2 + d.defl_C_S3) - self.defl_min_camb_check
        if self.defl_check.any() < 0:
            self.check = "Negative"
            #print("OVERALL DEFLECTION NEGATIVE, REVISE DESIGN")
        else:
            self.check = "Positive"
            #print("OVERALL DEFLECTION POSITIVE, GOOD DESIGN")
        return self

class seat_elev:
    def __init__(self, inputs, beam_rail_obj, beam_layout_obj, stations_obj, deck_sections_obj, final_haunch_obj, min_haunch_check_obj):
        b_r, f, m = beam_rail_obj, final_haunch_obj, min_haunch_check_obj

        ns = beam_layout_obj.ns
        offsets = beam_layout_obj.offsets
        s = stations_obj.s
        over_deck_t = deck_sections_obj.over_deck_t

        self._calc_seat_elev(inputs, b_r, f, m, ns, offsets, s, over_deck_t)

    def _calc_seat_elev(self, inputs, b_r, f, m, ns, offsets, s, over_deck_t):
        self.min_haunch_GL = np.zeros((int(s.sum()), b_r.no_long_lines))
        for j in range(b_r.no_long_lines):
            self.min_haunch_GL[:, j] = 0 if ((offsets[0, j] < 0) == (j % 2 == 0)) else inputs.bridge_info.rdwy_slope * b_r.tf_width

        var_haunch = f.var_haunch_i + self.min_haunch_GL
        self.BS_Elev = f.TS_Elev - over_deck_t / 12
        self.Min_Haunch_Elev = self.BS_Elev - self.min_haunch_GL - 1 / 12
        self.TG_Elev = self.BS_Elev - var_haunch - 1 / 12
        self.TG_Check = self.TG_Elev - 0.6 * (1.8 * f.camber_adj - 1.85 * f.defl_self_wt_adj) / 12 - m.defl_min_camb_check / 12
        self.BG_Elev = self.TG_Elev - b_r.b_height / 12

        self.seat_elev = np.zeros((ns * 2, inputs.bridge_info.n_beams))
        self.SS_Height = np.zeros((ns * 2, inputs.bridge_info.n_beams))
        self.var_haunch_at_brg_CL = np.zeros((ns * 2, inputs.bridge_info.n_beams))

        for i in range(ns):
            start_index = int(s[:i].sum()) if i > 0 else 0
            end_index = int(s[:i+1].sum()) - 1
            for j in range(inputs.bridge_info.n_beams):
                self.seat_elev[2 * i, j] = min(self.BG_Elev[start_index, 2 * j], self.BG_Elev[start_index, 2 * j + 1]) - inputs.bridge_info.brg_thick
                self.seat_elev[2 * i + 1, j] = min(self.BG_Elev[end_index, 2 * j], self.BG_Elev[end_index, 2 * j + 1]) - inputs.bridge_info.brg_thick
                self.SS_Height[2 * i, j] = ((f.TS_Elev[start_index, 2 * j] - (self.BG_Elev[start_index, 2 * j] - inputs.bridge_info.brg_thick - 4 / 12)) +
                                             (f.TS_Elev[start_index, 2 * j + 1] - (self.BG_Elev[start_index, 2 * j + 1] - inputs.bridge_info.brg_thick - 4 / 12))) / 2
                self.SS_Height[2 * i + 1, j] = ((f.TS_Elev[end_index, 2 * j] - (self.BG_Elev[end_index, 2 * j] - inputs.bridge_info.brg_thick - 4 / 12)) +
                                                  (f.TS_Elev[end_index, 2 * j + 1] - (self.BG_Elev[end_index, 2 * j + 1] - inputs.bridge_info.brg_thick - 4 / 12))) / 2
                self.var_haunch_at_brg_CL[2 * i, j] = (f.var_haunch_i[start_index, 2 * j] + f.var_haunch_i[start_index, 2 * j + 1]) / 2
                self.var_haunch_at_brg_CL[2 * i + 1, j] = (f.var_haunch_i[end_index, 2 * j] + f.var_haunch_i[end_index, 2 * j + 1]) / 2

        self.profile_tan_line = np.max(f.profile_deflections, axis = 0) - f.profile_deflections + f.TS_Elev

@dataclass
class AnalysisResults:
    """Container for all bridge analysis results"""
    vc_obj: object = field(default=None)              # Vertical curve geometry
    beam_rail_obj: object = field(default=None)       # Beam and railing properties
    beam_layout_obj: object = field(default=None)     # Beam positioning and layout
    stations_obj: object = field(default=None)        # Station locations along spans
    deck_sections_obj: object = field(default=None)   # Section properties and dead loads
    prestress_obj: object = field(default=None)       # Prestressing forces and camber
    defl_obj: object = field(default=None)            # Simple span deflections
    con_span_defl_calc: object = field(default=None)  # Continuous span deflections
    final_haunch_obj: object = field(default=None)    # Variable haunch calculations
    min_haunch_check_obj: object = field(default=None)# Minimum haunch verification
    seat_obj: object = field(default=None)            # Bearing seat elevations
    avg_superstructure_elev: float = field(default=None)  # Average elevation of superstructure centerline

def run_analysis(inputs):
    """
    Main bridge analysis function for prestressed concrete girder bridges
    Sequential analysis: geometry → properties → forces → deflections → haunch design
    """
    results = AnalysisResults()

    # Step 1: Establish vertical curve geometry (VPC/VPT stations and elevations)
    results.vc_obj = VerticalCurve(inputs)

    # Step 2: Define beam cross-section and railing properties
    results.beam_rail_obj = beam_rail_info(inputs)

    # Step 3: Calculate beam layout and positioning across deck width
    results.beam_layout_obj = beam_layout(inputs, results.beam_rail_obj)

    # Step 4: Generate station points for analysis along each span
    results.stations_obj = stations_locations(inputs, results.beam_layout_obj, results.beam_rail_obj)

    # Step 5: Calculate section properties and dead load effects
    results.deck_sections_obj = section_properties_dead_loads(inputs, results.beam_layout_obj, results.beam_rail_obj)

    # Step 6: Determine prestressing forces and initial camber
    results.prestress_obj = PrestressingCamberCalculator(inputs, results.beam_rail_obj, results.beam_layout_obj, results.stations_obj)

    # Step 7: Calculate simple span deflections under all loads
    results.defl_obj = simple_span(inputs, results.beam_rail_obj, results.beam_layout_obj, results.stations_obj, results.deck_sections_obj)

    # Step 8: Analyze continuous span behavior and deflections
    results.con_span_defl_calc = continuous_deflections(inputs, results.beam_rail_obj, results.beam_layout_obj, results.stations_obj, results.deck_sections_obj, results.defl_obj)

    # Step 9: Design variable haunch to achieve target profile
    results.final_haunch_obj = variable_haunch(inputs, results.vc_obj, results.beam_rail_obj, results.beam_layout_obj, results.stations_obj, results.deck_sections_obj, results.prestress_obj, results.defl_obj)

    # Step 10: Verify minimum haunch requirements
    results.min_haunch_check_obj = min_camber_check(results.beam_rail_obj, results.beam_layout_obj, results.stations_obj, results.defl_obj, results.final_haunch_obj)

    # Step 11: Calculate final bearing seat elevations
    results.seat_obj = seat_elev(inputs, results.beam_rail_obj, results.beam_layout_obj, results.stations_obj, results.deck_sections_obj, results.final_haunch_obj, results.min_haunch_check_obj)

    # Step 12: Calculate average superstructure elevation (centerline of railing/deck/beam system)
    sta_elev = results.vc_obj.elev(results.stations_obj.sta_x_10_ft)
    offset = (results.beam_rail_obj.r_height - results.beam_rail_obj.b_height - results.deck_sections_obj.over_deck_t * 12) / 24
    results.avg_superstructure_elev = np.mean(sta_elev + offset)

    return results

