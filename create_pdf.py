# Commented out IPython magic to ensure Python compatibility.
# %pip install reportlab

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from io import BytesIO
from matplotlib.backends.backend_pdf import PdfPages
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus import Image

"""#Functions"""

def draw_title(c, text, x, y, font_size=20):
    c.setFont("Times-Bold", font_size)
    c.drawString(x, y, text)
    line_end_x = x + c.stringWidth(text, "Times-Bold", font_size)
    c.setStrokeColor(colors.black), c.setLineWidth(0.8), c.setDash([])
    c.line(x, y - 3, line_end_x, y - 3)
    return y

def title_block_and_borders(c, inputs):
    width, height = letter

    #### TITLE BLOCK PARAMETERS ####
    title_block_width, title_block_height = width - inch, 0.7 * inch
    title_block_x, title_block_y = 0.5 * inch, height - 0.5 * inch - title_block_height

    #### BORDER PARAMETERS ####
    border_x, border_y = title_block_x, 0.5 * inch
    border_width, border_height = title_block_width, height - title_block_height - 1.1 * inch

    #### DRAW BORDERS ####
    steel_blue, tan_color = colors.Color(0.27, 0.51, 0.71), colors.Color(0.96, 0.92, 0.84)
    c.setLineWidth(4), c.setStrokeColor(steel_blue), c.setFillColor(tan_color)
    c.rect(title_block_x, title_block_y, title_block_width, title_block_height, stroke = 1, fill = 1)
    c.rect(border_x, border_y, border_width, border_height, stroke = 1, fill = 0)

    #### TITLE BLOCK CONTENT ####
    try:
        from config_manager import get_embedded_logo
        logo_buffer = get_embedded_logo()
        logo = Image(logo_buffer, width=1.5*inch, height=0.5*inch)
    except Exception as e:
        raise Exception(f"Failed to load NDOT logo for PDF: {str(e)}")
    logo_x = title_block_x + 0.1 * inch
    logo_y = title_block_y + title_block_height - logo.drawHeight - 0.1 * inch
    logo.drawOn(c, logo_x, logo_y)

    c.setFillColor(colors.black), c.setFont("Times-Roman",8)
    col2_x, col2_y_start = width / 2, title_block_y + title_block_height - 0.25 * inch
    line_spacing = 10
    c.drawCentredString(col2_x, col2_y_start, f"Structure Number: {inputs.header.structure_number}")
    c.drawCentredString(col2_x, col2_y_start - line_spacing, f"Route Name: {inputs.header.route_name}")
    c.drawCentredString(col2_x, col2_y_start - 2 * line_spacing, f"Feature Crossed: {inputs.header.feature_crossed}")

    col3_x, col3_y_start = title_block_x + title_block_width - 0.1 * inch, title_block_y + title_block_height - 0.3 * inch
    c.drawRightString(col3_x, col3_y_start, f"Designer Name: {inputs.header.designer_name}   Date: {inputs.header.designer_date}")
    c.drawRightString(col3_x, col3_y_start - 1.2 * line_spacing, f"Reviewer Name: {inputs.header.reviewer_name}   Date: {inputs.header.reviewer_date}")

def create_beam_cx(results):
  beam_ht = results.beam_rail_obj.b_height
  tf_width = results.beam_rail_obj.tf_width * 12
  #### NU BEAMS ####
  if results.beam_rail_obj.is_NU == True:
    x = []
    y = []
    theta_bot = np.arctan(5.5/(38.375/2-(5+15/16)/2))
    theta_top = np.arctan(1.75/(48.25/2-(5+15/16)/2))
    R_stem = 7.875
    R_flng = 2
    d_top_flng = R_flng * np.tan(np.pi/4 - theta_top / 2)
    d_bot_flng = R_flng * np.tan(np.pi/4 - theta_bot / 2)
    d_top_stem = R_stem * np.tan(np.pi/4 - theta_top / 2)
    d_bot_stem = R_stem * np.tan(np.pi/4 - theta_bot / 2)
    bf_width = 38.375
    thick_w = 5 + 15 / 16
    champfer = 0.75
    no = 50

    #### POINTS ####

    # Start and Champfer
    x.append((tf_width - bf_width - champfer * 2) / 2), y.append(0)
    x.append(x[0] - champfer), y.append(y[0] + champfer)

    # Curve at Bottom Flange Edge
    x_curve_start, y_curve_start = x[1], 5 + 5 / 16 - d_bot_flng
    x.append(x_curve_start), y.append(y_curve_start)
    x_curve_end = x[2] + d_bot_flng * np.cos(theta_bot)
    y_curve_end = y[2] + d_bot_flng * (1 + np.sin(theta_bot))
    # Define all x spaces between first and last point
    x_bt_lft_fl = np.linspace(x_curve_start, x_curve_end, no)
    # Define Circle X-Coordinates
    x_cir = R_flng - (x_bt_lft_fl - x_curve_start)
    # Append X-Coordinates, Use Circle Coordinates to define and append y
    for i in range(no):
      x.append(x_bt_lft_fl[i]), y.append(y_curve_start + np.sqrt(R_flng ** 2 - x_cir[i] ** 2))

    # Curve at Bottom of Stem
    x_curve_end = tf_width / 2 - thick_w / 2
    y_curve_end = 5.5 + 5 + 5 / 16 + d_bot_stem
    # Define all x spaces between first and last point
    x_bt_lft_stm = np.linspace(x_curve_end - d_bot_stem * np.cos(theta_bot), x_curve_end, no)
    # Define Circle X-Coordinates
    x_cir = R_stem - (x_curve_end - x_bt_lft_stm)
    # Append X-Coordinates, Use Circle Coordinates to define and append y
    for i in range(no):
      x.append(x_bt_lft_stm[i]), y.append(y_curve_end - np.sqrt(R_stem ** 2 - x_cir[i] ** 2))

    # Curve at Top of Stem
    x_curve_start, y_curve_start = tf_width / 2 - thick_w / 2, beam_ht - 2 - 9 / 16 - 1.75 - d_top_stem
    x_curve_end = tf_width / 2 - thick_w / 2 - d_top_stem * np.cos(theta_top)
    y_curve_end = beam_ht - 2 - 9 / 16 - 1.75 + d_top_stem * np.sin(theta_top)
    # Define all x spaces between first and last point
    x_tp_lft_stm = np.linspace(x_curve_start, x_curve_end, no)
    # Define Circle X-Coordinates
    x_cir = R_stem  - (x_curve_start - x_tp_lft_stm)
    # Append X-Coordinates, Use Circle Coordinates to define and append y
    for i in range(no):
      x.append(x_tp_lft_stm[i]), y.append(y_curve_start + np.sqrt(R_stem ** 2 - x_cir[i] ** 2))

    # Curve at Top Flange Edge
    x_curve_start, y_curve_start = d_top_flng * np.cos(theta_top), beam_ht - (2 + 9 / 16 + d_top_flng * np.sin(theta_top))
    x_curve_end, y_curve_end = 0, beam_ht - (2 + 9 / 16 - d_top_flng)
    # Define all x spaces between first and last point
    x_tp_lft_flng = np.linspace(x_curve_start, x_curve_end, no)
    # Define Circle X-Coordinates
    x_cir = R_flng - (x_tp_lft_flng - x_curve_end)
    # Append X-Coordinates, Use Circle Coordinates to define and append y
    for i in range(no):
      x.append(x_tp_lft_flng[i]), y.append(y_curve_end - np.sqrt(R_flng ** 2 - x_cir[i] ** 2))

    # Flat Top of Beam
    x.append(0), y.append(beam_ht)
    x.append(tf_width), y.append(beam_ht)

    # Curve at Top Flange Edge
    x_curve_start, y_curve_start = tf_width, beam_ht - (2 + 9 / 16 - d_top_flng)
    x_curve_end, y_curve_end = tf_width - d_top_flng * np.cos(theta_top), beam_ht - (2 + 9 / 16 + d_top_flng * np.sin(theta_top))
    # Define all x spaces between first and last point
    x_tp_rt_flng = np.linspace(x_curve_start, x_curve_end, no)
    # Define Circle X-Coordinates
    x_cir = R_flng - (x_curve_start - x_tp_rt_flng)
    # Append X-Coordinates, Use Circle Coordinates to define and append y
    for i in range(no):
      x.append(x_tp_rt_flng[i]), y.append(y_curve_start - np.sqrt(R_flng ** 2 - x_cir[i] ** 2))

    # Curve at Top of Stem
    x_curve_start, y_curve_start = tf_width / 2 + thick_w / 2 + d_top_stem * np.cos(theta_top), beam_ht - (2 + 9 / 16 + 1.75) + d_top_stem * np.sin(theta_top)
    x_curve_end, y_curve_end = tf_width / 2 + thick_w / 2, beam_ht - (2 + 9 / 16 + 1.75 + d_top_stem)
    # Define all x spaces between first and last point
    x_tp_rt_stm = np.linspace(x_curve_start, x_curve_end, no)
    # Define Circle X-Coordinates
    x_cir = R_stem - (x_tp_rt_stm - x_curve_end)
    # Append X-Coordinates, Use Circle Coordinates to define and append y
    for i in range(no):
      x.append(x_tp_rt_stm[i]), y.append(y_curve_end + np.sqrt(R_stem ** 2 - x_cir[i] ** 2))

    # Curve at Bottom of Stem
    x_curve_start, y_curve_start = tf_width / 2 + thick_w / 2, 5.5 + 5 + 5 / 16 + d_bot_stem
    x_curve_end, y_curve_end = tf_width / 2 + thick_w / 2 + d_bot_stem * np.cos(theta_bot), 5.5 + 5 + 5 / 16 - d_bot_stem * (1 + np.sin(theta_bot))
    # Define all x spaces between first and last point
    x_bt_rt_stm = np.linspace(x_curve_start, x_curve_end, no)
    # Define Circle X-Coordinates
    x_cir = R_stem - (x_bt_rt_stm - x_curve_start)
    # Append X-Coordinates, Use Circle Coordinates to define and append y
    for i in range(no):
      x.append(x_bt_rt_stm[i]), y.append(y_curve_start - np.sqrt(R_stem ** 2 - x_cir[i] ** 2))

    # Curve at Bottom Flange Edge
    x_curve_start, y_curve_start = tf_width / 2 + bf_width / 2 - d_bot_flng * np.cos(theta_bot), 5 + 5 / 16 + d_bot_flng * np.sin(theta_bot)
    x_curve_end, y_curve_end = tf_width / 2 + bf_width / 2, 5 + 5 / 16 - d_bot_flng
    # Define all x spaces between first and last point
    x_bt_rt_flng = np.linspace(x_curve_start, x_curve_end, no)
    # Define Circle X-Coordinates
    x_cir = R_flng - (x_curve_end - x_bt_rt_flng)
    # Append X-Coordinates, Use Circle Coordinates to define and append y
    for i in range(no):
      x.append(x_bt_rt_flng[i]), y.append(y_curve_end + np.sqrt(R_flng ** 2 - x_cir[i] ** 2))

    # Champfer
    x.append(x_curve_end), y.append(champfer)
    x.append(x_curve_end - champfer), y.append(0)
    x.append((tf_width - bf_width - champfer * 2) / 2), y.append(0)

  elif results.beam_rail_obj.is_IT == True:
    print("UPDATE CODE")
    x, y = 0, 0

  return x, y

def create_rail_cx(inputs, results):
  ht = results.beam_rail_obj.b_height
  rail_shape = inputs.bridge_info.rail_shape
  x = []
  y = []
  if rail_shape == ('39_SSCR'):
    x.append(0), y.append(0)
    x.append(0), y.append(ht - 0.75)
    x.append(0.75), y.append(ht)
    x.append(8 - 0.75), y.append(ht)
    x.append(8), y.append(ht - 0.75)
    x.append(10), y.append(0)
  elif rail_shape == ('39_OCR'):
    x.append(0), y.append(0)
    x.append(0), y.append(12 - 0.75)
    x.append(0.75), y.append(12)
    x.append(0), y.append(12 + 0.75)
    x.append(0), y.append(ht - 0.75)
    x.append(0.75), y.append(ht)
    x.append(14 - 0.75), y.append(ht)
    x.append(14), y.append(ht - 0.75)
    x.append(14), y.append(12 + 0.75)
    x.append(14 - 0.75), y.append(12)
    x.append(0.75), y.append(12)
    x.append(10), y.append(12)
    x.append(10), y.append(0)
  elif rail_shape == ('42_NU_O'):
    x.append(0), y.append(0)
    x.append(0), y.append(11 - 0.75)
    x.append(0.75), y.append(11)
    x.append(0), y.append(11 + 0.75)
    x.append(0), y.append(ht - 0.75)
    x.append(0.75), y.append(ht)
    x.append(8.5 - 0.75), y.append(ht)
    x.append(8.5), y.append(ht - 0.75)
    x.append(9.5), y.append(ht - 8)
    x.append(14), y.append(ht - 8 - 2)
    x.append(14), y.append(11 + 1)
    x.append(10.5), y.append(11)
    x.append(0.75), y.append(11)
    x.append(10.5), y.append(11)
    x.append(10.5), y.append(0)
  elif rail_shape == ('42_NU_C'):
    x.append(0), y.append(0)
    x.append(0), y.append(ht - 0.75)
    x.append(0.75), y.append(ht)
    x.append(8.5 - 0.75), y.append(ht)
    x.append(8.5), y.append(ht - 0.75)
    x.append(9.5), y.append(ht - 8)
    x.append(14), y.append(ht - 8 - 2)
    x.append(14), y.append(11 + 1)
    x.append(10.5), y.append(11)
    x.append(10.5), y.append(0)
  elif rail_shape == ('42_NU_M'):
    x.append(3.5), y.append(0)
    x.append(3.5), y.append(11)
    x.append(0), y.append(12)
    x.append(0), y.append(32)
    x.append(4.5), y.append(34)
    x.append(5.5), y.append(42 - 0.75)
    x.append(5.5 + 0.75), y.append(42)
    x.append(18.5 - 0.75), y.append(42)
    x.append(18.5), y.append(42 - 0.75)
    x.append(19.5), y.append(34)
    x.append(24), y.append(32)
    x.append(24), y.append(12)
    x.append(20.5), y.append(11)
    x.append(20.5), y.append(0)
  elif rail_shape == ('34_NU_O'):
    x.append(0), y.append(0)
    x.append(0), y.append(11 - 0.75)
    x.append(0.75), y.append(11)
    x.append(0), y.append(11 + 0.75)
    x.append(0), y.append(ht - 0.75)
    x.append(0.75), y.append(ht)
    x.append(14 - 0.75), y.append(ht)
    x.append(14), y.append(ht - 0.75)
    x.append(14), y.append(11 + 0.75)
    x.append(14 - 0.75), y.append(11)
    x.append(0.75), y.append(11)
    x.append(10.5), y.append(11)
    x.append(10.5), y.append(0)
  elif rail_shape == ('34_NU_C'):
    x.append(0), y.append(0)
    x.append(0), y.append(ht - 0.75)
    x.append(0.75), y.append(ht)
    x.append(14 - 0.75), y.append(ht)
    x.append(14), y.append(ht - 0.75)
    x.append(14), y.append(11 + 0.75)
    x.append(14 - 0.75), y.append(11)
    x.append(10.5), y.append(11)
    x.append(10.5), y.append(0)
  elif rail_shape == ('29_NE_O'):
    x.append(1), y.append(0)
    x.append(1), y.append(13)
    x.append(0.75), y.append(13)
    x.append(0), y.append(13 + 0.75)
    x.append(0), y.append(ht - 0.75)
    x.append(0.75), y.append(ht)
    x.append(14 - 0.75), y.append(ht)
    x.append(14), y.append(ht - 0.75)
    x.append(14), y.append(13 + 0.75)
    x.append(14 - 0.75), y.append(13)
    x.append(0.75), y.append(13)
    x.append(10.5), y.append(13)
    x.append(10.5), y.append(0)
  elif rail_shape == ('29_NE_C'):
    x.append(1), y.append(0)
    x.append(1), y.append(13)
    x.append(0.75), y.append(13)
    x.append(0), y.append(13 + 0.75)
    x.append(0), y.append(ht - 0.75)
    x.append(0.75), y.append(ht)
    x.append(14 - 0.75), y.append(ht)
    x.append(14), y.append(ht - 0.75)
    x.append(14), y.append(13 + 0.75)
    x.append(14 - 0.75), y.append(13)
    x.append(10.5), y.append(13)
    x.append(10.5), y.append(0)
  elif rail_shape == ('42_NJ'):
    x.append(0), y.append(0)
    x.append(0), y.append(ht - 0.75)
    x.append(0.75), y.append(ht)
    x.append(7 - 0.75), y.append(ht)
    x.append(7), y.append(ht - 0.75)
    x.append(7), y.append(ht - 10)
    x.append(9), y.append(13)
    x.append(16), y.append(3)
    x.append(16), y.append(0)
  elif rail_shape == ('32_NJ'):
    x.append(0), y.append(0)
    x.append(0), y.append(ht - 0.75)
    x.append(0.75), y.append(ht)
    x.append(7 - 0.75), y.append(ht)
    x.append(7), y.append(ht - 0.75)
    x.append(9), y.append(13)
    x.append(16), y.append(3)
    x.append(16), y.append(0)
  else:
    print("UPDATE CODE FOR PRINTING NEW RAIL SHAPE")
    x, y = 0, 0

  return x, y

def create_plot(c, inputs, results, x_offset, y_offset, width, height):
    vc = results.vc_obj
    inp = inputs.vertical_curve
    sta_CL_sub = inputs.substructure.sta_CL_sub

    #### PLOT BOUNDARIES ####
    plot_start = min(vc.sta_VPC - 50, sta_CL_sub[0] - 20)
    plot_end = max(vc.sta_VPT + 50, sta_CL_sub[-1] + 20)
    
    #### STATIONS AND ELEVATIONS ####
    stations = np.linspace(plot_start, plot_end, 1000)
    elevations = [vc.elev(sta) for sta in stations]

    #### SCALE FOR PLOTTING ####
    min_sta, max_sta = plot_start, plot_end
    min_elev, max_elev = min(elevations) - 10, max(elevations) + 15

    scale_init = lambda elevation: y_offset + (elevation - min_elev) / (max_elev - min_elev) * height
    bot_graph = min(scale_init(inp.elev_VPI + inp.grade_1), scale_init(inp.elev_VPI - inp.grade_2), y_offset)

    scale_x = lambda station: x_offset + (station - min_sta) / (max_sta - min_sta) * width
    scale_y = lambda elevation: (y_offset + (y_offset - bot_graph) + 15) + (elevation - min_elev) / (max_elev - min_elev) * height

    #### MAIN PROFILE LINE ####
    path = c.beginPath()
    path.moveTo(scale_x(stations[0]), scale_y(elevations[0]))
    for i in range(1, len(stations)):
        path.lineTo(scale_x(stations[i]), scale_y(elevations[i]))
    c.setLineWidth(1), c.drawPath(path, stroke=1, fill=0)

    #### GRADE LINES ####
    c.setLineWidth(1), c.setDash([3, 3])

    #### ONE ####
    grade1_start_sta, grade1_end_sta = plot_start, inp.sta_VPI + 100
    grade1_start_elev = inp.elev_VPI + inp.grade_1/100 * (grade1_start_sta - inp.sta_VPI)
    grade1_end_elev = inp.elev_VPI + inp.grade_1/100 * (grade1_end_sta - inp.sta_VPI)
    c.line(scale_x(grade1_start_sta), scale_y(grade1_start_elev),
                 scale_x(grade1_end_sta), scale_y(grade1_end_elev))

    #### TWO ####
    grade2_start_sta, grade2_end_sta = inp.sta_VPI - 100, plot_end
    grade2_start_elev = inp.elev_VPI + inp.grade_2/100 * (grade2_start_sta - inp.sta_VPI)
    grade2_end_elev = inp.elev_VPI + inp.grade_2/100 * (grade2_end_sta - inp.sta_VPI)
    c.line(scale_x(grade2_start_sta), scale_y(grade2_start_elev),
                 scale_x(grade2_end_sta), scale_y(grade2_end_elev))

    #### GRADE LINE LABELS ####
    c.setFont("Times-Roman", 8)
    adj = 8 if inp.grade_1 > 0 else -8
    grade1_mid_sta = (grade1_start_sta + inp.sta_VPI) / 2
    grade1_mid_elev = inp.elev_VPI + inp.grade_1/100 * (grade1_mid_sta - inp.sta_VPI)
    x_adj = c.stringWidth(f"Grade 1: +0.0000%", "Times-Roman", 8)
    c.drawString(scale_x(grade1_mid_sta) - x_adj, scale_y(grade1_mid_elev) + adj, f"Grade 1: {inp.grade_1:.4f}%")

    adj = -8 if inp.grade_2 > 0 else 8
    grade2_mid_sta = (inp.sta_VPI + grade2_end_sta) / 2
    grade2_mid_elev = inp.elev_VPI + inp.grade_2/100 * (grade2_mid_sta - inp.sta_VPI)
    c.drawString(scale_x(grade2_mid_sta), scale_y(grade2_mid_elev) + adj, f"Grade 2: {inp.grade_2:.4f}%")

    #### VPI POINT ####
    c.setFillColor(colors.black), c.setDash([])
    c.circle(scale_x(inp.sta_VPI), scale_y(inp.elev_VPI), 3, stroke=1, fill=1)

    #### CURVE ENDS ####
    c.setFillColor(colors.white)
    c.circle(scale_x(vc.sta_VPC), scale_y(vc.elev(vc.sta_VPC)), 4.5, stroke=1, fill=1)
    c.circle(scale_x(vc.sta_VPT), scale_y(vc.elev(vc.sta_VPT)), 4.5, stroke=1, fill=1)

    #### STRUCTURE LIMITS ####
    if sta_CL_sub[0] and sta_CL_sub[-1]:
        elev_ab1 = vc.elev(sta_CL_sub[0])
        elev_ab2 = vc.elev(sta_CL_sub[-1])

        structure_elev = max(elev_ab1, elev_ab2) + 5
        horiz_line_y = scale_y(structure_elev)
        vert_line_top = horiz_line_y + 2.25

        c.line(scale_x(sta_CL_sub[0]), scale_y(elev_ab1), scale_x(sta_CL_sub[0]), vert_line_top)
        c.line(scale_x(sta_CL_sub[-1]), scale_y(elev_ab2), scale_x(sta_CL_sub[-1]), vert_line_top)
        c.line(scale_x(sta_CL_sub[0]), horiz_line_y, scale_x(sta_CL_sub[-1]), horiz_line_y)

        mid_station = (sta_CL_sub[0] + sta_CL_sub[-1]) / 2
        c.setFont("Times-Roman", 6), c.setFillColor(colors.black)
        c.drawCentredString(scale_x(mid_station), horiz_line_y + 3, "Structure")
        c.drawCentredString(scale_x(mid_station), horiz_line_y - 8, "Limits")

    #### HIGHLIGHT STRUCTURE LOCATION ####
    if sta_CL_sub[0] and sta_CL_sub[-1]:
        c.setLineWidth(3)
        struct_stations = [sta for sta in stations if sta_CL_sub[0] <= sta <= sta_CL_sub[-1]]
        struct_elevations = [elevations[i] for i, sta in enumerate(stations) if sta_CL_sub[0] <= sta <= sta_CL_sub[-1]]
        if struct_stations:
            path = c.beginPath()
            path.moveTo(scale_x(struct_stations[0]), scale_y(struct_elevations[0]))
            for i in range(1, len(struct_stations)):
                path.lineTo(scale_x(struct_stations[i]), scale_y(struct_elevations[i]))
            c.drawPath(path, stroke=1, fill=0)

def bridge_figure_sta_elev_points(c, inputs, results):
    width, height = letter

    #### INPUTS ####
    rdwy_width = inputs.bridge_info.rdwy_width
    n_beams = inputs.bridge_info.n_beams
    skew = inputs.bridge_info.skew
    turn_width = inputs.bridge_info.turn_width
    sta_CL_sub = inputs.substructure.sta_CL_sub
    off = results.beam_layout_obj.off
    offsets = results.beam_layout_obj.offsets
    span = results.beam_layout_obj.span
    s = results.stations_obj.s
    sta_x_10_ft = results.stations_obj.sta_x_10_ft
    sta_G = results.stations_obj.sta_G

    #### TITLE ####
    title_y = draw_title(c, "Bridge Stations Plan View", inch, height - 1.5 * inch - 8)

    #### PLOT PARAMETERS ####
    plot_width = width - 1.25 * inch
    plot_height = rdwy_width / span.sum() * plot_width
    plot_x, plot_y = 0.75 * inch, title_y - plot_height - 0.1 * inch
    all_stations = np.concatenate([np.array(np.min(sta_x_10_ft) - 5).reshape(-1,1), sta_x_10_ft, np.array(np.max(sta_x_10_ft) + 5).reshape(-1,1)])
    all_offsets = np.concatenate([np.array(np.min(offsets) - 5).reshape(-1,1), offsets, np.array(np.max(offsets) + 5).reshape(-1,1)], axis = 1)
    min_station, max_station, min_offset, max_offset = np.min(all_stations), np.max(all_stations), np.min(all_offsets), np.max(all_offsets)

    #### SCALING FUNCTIONS ####
    station_to_x = lambda station: plot_x + (station - min_station) / (max_station - min_station) * plot_width
    offset_to_y = lambda offset: plot_y + (offset - min_offset) / (max_offset - min_offset) * plot_height

    #### PLOT BEAM FLANGE EDGES AND X POINTS ####
    span_start_idx = 0
    c.setFont("Times-Roman", 6)
    for beam_idx in range(n_beams):
        c.drawString(0.65 * inch, offset_to_y(off[0][2 * beam_idx]), f"B{beam_idx + 1}")
    for span_idx, span_points in enumerate(s):
        span_end_idx = int(span_start_idx + span_points)
        for beam_idx in range(n_beams):
            shot_stations = sta_G[span_start_idx:span_end_idx, 2 * beam_idx]
            left_flange_offset, right_flange_offset = offsets[:, 2 * beam_idx], offsets[:, 2 * beam_idx + 1]

            #### FLANGE LINES ####
            c.setStrokeColor(colors.blue), c.setLineWidth(1), c.setDash([])
            for i in range(len(shot_stations) - 1):
                x1, x2 = station_to_x(shot_stations[i]), station_to_x(shot_stations[i + 1])
                c.line(x1, offset_to_y(left_flange_offset), x2, offset_to_y(left_flange_offset))
                c.line(x1, offset_to_y(right_flange_offset), x2, offset_to_y(right_flange_offset))

            #### BEAM CENTERLINE ####
            c.setStrokeColor(colors.grey), c.setLineWidth(0.5), c.setDash([3, 3])
            centerline_offset = off[0, 2 * beam_idx]
            for i in range(len(shot_stations) - 1):
                x1, x2 = station_to_x(shot_stations[i]), station_to_x(shot_stations[i + 1])
                c.line(x1, offset_to_y(centerline_offset), x2, offset_to_y(centerline_offset))

            #### MARK SHOT POINTS ####
            for j, station in enumerate(shot_stations):
                x = station_to_x(station)
                if j != 0 and j != len(shot_stations) - 1: #### NOT BEARING POINTS ####
                    c.setFont("Helvetica", 7)
                    c.drawCentredString(x, offset_to_y(left_flange_offset) - 2.25, "x")
                    c.drawCentredString(x, offset_to_y(right_flange_offset) - 2.25, "x")
                    if beam_idx == n_beams - 1:
                        c.setFont("Times-Roman", 6)
                        if (station_to_x(station) - station_to_x(shot_stations[j - 1]) < 20) & (j > 1):
                            c.drawCentredString(x, offset_to_y(right_flange_offset) - 28, f"S{j}")
                        else:
                            c.drawCentredString(x, offset_to_y(right_flange_offset) - 20, f"S{j}")

        span_start_idx = span_end_idx

    #### SUBSTRUCTURE AND BEARING CENTERLINES ####
    line_bottom_y, line_top_y = offset_to_y(min_offset), offset_to_y(max_offset)
    line_length, total_x_offset = max_offset - min_offset, (max_offset - min_offset) * np.tan(np.radians(skew)) if skew != 0 else 0
    for sub_idx, sub_station in enumerate(sta_CL_sub):
        #### SUBSTRUCTURE CL ####
        if skew != 0:
            x1, x2 = station_to_x(sub_station - total_x_offset/2), station_to_x(sub_station + total_x_offset/2)
        else:
            x1 = x2 = station_to_x(sub_station)
        c.line(x1, line_bottom_y, x2, line_top_y)

        #### BEARING CL AT PIERS ####
        bearing_stations = [sub_station - 10/12, sub_station + 10/12] if 0 < sub_idx < len(sta_CL_sub) - 1 else [sub_station]
        for bearing_station in bearing_stations:
            if skew != 0:
                x1_bear, x2_bear = station_to_x(bearing_station - total_x_offset/2), station_to_x(bearing_station + total_x_offset/2)
            else:
                x1_bear = x2_bear = station_to_x(bearing_station)
            if bearing_station != sub_station:
                c.line(x1_bear, line_bottom_y, x2_bear, line_top_y)

            #### MARK BEARING POINTS ####
            c.setFillColor(colors.red), c.setFont("Times-Roman", 12)
            for beam_idx in range(n_beams):
                centerline_offset = off[0, 2 * beam_idx]
                y_triangle = offset_to_y(centerline_offset)
                if skew != 0:
                    # Interpolate x position based on y position
                    y_fraction = (centerline_offset - min_offset) / (max_offset - min_offset)
                    x_triangle = x1_bear + y_fraction * (x2_bear - x1_bear)
                else:
                    x_triangle = x1_bear
                c.drawCentredString(x_triangle, y_triangle - 6, "^")

    #### ABUT AND PIER TURNDOWN EDGES ####
    c.setStrokeColor(colors.blue), c.setDash([]), c.setLineWidth(1)
    line_bottom_y, line_top_y = offset_to_y(min_offset + 2), offset_to_y(max_offset - 2)
    for sub_idx, sub_station in enumerate(sta_CL_sub):
        if sub_idx == 0 or sub_idx == len(sta_CL_sub) - 1: #### ABUTMENTS ####
            turndown_station = sub_station + (0.5 if sub_idx == 0 else -0.5)
            turndown_stations = [turndown_station]
        else: #### PIERS ####
            turndown_stations = [sub_station - turn_width/2, sub_station + turn_width/2]
        for turndown_station in turndown_stations:
            if skew != 0:
                line_length_turn = (max_offset - 2) - (min_offset + 2)
                total_x_offset_turn = line_length_turn * np.tan(np.radians(skew))
                x1_turn, x2_turn = station_to_x(turndown_station - total_x_offset_turn/2), station_to_x(turndown_station + total_x_offset_turn/2)
            else:
                x1_turn = x2_turn = station_to_x(turndown_station)
            c.line(x1_turn, line_bottom_y, x2_turn, line_top_y)

    #### LEGEND ####
    legend_y = plot_y - 0.3 * inch
    legend_items = [
        (colors.grey, 0.5, [3, 3], "Centerline", "red", "^", "Bearing Point"),
        (colors.blue, 1, [], "Structural Unit", "black", "x", "Shot Point")
    ]

    for i, (line_color, line_width, dash_pattern, line_label, symbol_color, symbol, symbol_label) in enumerate(legend_items):
        y_pos = legend_y - i * 0.3 * inch
        c.setStrokeColor(line_color), c.setLineWidth(line_width), c.setDash(dash_pattern)
        c.line(0.75 * inch, y_pos, 1.05 * inch, y_pos)
        c.setFillColor(colors.black), c.setFont("Times-Roman", 10)
        c.drawString(1.15 * inch, y_pos - 3, line_label)
        c.drawString(2.65 * inch, y_pos - 3, symbol_label)
        c.setFillColor(getattr(colors, symbol_color))
        c.setFont("Times-Roman" if symbol == "^" else "Helvetica", 12 if symbol == "^" else 7)
        c.drawString(2.5 * inch, y_pos - (5.5 if symbol == "^" else 1.5), symbol)

    return legend_y - 0.3 * inch

class BridgeDesign3DVisualizer:
    def __init__(c, inputs, results):
        #### INPUTS ####
        n_beams = inputs.bridge_info.n_beams
        ns = results.beam_layout_obj.ns
        offsets = results.beam_layout_obj.offsets
        off = results.beam_layout_obj.off
        span = results.beam_layout_obj.span
        s = results.stations_obj.s
        sta_x_10_ft = results.stations_obj.sta_x_10_ft
        sta_G = results.stations_obj.sta_G
        over_deck_t = results.deck_sections_obj.over_deck_t
        TS_Elev = results.final_haunch_obj.TS_Elev
        BS_Elev = results.seat_obj.BS_Elev
        Min_Haunch_Elev = results.seat_obj.Min_Haunch_Elev
        TG_Elev = results.seat_obj.TG_Elev

        #### REMOVE CL BEARING LOCATIONS FROM ARRAY FOR PLOTTING ####
        to_remove = []
        for i in range(ns):
          start_index = int(s[:i].sum()) if i > 0 else 0
          end_index = int(s[:i+1].sum()) - 1
          to_remove.append(start_index)
          to_remove.append(end_index)

        c.sta_G = np.array(np.delete(sta_G, to_remove, axis=0))
        c.TG_Elev = np.array(np.delete(TG_Elev, to_remove, axis=0))
        c.Min_Haunch_Elev = np.array(np.delete(Min_Haunch_Elev, to_remove, axis=0))
        c.BS_Elev = np.array(np.delete(BS_Elev, to_remove, axis=0))
        c.TS_Elev = np.array(np.delete(TS_Elev, to_remove, axis=0))
        c.offsets = np.array(offsets[0])
        c.off = np.array(off[0])

        #### MESHGRID ####
        c.n_points, c.n_girders = c.sta_G.shape

    def create_haunch_surfaces(c):
        surfaces = {}
        X = c.sta_G
        Y = np.tile(c.offsets, (c.n_points, 1))
        surfaces['Minimum_Haunch'] = {
            'X': X,
            'Y': Y,
            'Z_top': c.BS_Elev,
            'Z_bot': c.Min_Haunch_Elev + 0.0005,
            'color': 'lightcoral'
        }
        surfaces['Variable_Haunch'] = {
            'X': X,
            'Y': Y,
            'Z_top': c.Min_Haunch_Elev - 0.0005,
            'Z_bot': c.TG_Elev,
            'color': 'lightblue'
        }
        return surfaces

    def plot_3d_bridge(c, inputs, results, fig_size=(15, 10)):
        ns = results.beam_layout_obj.ns
        s = results.stations_obj.s
        sta_x_10_ft = results.stations_obj.sta_x_10_ft
        n_beams = inputs.bridge_info.n_beams
        over_deck_t = results.deck_sections_obj.over_deck_t
        fig = plt.figure(figsize=fig_size)
        ax = fig.add_subplot(111, projection='3d')

        surfaces = c.create_haunch_surfaces()

        c.plot_haunch_volume(inputs, results, ax, surfaces['Variable_Haunch'], 'Variable Haunch')
        c.plot_haunch_volume(inputs, results, ax, surfaces['Minimum_Haunch'], 'Minimum Haunch')
        #self.plot_slab_surface(ax)

        ax.set_zlim([np.min(c.TG_Elev)-2, np.max(c.BS_Elev)+2])
        ax.set_xlabel('Station (X)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Offset (Y)', fontsize=12, fontweight='bold')
        ax.set_zlabel('Elevation (Z)', fontsize=12, fontweight='bold')
        c._add_legend(ax)

        #### SET VIEWING ANGLE ####
        ax.view_init(elev = 15, azim = 20)

        # Grid and styling
        ax.grid(True, alpha = 0.3)

        # Remove white space around the plot
        plt.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=0, hspace=0)

        return fig, ax

    def plot_haunch_volume(c, inputs, results, ax, surface_data, label):
        ns = results.beam_layout_obj.ns
        s = results.stations_obj.s
        n_beams = inputs.bridge_info.n_beams
        over_deck_t = results.deck_sections_obj.over_deck_t
        sta_x_10_ft = results.stations_obj.sta_x_10_ft

        color = surface_data['color']
        for k in range(ns):
          start_index = int(s[:k].sum()) - 2 * k if k > 0 else 0
          end_index = int(s[:k + 1].sum()) - 2 * (k + 1)
          start_index_pgl = int(s[:k].sum()) + 1 if k > 0 else 1
          end_index_pgl = int(s[:k + 1].sum()) - 1
          for j in range(n_beams):
            #### EXTRACT X, Y, Z POINTS ####
            m = 2 * j
            n = 2 * j + 1
            x_girder_lt = surface_data['X'][start_index:end_index, m]
            x_girder_rt = surface_data['X'][start_index:end_index, n]
            y_girder_lt = surface_data['Y'][start_index:end_index, m]
            y_girder_rt = surface_data['Y'][start_index:end_index, n]
            z_top_girder_lt = surface_data['Z_top'][start_index:end_index, m]
            z_top_girder_rt = surface_data['Z_top'][start_index:end_index, n]
            z_bot_girder_lt = surface_data['Z_bot'][start_index:end_index, m]
            z_bot_girder_rt = surface_data['Z_bot'][start_index:end_index, n]
            PGL_elev_bot_deck = results.vc_obj.elev(sta_x_10_ft[start_index_pgl:end_index_pgl]).flatten() - over_deck_t / 12
            PGL = sta_x_10_ft[start_index_pgl:end_index_pgl].flatten()
            for i in range(int(s[k] - 3)):
                #### BOTTOM FACE ####
                vertices = [
                    [x_girder_lt[i], y_girder_lt[i], z_bot_girder_lt[i]],
                    [x_girder_rt[i], y_girder_rt[i], z_bot_girder_rt[i]],
                    [x_girder_rt[i+1], y_girder_rt[i+1], z_bot_girder_rt[i+1]],
                    [x_girder_lt[i+1], y_girder_lt[i+1], z_bot_girder_lt[i+1]]
                ]
                face = Poly3DCollection([vertices], facecolor=color, edgecolor='black', linewidth=0.3)
                ax.add_collection3d(face)
                #### TOP FACE ####
                if ((((y_girder_lt[i] > 0) and (y_girder_rt[i] < 0)) | ((y_girder_lt[i] < 0) and (y_girder_rt[i] > 0))) and label == 'Minimum Haunch'):
                  vertices = [
                    [x_girder_lt[i], y_girder_lt[i], z_top_girder_lt[i]],
                    [PGL[i], 0, PGL_elev_bot_deck[i]],
                    [PGL[i+1], 0, PGL_elev_bot_deck[i+1]],
                    [x_girder_lt[i+1], y_girder_lt[i+1], z_top_girder_lt[i+1]]
                  ]
                  face = Poly3DCollection([vertices], facecolor=color, edgecolor='black', linewidth=0.3)
                  ax.add_collection3d(face)
                  vertices = [
                    [PGL[i], 0, PGL_elev_bot_deck[i]],
                    [x_girder_rt[i], y_girder_rt[i], z_top_girder_rt[i]],
                    [x_girder_rt[i+1], y_girder_rt[i+1], z_top_girder_rt[i+1]],
                    [PGL[i+1], 0, PGL_elev_bot_deck[i+1]]
                  ]
                  face = Poly3DCollection([vertices], facecolor=color, edgecolor='black', linewidth=0.3)
                  ax.add_collection3d(face)
                else:
                  vertices = [
                    [x_girder_lt[i], y_girder_lt[i], z_top_girder_lt[i]],
                    [x_girder_rt[i], y_girder_rt[i], z_top_girder_rt[i]],
                    [x_girder_rt[i+1], y_girder_rt[i+1], z_top_girder_rt[i+1]],
                    [x_girder_lt[i+1], y_girder_lt[i+1], z_top_girder_lt[i+1]]
                  ]
                  face = Poly3DCollection([vertices], facecolor=color, edgecolor='black', linewidth=0.3)
                  ax.add_collection3d(face)
                #### LEFT FACE ####
                vertices = [
                    [x_girder_lt[i], y_girder_lt[i], z_bot_girder_lt[i]],
                    [x_girder_lt[i], y_girder_lt[i], z_top_girder_lt[i]],
                    [x_girder_lt[i+1], y_girder_lt[i+1], z_top_girder_lt[i+1]],
                    [x_girder_lt[i+1], y_girder_lt[i+1], z_bot_girder_lt[i+1]]
                ]
                face = Poly3DCollection([vertices], facecolor=color, edgecolor='black', linewidth=0.3)
                ax.add_collection3d(face)
                #### RIGHT FACE ####
                vertices = [
                    [x_girder_rt[i], y_girder_rt[i], z_bot_girder_rt[i]],
                    [x_girder_rt[i], y_girder_rt[i], z_top_girder_rt[i]],
                    [x_girder_rt[i+1], y_girder_rt[i+1], z_top_girder_rt[i+1]],
                    [x_girder_rt[i+1], y_girder_rt[i+1], z_bot_girder_rt[i+1]]
                ]
                face = Poly3DCollection([vertices], facecolor=color, edgecolor='black', linewidth=0.3)
                ax.add_collection3d(face)

            #### FRONT FACE ####
            vertices_start = [
                [x_girder_lt[0], y_girder_lt[0], z_bot_girder_lt[0]],
                [x_girder_lt[0], y_girder_lt[0], z_top_girder_lt[0]],
                [x_girder_rt[0], y_girder_rt[0], z_top_girder_rt[0]],
                [x_girder_rt[0], y_girder_rt[0], z_bot_girder_rt[0]]
            ]
            face = Poly3DCollection([vertices_start], facecolor=color, edgecolor='black', linewidth=0.5)
            ax.add_collection3d(face)

            #### BACK FACE ####
            vertices_end = [
                [x_girder_lt[-1], y_girder_lt[-1], z_bot_girder_lt[-1]],
                [x_girder_lt[-1], y_girder_lt[-1], z_top_girder_lt[-1]],
                [x_girder_rt[-1], y_girder_rt[-1], z_top_girder_rt[-1]],
                [x_girder_rt[-1], y_girder_rt[-1], z_bot_girder_rt[-1]]
            ]
            face = Poly3DCollection([vertices_end], facecolor=color, edgecolor='black', linewidth=0.5)
            ax.add_collection3d(face)

    def _add_legend(c, ax):
        legend_elements = [
            mpatches.Patch(color='lightblue', alpha=0.7, label='Variable Haunch'),
            mpatches.Patch(color='lightcoral', alpha=0.7, label='Minimum Haunch'),
        ]
        ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(0, 1))

"""#Sheet Creation"""

def profile_curve_pdf(c, inputs, results):
    width, height = letter
    title_block_and_borders(c, inputs)

    #### INPUTS ####
    inp = inputs.vertical_curve
    sta_CL_sub = inputs.substructure.sta_CL_sub
    inpb = inputs.bridge_info
    PGL_loc = inpb.PGL_loc
    deck_width = inpb.deck_width
    rdwy_slope = inpb.rdwy_slope
    bm = results.beam_rail_obj
    rail_b_w = bm.bottom_width
    rail_ed = bm.edge_distance
    cant_len = results.beam_layout_obj.cant_len
    over_deck_t = results.deck_sections_obj.over_deck_t

    #### TITLE VERTICAL PROFILE CURVE ####
    title_y = draw_title(c, "Vertical Curve Data", inch, height - 1.5 * inch - 8)

    def draw_table(data, x, y, col2_offset=110, row_height=15, draw_rect=False):
        c.setFont("Times-Roman", 10)
        for i, (param, value) in enumerate(data):
            y_pos = y - (i * row_height)
            c.drawString(x, y_pos, param)
            c.drawString(x + col2_offset, y_pos, value)
            if draw_rect:
                c.rect(x - 5, y_pos - 5, 220, row_height, stroke=1, fill=0)

    #### VERTICAL CURVE DATA ####
    c.setFont("Times-Roman", 10)
    profile_grade_data = [
        ('VPI Station:', f'{int(inp.sta_VPI//100)}+{inp.sta_VPI%100:05.2f}'), ('VPI Elevation:', f'{inp.elev_VPI:.2f}'),
        ('Grade 1:', f'{inp.grade_1:.4f}%'), ('Grade 2:', f'{inp.grade_2:.4f}%'),
        ('Curve Length:', f'{inp.L_v_curve:.0f}'), 
        ('VPC Station:', f'{int(results.vc_obj.sta_VPC//100)}+{results.vc_obj.sta_VPC%100:05.2f}'),
        ('VPC Elevation:', f'{results.vc_obj.elev_VPC:.2f}'), 
        ('Abutment 1 Station:', f'{int(sta_CL_sub[0]//100)}+{sta_CL_sub[0]%100:05.2f}'),
        ('Abutment 2 Station:', f'{int(sta_CL_sub[-1]//100)}+{sta_CL_sub[-1]%100:05.2f}')
    ]

    #### TABLE SIZE ####
    table_x, table_y = inch, height - inch * 2.1
    draw_table(profile_grade_data, table_x, table_y)

    #### VERTICAL CURVE FIGURE ####
    plot_width, plot_height = inch * 3, inch * 1.5
    plot_x, plot_y = table_x + 200, table_y - 15 * 6
    create_plot(c, inputs, results, plot_x, plot_y, plot_width, plot_height)

    #### ADD TITLE ####
    c.setFont("Times-Roman", 12)
    c.drawCentredString(plot_x + plot_width/2, plot_y, "PROFILE GRADE")

    c.setFont("Times-Italic", 9)
    for i, text in enumerate(["Not to Scale", "(For Bridge Only)"]):
        c.drawCentredString(plot_x + plot_width/2, plot_y - 15 - (i * 13), text)

    #### BRIDGE INFO TITLE ####
    title_y = draw_title(c, "Bridge Superstructure Info", inch, 440)

    #### SPANS, BEAM TYPE AND NO., DECK WIDTH, BRIDGE SKEW
    brg_span_x, brg_span_y = inch, title_y - 30
    c.setFont("Times-Roman", 10)
    for i, span_val in enumerate(results.beam_layout_obj.span):
      c.drawString(brg_span_x, brg_span_y - i * 15, f"Span {i+1}: {span_val:.2f}'")

    basic_data = [
        (f"Beam Shape: {inpb.beam_shape}", brg_span_y - 30),
        (f"No. Beams: {inpb.n_beams:.0f}", brg_span_y - 45),
        (f"Overall Deck Width: {inpb.deck_width:.0f}'", brg_span_y - 60),
        (f"Bridge Skew: {inpb.skew:.2f} deg", brg_span_y - 75)
    ]

    for text, y_pos in basic_data:
        c.drawString(brg_span_x, y_pos, text)

    #### BEAM INFO ####
    beam_shape_data = [
          ('Beam Height (in):', f'{bm.b_height:.2f}'), ('Beam Area (sq in):', f'{bm.area:.1f}'),
          ('Beam Centroid (in):', f'{bm.y_b_nc:.2f}'), ('Beam Moment of Inertia (qu in):', f'{bm.I_g_nc:.0f}'),
          ('Beam Strength (ksi):', f'{inpb.f_c_beam}'), ('Beam Release Strength (ksi):', f'{bm.f_c_i_beam}'),
          ('Beam Modulus of Elasticity (ksi):', f'{bm.E_c:.0f}'), ('Beam Release Modulus of Elasticity (ksi):', f'{bm.E_c_i:.0f}'),
          ('Beam Weight (k/ft):', f'{bm.b_weight:.2f}')
    ]
    draw_table(beam_shape_data, brg_span_x + 120, title_y - 30, col2_offset = 180, draw_rect = True)

    #### BEAM CROSS-SECTION ####
    x_beam, y_beam = create_beam_cx(results)
    path = c.beginPath()
    x_offset, y_offset, scale = 432, 260, 2.5
    path.moveTo(scale * x_beam[0] + x_offset, scale * y_beam[0] + y_offset)
    for i in range(len(x_beam)):
      path.lineTo(scale * x_beam[i] + x_offset, scale * y_beam[i] + y_offset)
    c.drawPath(path, stroke=1, fill=0)

    #### TYPICAL DECK CROSS-SECTION ####
    draw_title(c, "Typical Cross-Section", inch, 220)

    avail_x, avail_y = width - inch - 10, 212 - (inch / 2 + 5)
    max_ht_cx = bm.b_height + over_deck_t + rdwy_slope * deck_width * 12 / 2 + bm.r_height + 1
    cx_scale = min(avail_x / (deck_width * 12), avail_y / max_ht_cx)

    if avail_x / (deck_width * 12) < avail_y / max_ht_cx:
      x_begin, y_begin = inch / 2 + 5, inch / 2 + 5 + (avail_y - max_ht_cx * cx_scale) / 2
    else:
      x_begin, y_begin = (width - deck_width * 12 * cx_scale) / 2, inch / 2 + 5

        #### BEAMS ####
    for i in range(inpb.n_beams):
      path = c.beginPath()
      x_offset = x_begin + cx_scale * (cant_len + i * inpb.beam_spa - bm.tf_width / 2) * 12
      y_offset = y_begin + (x_offset - x_begin) * rdwy_slope if (cant_len + i * inpb.beam_spa - bm.tf_width / 2) <= PGL_loc else y_begin + (PGL_loc - (cant_len + i * inpb.beam_spa + bm.tf_width / 2 - PGL_loc)) * 12 * inpb.rdwy_slope * cx_scale
      path.moveTo(cx_scale * x_beam[0] + x_offset, cx_scale * y_beam[0] + y_offset)
      for i in range(len(x_beam)):
        path.lineTo(cx_scale * x_beam[i] + x_offset, cx_scale * y_beam[i] + y_offset)
      c.drawPath(path, stroke=1, fill=0)

        #### DECK ####
    path = c.beginPath()
    y_begin_deck = y_begin + cx_scale * (bm.b_height + 1)
    path.moveTo(x_begin, y_begin + (bm.b_height + 1) * cx_scale)

            #### BOTTOM ####
    path.lineTo(x_begin + cx_scale * (cant_len - bm.tf_width / 2) * 12, y_begin_deck + cx_scale * ((cant_len - bm.tf_width / 2) * 12 * rdwy_slope) )
    for i in range(inpb.n_beams):
      x_beam_loc = cant_len + i * inpb.beam_spa - bm.tf_width / 2
      if x_beam_loc < PGL_loc:
        x_under_deck = min(PGL_loc - x_beam_loc - bm.tf_width, inpb.beam_spa - bm.tf_width)
        path.lineTo(x_begin + cx_scale * (x_beam_loc * 12), y_begin_deck + cx_scale * (x_beam_loc * 12 * rdwy_slope))
        path.lineTo(x_begin + cx_scale * (x_beam_loc * 12), y_begin_deck + cx_scale * (x_beam_loc * 12 * rdwy_slope - 1))
        path.lineTo(x_begin + cx_scale * (x_beam_loc + bm.tf_width) * 12, y_begin_deck + cx_scale * (x_beam_loc * 12 * rdwy_slope - 1))

        if (x_beam_loc + bm.tf_width) > PGL_loc:
          path.lineTo(x_begin + cx_scale * (x_beam_loc + bm.tf_width) * 12, y_begin_deck + cx_scale * ((PGL_loc - (bm.tf_width / 2)) * 12 * rdwy_slope))
        else:
          path.lineTo(x_begin + cx_scale * (x_beam_loc + bm.tf_width) * 12, y_begin_deck + cx_scale * ((x_beam_loc + bm.tf_width) * 12 * rdwy_slope))
          path.lineTo(x_begin + cx_scale * (x_beam_loc + bm.tf_width + x_under_deck) * 12, y_begin_deck + cx_scale * ((x_beam_loc + bm.tf_width + x_under_deck) * 12 * rdwy_slope))
      else:
        x_under_deck = min(x_beam_loc - PGL_loc, inpb.beam_spa - bm.tf_width)
        path.lineTo(x_begin + cx_scale * (x_beam_loc - x_under_deck) * 12, y_begin_deck + cx_scale * ((PGL_loc - (x_beam_loc - PGL_loc - x_under_deck)) * 12 * rdwy_slope))
        path.lineTo(x_begin + cx_scale * (x_beam_loc) * 12, y_begin_deck + cx_scale * ((PGL_loc - (x_beam_loc - PGL_loc)) * 12 * rdwy_slope))
        path.lineTo(x_begin + cx_scale * (x_beam_loc) * 12, y_begin_deck + cx_scale * ((PGL_loc - (x_beam_loc - PGL_loc) - bm.tf_width) * 12 * rdwy_slope - 1))
        path.lineTo(x_begin + cx_scale * (x_beam_loc + bm.tf_width) * 12, y_begin_deck + cx_scale * ((PGL_loc - (x_beam_loc - PGL_loc) - bm.tf_width) * 12 * rdwy_slope - 1))
        path.lineTo(x_begin + cx_scale * (x_beam_loc + bm.tf_width) * 12, y_begin_deck + cx_scale * ((PGL_loc - (x_beam_loc - PGL_loc + bm.tf_width)) * 12 * rdwy_slope))

    deck_points = [
        (x_begin + cx_scale * deck_width * 12, y_begin_deck + cx_scale * ((PGL_loc - (deck_width - PGL_loc)) * 12 * rdwy_slope)),
        (x_begin + deck_width * 12 * cx_scale, y_begin + cx_scale * (bm.b_height + 1 + over_deck_t + (rail_b_w + rail_ed + (PGL_loc - (deck_width - PGL_loc)) * 12) * rdwy_slope)),
        (x_begin + (deck_width * 12 - (rail_b_w + rail_ed)) * cx_scale, y_begin + cx_scale * (bm.b_height + 1 + over_deck_t + (rail_b_w + rail_ed + (PGL_loc - (deck_width - PGL_loc)) * 12) * rdwy_slope)),
        (x_begin + PGL_loc * 12 * cx_scale, y_begin + ((bm.b_height + 1) + PGL_loc * 12 * rdwy_slope + over_deck_t) * cx_scale),
        (x_begin + (rail_b_w + rail_ed) * cx_scale, y_begin + (bm.b_height + 1 + over_deck_t + (rail_b_w + rail_ed) * rdwy_slope) * cx_scale),
        (x_begin, y_begin + (bm.b_height + 1 + over_deck_t + (rail_b_w + rail_ed) * rdwy_slope) * cx_scale),
        (x_begin, y_begin + (bm.b_height + 1) * cx_scale)
    ]
    for point in deck_points:
        path.lineTo(*point)
    c.drawPath(path, stroke=1, fill=0)

        #### RAILING ####
    x_rail, y_rail = create_rail_cx(inputs, results)
    rail_positions = [
        (rail_ed, rail_b_w + rail_ed),
        (deck_width * 12 - (rail_b_w + rail_ed), -(rail_b_w + rail_ed))
    ]

    for rail_x_base, rail_offset in rail_positions:
        path = c.beginPath()
        base_y = bm.b_height + 1 + over_deck_t + ((rail_b_w + rail_ed) + (PGL_loc - (deck_width - PGL_loc)) * 12) * rdwy_slope
        path.moveTo(x_begin + cx_scale * rail_x_base, y_begin + cx_scale * base_y)
        for i in range(len(x_rail)):
            x_coord = x_begin + cx_scale * (deck_width * 12 - x_rail[i] - rail_ed if rail_offset < 0 else x_rail[i] + rail_ed)
            y_coord = y_begin + cx_scale * (y_rail[i] + base_y)
            path.lineTo(x_coord, y_coord)
        c.drawPath(path, stroke=1, fill=0)

def deck_section(c, inputs, results):
    width, height = letter
    title_block_and_borders(c, inputs)

    #### INPUTS ####
    deck_width = inputs.bridge_info.deck_width
    beam_spa = inputs.bridge_info.beam_spa
    PGL_loc = inputs.bridge_info.PGL_loc
    rdwy_slope = inputs.bridge_info.rdwy_slope
    n_beams = inputs.bridge_info.n_beams
    beam_ht = results.beam_rail_obj.b_height
    over_deck_t = results.deck_sections_obj.over_deck_t
    bm = results.beam_rail_obj
    rail_b_w = bm.bottom_width
    rail_ed = bm.edge_distance
    cant_len = results.beam_layout_obj.cant_len
    cl_info = results.deck_sections_obj

    #### DRAW STAGING CROSS-SECTION ############################################

    # Title for Cross-Section View of Staging
    line_y = draw_title(c, "Staging Plan", inch, height - 1.5 * inch - 8)

    avail_x = width - inch - 10
    max_ht_cx = beam_ht + 1 + rdwy_slope * deck_width * 12 / 2 + over_deck_t + bm.r_height
    cx_scale = avail_x / (deck_width * 12)
    x_begin = inch / 2 + 5
    y_begin = line_y - 5 - cx_scale * max_ht_cx - 50

    # Draw Beams
    x_beam, y_beam = create_beam_cx(results)
    beam_strt = results.beam_layout_obj.beam_pos - bm.tf_width / 2
    y_offset = np.zeros(inputs.bridge_info.n_beams)
    for i in range(inputs.bridge_info.n_beams):
      path = c.beginPath()
      x_offset = x_begin + cx_scale * (beam_strt[i]) * 12
      if (results.beam_layout_obj.beam_pos[i]) <= PGL_loc:
        y_offset[i] = y_begin + (x_offset - x_begin) * rdwy_slope
      else:
        y_offset[i] = y_begin + cx_scale * (PGL_loc - (cant_len + i * beam_spa + bm.tf_width / 2 - PGL_loc )) * 12 * rdwy_slope
      path.moveTo(cx_scale * x_beam[0] + x_offset, cx_scale * y_beam[0] + y_offset[i])
      c.setFont("Times-Roman", 8)
      c.drawCentredString(x_offset + cx_scale * bm.tf_width * 12 / 2, y_offset[i] - 12, f"Beam {i + 1}")
      for j in range(len(x_beam)):
        path.lineTo(cx_scale * x_beam[j] + x_offset, cx_scale * y_beam[j] + y_offset[i])
      c.drawPath(path, stroke=1, fill=0)
    # Draw Roadway
    path = c.beginPath()
    y_begin_deck = y_begin + cx_scale * (beam_ht + 1)
    path.moveTo(x_begin, y_begin_deck)
    # Bottom of Deck
    path.lineTo(x_begin + cx_scale * (cant_len - bm.tf_width / 2) * 12, y_begin_deck + cx_scale * ((cant_len - bm.tf_width / 2) * 12 * rdwy_slope) )
    for i in range(inputs.bridge_info.n_beams):
      if beam_strt[i] < PGL_loc:
        x_under_deck = min(PGL_loc - beam_strt[i] - bm.tf_width, beam_spa - bm.tf_width)
        path.lineTo(x_begin + cx_scale * (beam_strt[i] * 12), y_begin_deck + cx_scale * (beam_strt[i] * 12 * rdwy_slope))
        path.lineTo(x_begin + cx_scale * (beam_strt[i] * 12), y_begin_deck + cx_scale * (beam_strt[i] * 12 * rdwy_slope - 1))
        path.lineTo(x_begin + cx_scale * (beam_strt[i] + bm.tf_width) * 12, y_begin_deck + cx_scale * (beam_strt[i] * 12 * rdwy_slope - 1))
        if (beam_strt[i] + bm.tf_width) > PGL_loc:
          path.lineTo(x_begin + cx_scale * (beam_strt[i] + bm.tf_width) * 12, y_begin_deck + cx_scale * ((PGL_loc - (bm.tf_width / 2)) * 12 * rdwy_slope))
        else:
          path.lineTo(x_begin + cx_scale * (beam_strt[i] + bm.tf_width) * 12, y_begin_deck + cx_scale * ((beam_strt[i] + bm.tf_width) * 12 * rdwy_slope))
          path.lineTo(x_begin + cx_scale * (beam_strt[i] + bm.tf_width + x_under_deck) * 12, y_begin_deck + cx_scale * ((beam_strt[i] + bm.tf_width + x_under_deck) * 12 * rdwy_slope))
      else:
        x_under_deck = min(beam_strt[i] - PGL_loc, beam_spa - bm.tf_width)
        path.lineTo(x_begin + cx_scale * (beam_strt[i] - x_under_deck) * 12, y_begin_deck + cx_scale * ((PGL_loc - (beam_strt[i] - PGL_loc - x_under_deck)) * 12 * rdwy_slope))
        path.lineTo(x_begin + cx_scale * (beam_strt[i]) * 12, y_begin_deck + cx_scale * ((PGL_loc - (beam_strt[i] - PGL_loc)) * 12 * rdwy_slope))
        path.lineTo(x_begin + cx_scale * (beam_strt[i]) * 12, y_begin_deck + cx_scale * ((PGL_loc - (beam_strt[i] - PGL_loc) - bm.tf_width) * 12 * rdwy_slope - 1))
        path.lineTo(x_begin + cx_scale * (beam_strt[i] + bm.tf_width) * 12, y_begin_deck + cx_scale * ((PGL_loc - (beam_strt[i] - PGL_loc) - bm.tf_width) * 12 * rdwy_slope - 1))
        path.lineTo(x_begin + cx_scale * (beam_strt[i] + bm.tf_width) * 12, y_begin_deck + cx_scale * ((PGL_loc - (beam_strt[i] - PGL_loc + bm.tf_width)) * 12 * rdwy_slope))
    path.lineTo(x_begin + cx_scale * deck_width * 12, y_begin_deck + cx_scale * ((PGL_loc - (deck_width - PGL_loc)) * 12 * rdwy_slope) )
    # Right Side of Deck
    path.lineTo(x_begin + cx_scale * deck_width * 12, \
                y_begin_deck + cx_scale * (over_deck_t + (rail_b_w + rail_ed + (PGL_loc - (deck_width - PGL_loc)) * 12) * rdwy_slope) )
    # Flat Deck Under Railing
    path.lineTo(x_begin + cx_scale * (deck_width * 12 - (rail_b_w + rail_ed)), \
                y_begin_deck + cx_scale * (over_deck_t + (rail_b_w + rail_ed + (PGL_loc - (deck_width - PGL_loc)) * 12) * rdwy_slope) )
    # Top of Deck
    path.lineTo(x_begin + cx_scale * PGL_loc * 12, y_begin_deck + cx_scale * (over_deck_t + PGL_loc * 12 * rdwy_slope) )
    path.lineTo(x_begin + cx_scale * (rail_b_w + rail_ed), y_begin_deck + cx_scale * (over_deck_t + (rail_b_w + rail_ed) * rdwy_slope) )
    # Flat Deck Under Railing
    path.lineTo(x_begin, y_begin_deck + cx_scale * (over_deck_t + (rail_b_w + rail_ed) * rdwy_slope) )
    # Left Side of Deck
    path.lineTo(x_begin, y_begin_deck)
    c.drawPath(path, stroke=1, fill=0)

    # Draw Railing
    path = c.beginPath()
    path.moveTo(x_begin + cx_scale * rail_ed, y_begin_deck + cx_scale * over_deck_t )
    x_rail, y_rail = create_rail_cx(inputs, results)
    for i in range(len(x_rail)):
      path.lineTo(x_begin + cx_scale * (x_rail[i] + rail_ed), y_begin_deck + cx_scale * (y_rail[i] + over_deck_t + (rail_b_w + rail_ed) * rdwy_slope) )
    c.drawPath(path, stroke=1, fill=0)
    path = c.beginPath()
    path.moveTo(x_begin + cx_scale * (deck_width * 12 - (rail_b_w + rail_ed)),\
                y_begin_deck + cx_scale * (over_deck_t + ((rail_b_w + rail_ed) + (PGL_loc - (deck_width - PGL_loc)) * 12) * rdwy_slope) )
    for i in range(len(x_rail)):
      path.lineTo(x_begin + cx_scale * (deck_width * 12 - x_rail[i] - rail_ed),\
                y_begin_deck + cx_scale * (y_rail[i] + over_deck_t + ((rail_b_w + rail_ed) + (PGL_loc - (deck_width - PGL_loc)) * 12) * rdwy_slope) )
    c.drawPath(path, stroke=1, fill=0)

    # Staging Lines
    if inputs.bridge_info.staged == "yes"
        x_lt_stage_line = x_begin + cx_scale * inputs.bridge_info.stg_line_lt * 12
        y_lt_stage_line_top = y_begin_deck + cx_scale * (inputs.bridge_info.stg_line_lt * 12 * rdwy_slope + over_deck_t)
        x_rt_stage_line = x_begin + cx_scale * inputs.bridge_info.stg_line_rt * 12
        y_rt_stage_line_top = y_begin_deck + cx_scale * (inputs.bridge_info.stg_line_rt * 12 * rdwy_slope + over_deck_t)

        y_lt_stage_line_bot = y_lt_stage_line_top - over_deck_t # Default value
        y_rt_stage_line_bot = y_rt_stage_line_top - over_deck_t # Default value
        for i in range(inputs.bridge_info.n_beams):
            if (inputs.bridge_info.stg_line_rt >= beam_strt[i]) and (inputs.bridge_info.stg_line_rt <= (beam_strt[i] + bm.tf_width)):
                y_lt_stage_line_bot = y_offset[i] + cx_scale * beam_ht
                y_rt_stage_line_bot = y_offset[i] + cx_scale * beam_ht
                break # Exit the loop once a match is found

        c.line(x_lt_stage_line, y_lt_stage_line_top, x_lt_stage_line, y_lt_stage_line_bot)
        c.line(x_rt_stage_line, y_rt_stage_line_top, x_rt_stage_line, y_rt_stage_line_bot)
    
        # Stage Dimension Lines
        y_lt_dim_line = y_lt_stage_line_top + 5
        y_rt_dim_line = y_rt_stage_line_top + 5
        y_dim_line_top = max(y_lt_dim_line, y_rt_dim_line) + 60
        c.line(x_lt_stage_line, y_lt_dim_line, x_lt_stage_line, y_dim_line_top)
        c.line(x_rt_stage_line, y_rt_dim_line, x_rt_stage_line, y_dim_line_top)
        c.line(x_lt_stage_line, y_dim_line_top - 5, x_rt_stage_line, y_dim_line_top - 5)
        y_dim_railing_lt = y_begin_deck + cx_scale * (max(y_rail) + over_deck_t + (rail_b_w + rail_ed) * rdwy_slope) + 5
        y_dim_railing_rt = y_begin_deck + cx_scale * (max(y_rail) + over_deck_t + ((rail_b_w + rail_ed) + (PGL_loc - (deck_width - PGL_loc)) * 12 )* rdwy_slope) + 5
        x_dim_railing_lt = x_begin + cx_scale * (rail_ed)
        x_dim_railing_rt = x_begin + cx_scale * (deck_width * 12 - rail_ed)
        c.line(x_dim_railing_lt, y_dim_railing_lt, x_dim_railing_lt, y_dim_line_top)
        c.line(x_dim_railing_lt, y_dim_line_top - 5, x_lt_stage_line, y_dim_line_top - 5)
        c.line(x_dim_railing_rt, y_dim_railing_rt, x_dim_railing_rt, y_dim_line_top)
        c.line(x_dim_railing_rt, y_dim_line_top - 5, x_rt_stage_line, y_dim_line_top - 5)
        
        # Label Stage Lines
        c.setFont("Times-Roman", 8)
        c.drawCentredString((x_lt_stage_line - x_dim_railing_lt) / 2 + x_begin, y_dim_line_top - 1, "Stage 1")
        c.drawCentredString((x_dim_railing_rt - x_rt_stage_line) / 2 + x_rt_stage_line, y_dim_line_top - 1, "Stage 2")
        c.drawCentredString((x_rt_stage_line - x_lt_stage_line) / 2 + x_lt_stage_line, y_dim_line_top - 1, "Closure")
        c.drawCentredString((x_rt_stage_line - x_lt_stage_line) / 2 + x_lt_stage_line, y_dim_line_top - 12, "Pour")

        # Tributary widths
        for i in range(inputs.bridge_info.n_beams - 1):
            x_loc = x_begin + cx_scale * (results.beam_layout_obj.beam_pos[i] + beam_spa / 2) * 12
            if results.beam_layout_obj.beam_pos[i] <= (PGL_loc - beam_spa):
                y_loc_top = y_begin_deck + cx_scale * (over_deck_t) + (x_loc - x_begin) * rdwy_slope
            else:
                y_loc_top = y_begin_deck + cx_scale * (over_deck_t) + (x_loc - x_begin) * rdwy_slope - 2 * (x_loc - cx_scale * PGL_loc * 12 - x_begin) * rdwy_slope
            y_loc_bot = y_loc_top - over_deck_t
            c.setDash([3, 3])
            c.setStrokeColor(colors.black)
            c.line(x_loc, y_loc_top, x_loc, y_loc_bot)
            if (x_loc >= x_lt_stage_line) and (x_loc <= x_rt_stage_line):
                clos_lt_fl = cl_info.closure_over_beam_flange[np.nonzero(cl_info.closure_over_beam_flange)[0]] * 12 if np.nonzero(cl_info.closure_over_beam_flange)[0].size > 1 else 0
                x_loc_clos = x_lt_stage_line + cx_scale * (clos_lt_fl + (cl_info.closure_width.sum() - cl_info.closure_over_beam_flange.sum()) * 12 / 2)
                y_loc_clos_top = y_begin_deck + cx_scale * (over_deck_t) + (x_loc_clos - x_begin) * rdwy_slope
                y_loc_clos_bot = y_loc_clos_top - over_deck_t
                c.setStrokeColor(colors.red)
                c.line(x_loc_clos, y_loc_clos_top, x_loc_clos, y_loc_clos_bot)
    
            # Create Tributary Widths Table
            trib_width_x, trib_width_y = inch + c.stringWidth("Beam 1", "Times-Roman", 12) + 10, y_begin - 45
            line_y = draw_title(c, "Tributary Widths", trib_width_x, trib_width_y)

            x_stage_label_1 = inch + c.stringWidth("Beam 1", "Times-Roman", 12) + 10
            x_stage_label_2 = x_stage_label_1 + 60
            x_stage_label_3 = x_stage_label_2 + 60
            y_stage_labels = line_y - 15
            c.setFont("Times-Roman", 12)
            c.drawString(x_stage_label_1, y_stage_labels, f"Stage 1:")
            c.drawString(x_stage_label_2, y_stage_labels, f"Stage 2:")
            c.drawString(x_stage_label_3, y_stage_labels, f"Stage 3:")
            for i in range(inputs.bridge_info.n_beams):
                y_stage_labels -= 15
                x_beam_labels = inch
                c.drawString(x_beam_labels, y_stage_labels, f"Beam {i + 1}:")
                x_stage_labels = c.stringWidth(f"Beam {i + 1}:", "Times-Roman", 12) + 10
                c.drawCentredString(x_stage_label_1 + 20, y_stage_labels, f"{cl_info.deck_df['Stage 1 Width'][i]:.2f}")
                c.drawCentredString(x_stage_label_2 + 20, y_stage_labels, f"{cl_info.deck_df['Stage 1 Width'][i] + cl_info.deck_df['Stage 2 Width'][i]:.2f}")
                c.drawCentredString(x_stage_label_3 + 20, y_stage_labels, f"{cl_info.deck_df['Stage 3 Width'][i]:.2f}")

            c.drawString(400, y_stage_labels, "NC: Noncomposite")
            c.drawString(400, y_stage_labels - 15, "PC: Partially Composite")
            c.drawString(400, y_stage_labels - 30, "C: Composite")

            # Create Table of Dead Loads
            title_d_load_x, title_d_load_y = inch + c.stringWidth("Beam 1:", "Times-Roman", 12) + 10, y_stage_labels - 30
            line_y = draw_title(c, "Dead Loads (k/ft)", title_d_load_x, title_d_load_y)

            c.setFont("Times-Roman", 12)
            d_load_labels = ["Beam #:", "Self Weight:", "NC Stages 1 and 2:", "C Stages 1 and 2:", "PC Stage 3:", "C Stage 3:"]
            x_d_load_labels, w_d_load_labels = np.zeros(len(d_load_labels)), np.zeros(len(d_load_labels))
            y_d_load_labels = line_y - 15
            for i in range(len(d_load_labels)):
                w_d_load_labels[i] = c.stringWidth(d_load_labels[i], "Times-Roman', 12)
                if i < 1:
                    x_d_load_labels[i] = inch + w_d_load_labels[i] + 10
                else:
                    x_d_load_labels[i] = x_d_load_labels[i - 1] + w_d_load_labels[i] + 10
                    c.drawString(x_d_load_labels[i - 1], y_d_load_labels, d_load_labels[i])
                    c.rect(x_d_load_labels[i - 1] - 5, y_d_load_labels - 15 * n_beams - 5, w_d_load_labels[i] + 10, 15 * n_beams)
            for i in range(n_beams):
                y_d_load_labels -= 15
                c.drawString(inch, y_d_load_labels, f"Beam {i + 1}:")
                c.drawCentredString(x_d_load_label[0] + w_d_load_labels[1] / 2, y_d_load_labels, f"{(bm.b_weight):.3f}")
                c.drawCentredString(x_d_load_label[1] + w_d_load_labels[2] / 2, y_d_load_labels, f"{(cl_info.deck_df['Stage 1 NC Wt'][i] + cl_info.deck_df['Stage 2 NC Wt'][i]):.3f}")
                c.drawCentredString(x_d_load_label[2] + w_d_load_labels[3] / 2, y_d_load_labels, f"{(cl_info.deck_df['Stage 1 C Wt'][i] + cl_info.deck_df['Stage 2 C Wt'][i]):.3f}")
                c.drawCentredString(x_d_load_label[3] + w_d_load_labels[4] / 2, y_d_load_labels, f"{(cl_info.deck_df['Stage 3 PC Wt'][i]):.3f}")
                c.drawCentredString(x_d_load_label[4] + w_d_load_labels[5] / 2, y_d_load_labels, f"{(cl_info.deck_df['Stage 3 C Wt'][i]):.3f}")

def create_beam_titles(inputs):
    beam_title = []
    for beam in range(inputs.bridge_info.n_beams):
        beam_title.append(f'Beam {beam + 1} LF')
        beam_title.append(f'Beam {beam + 1} RF')
    return beam_title

def create_station_labels(results):
    ns = results.beam_layout_obj.ns
    s = results.stations_obj.s
    return [
        'Abutment 1 CL Bearing:' if (span_idx == 0 and span_point == 0) else
        f'Pier {span_idx} Downstation CL Bearing:' if (span_idx > 0 and span_point == 0) else
        'Abutment 2 CL Bearing:' if (span_idx == ns - 1 and span_point == s[span_idx] - 1) else
        f'Pier {span_idx + 1} Upstation CL Bearing:' if (span_idx < ns - 1 and span_point == s[span_idx] - 1) else
        f'Span {span_idx+1} Shot Point {span_point}:'
        for span_idx in range(ns) for span_point in range(int(s[span_idx]))
    ]

def draw_page_content(c, results, last_y, beam_start_col, beam_end_col, row_start, row_end,
                     beam_titles, station_labels):
    width, height = letter

    #### SECTION TITLES ####
    beam_range = f"Beam {(beam_start_col // 2) + 1} thru {beam_end_col // 2}"
    title_text = f"{beam_range} Stations and Elevations"
    title_x, title_y = width / 2, last_y - 30
    c.setFont("Times-Bold", 20)
    c.drawCentredString(title_x, title_y, title_text)

    #### DRAW TITLES ####
    title_width = c.stringWidth(title_text, "Times-Bold", 20)
    line_start_x, line_end_x = title_x - title_width / 2, title_x + title_width / 2
    line_y = title_y - 3
    c.setStrokeColor(colors.black)
    c.setLineWidth(0.8)
    c.line(line_start_x, line_y, line_end_x, line_y)

    #### DRAW COLUMN HEADERS ####
    x_header = 2.4 * inch + 5
    y_header = line_y - 15
    for col in range(beam_start_col, beam_end_col):
        x_header += c.stringWidth(beam_titles[col], "Times-Roman", 10) + 10
        c.setFont("Times-Roman", 10)
        c.drawString(x_header, y_header, beam_titles[col])
        c.line(x_header, y_header - 1,
               x_header + c.stringWidth(beam_titles[col], "Times-Roman", 10), y_header - 1)

    x_label = 0.65 * inch
    y_row_bot = y_header - 3

    for row_idx in range(row_start, min(row_end, len(station_labels))):
        y_row_bot -= 25

        #### WRITE STAION LABELS AND BOXES ####
        c.setFont("Times-Roman", 10)
        c.drawString(2.4 * inch + 8, y_row_bot + 15, "Station:")
        c.drawString(2.4 * inch + 8, y_row_bot + 3, "Elevation:")
        c.drawString(x_label, y_row_bot + 10, station_labels[row_idx])
        c.rect(45, y_row_bot, width - 90, 25, stroke=1, fill=0)

        #### WRITE STATION AND ELEVATION DATA ####
        x_data = 2.4 * inch + 5
        for col in range(beam_start_col, beam_end_col):
            x_data += c.stringWidth(beam_titles[col], "Times-Roman", 10) + 10
            c.drawString(x_data, y_row_bot + 15, f"{results.stations_obj.sta_G[row_idx, col]:.2f}")
            c.drawString(x_data, y_row_bot + 3, f"{results.final_haunch_obj.TS_Elev[row_idx, col]:.2f}")

def generate_multi_page_pdf(c, inputs, results):
    #### INITIALIZE PDF ####
    width, height = letter

    #### FIGURE ####
    bot_fig_y = bridge_figure_sta_elev_points(canvas.Canvas("x.pdf"), inputs, results)

    #### LAYOUT LIMITS ####
    max_beam_cols = (int((width - 0.5 * inch - 2.4 * inch) // 58) // 2) * 2
    max_rows = int((bot_fig_y - 1.5 * inch) // 25)

    #### TOTAL ROWS AND COLUMNS ####
    beam_titles = create_beam_titles(inputs)
    station_labels = create_station_labels(results)
    total_rows, total_beam_cols = len(station_labels), len(beam_titles)

    page_num = 1

    for beam_start in range(0, total_beam_cols, max_beam_cols):
        beam_end = min(beam_start + max_beam_cols, total_beam_cols)
        for row_start in range(0, total_rows, max_rows):
            row_end = min(row_start + max_rows, total_rows)
            if page_num > 1:
                c.showPage()

            #### TITLE BLOCK, BORDERS, FIGURE ####
            title_block_and_borders(c, inputs)
            bot_fig_y = bridge_figure_sta_elev_points(c, inputs, results)

            #### STATIONS AND ELEVATIONS ####
            draw_page_content(c, results, bot_fig_y, beam_start, beam_end, row_start, row_end,
                            beam_titles, station_labels)
            page_num += 1

def create_beam_haunch_pdf(c, inputs, results):
    width, height = letter
    title_block_and_borders(c, inputs)

    #### INPUTS ####
    sta_G = results.stations_obj.sta_G
    TG_Elev = results.seat_obj.TG_Elev
    Min_Haunch_Elev = results.seat_obj.Min_Haunch_Elev
    BS_Elev = results.seat_obj.BS_Elev
    TS_Elev = results.final_haunch_obj.TS_Elev
    offsets = results.beam_layout_obj.offsets
    ns = results.beam_layout_obj.ns

    #### TITLE VERTICAL PROFILE CURVE ####
    title_y = draw_title(c, "3D Minimum and Variable Beam Haunches", inch, height - 1.5 * inch - 8)

    visualizer = BridgeDesign3DVisualizer(inputs, results)
    fig, ax = visualizer.plot_3d_bridge(inputs, results)
    imgdata = BytesIO()
    fig.savefig(imgdata, format='png', bbox_inches='tight', pad_inches=0, dpi=150)
    imgdata.seek(0)  # rewind the data
    beam_iso = ImageReader(imgdata)
    img_ht, img_wdt = height - 4.5 * inch, width - 1.2 * inch
    c.drawImage(beam_iso, 0.6 * inch, title_y - 5 - img_ht, img_wdt, img_ht)
    plt.close(fig)
    for i in range(ns):
      c.showPage()
      create_beam_elevation_view(c, inputs, results, i, 0)

def create_beam_elevation_view(c, inputs, results, span, beam):
    width, height = letter
    title_block_and_borders(c, inputs)

    #### INPUTS ####
    offsets = results.beam_layout_obj.offsets
    s = results.stations_obj.s
    sta_G = results.stations_obj.sta_G
    TS_Elev = results.final_haunch_obj.TS_Elev
    TG_Elev = results.seat_obj.TG_Elev
    Min_Haunch_Elev = results.seat_obj.Min_Haunch_Elev
    BS_Elev = results.seat_obj.BS_Elev

    #### TITLE BEAM HAUNCH ELEVATION ####
    line_y = draw_title(c, f"Span {span+1} Beam 1 Haunch Elevation View", inch, height - 1.5 * inch - 8)

    #### CREATE 2D PLOT OF BEAM HAUNCHES #######################################

    start_index = int(s[:span].sum()) + 1 if span > 0 else 1
    end_index = int(s[:span + 1].sum()) - 1
    GL = 2 * beam
    sta_G_temp = sta_G[start_index:end_index, GL]
    TS_Elev_temp = TS_Elev[start_index:end_index, GL]
    BS_Elev_temp = BS_Elev[start_index:end_index, GL]
    Min_Haunch_Elev_temp = Min_Haunch_Elev[start_index:end_index, GL]
    TG_Elev_temp = TG_Elev[start_index:end_index, GL]

    fig, ax = plt.subplots(figsize = (11, 8.5))

    #### FILL AREAS ####
    deck_fill = ax.fill_between(sta_G_temp, TS_Elev_temp, BS_Elev_temp, color = 'lightgrey', alpha = 0.7)
    min_hnch_fill = ax.fill_between(sta_G_temp, BS_Elev_temp, Min_Haunch_Elev_temp, color = 'lightcoral', alpha = 0.7)
    var_hnch_fill = ax.fill_between(sta_G_temp, Min_Haunch_Elev_temp, TG_Elev_temp, color = 'lightblue', alpha = 0.7)

    #### PLOT LINES ####
    line_1 = (start_index, end_index)

    ax.plot(sta_G[line_1, GL], TG_Elev[line_1, GL], 'k--', linewidth = 1, label = 'Top of Girder')
    ax.plot(sta_G[line_1, GL], results.seat_obj.profile_tan_line[line_1, GL], 'k--', linewidth = 1, label = 'Profile Tangent Line')

    #### COMPONENT LABELS ####
    mid_point = round((end_index - start_index) / 2) + start_index
    qur_point = round((end_index - start_index) / 4) + start_index
    r1, r2, r3, r4 = mid_point - 1, mid_point - 2, qur_point - 1, qur_point - 2

    ax.text(np.mean(sta_G[r2:r1, GL]), np.mean(TS_Elev[r2:r1, GL] + BS_Elev[r2:r1, GL]) / 2,
            'Deck', ha = 'center', va = 'center', fontweight = 'bold', fontsize = 8,
            bbox = dict(boxstyle = "round,pad=0.3", facecolor = "white", alpha = 0.8))

    ax.text(np.mean(sta_G[r4:r3, GL]), np.mean(BS_Elev[r4:r3, GL] + Min_Haunch_Elev[r4:r3, GL]) / 2,
            'Minimum\nHaunch', ha = 'center', va = 'center', fontweight = 'bold', fontsize = 6,
            bbox = dict(boxstyle = "round,pad=0.3", facecolor = "white", alpha = 0.8))

    ax.text(np.mean(sta_G[start_index, GL]), np.mean(Min_Haunch_Elev[start_index, GL] + TG_Elev[start_index, GL]) / 2,
            'Variable\nHaunch', ha = 'center', va = 'center', fontweight = 'bold', fontsize = 6,
            bbox = dict(boxstyle = "round,pad=0.3", facecolor = "white", alpha = 0.8))

    #### DELTA PROFILE CURVE ####
    delta_profile = np.max(results.final_haunch_obj.profile_deflections, axis = 0)[GL]
    x_pos = sta_G[end_index, GL]
    top_ = results.seat_obj.profile_tan_line[end_index, GL]
    bot_ = TS_Elev[end_index, GL]

    ax.plot([x_pos - 2, x_pos - 2], [top_, bot_], 'b-', linewidth = 1)
    ax.plot([x_pos - 3, x_pos], [top_, top_], 'b-', linewidth = 1)
    ax.plot([x_pos - 3, x_pos], [bot_, bot_], 'b-', linewidth = 1)

    ax.text(x_pos - 4, (top_ + bot_) / 2 + 0.3, f'δ max profile \ncurve = {delta_profile:.3f}',
            ha = 'center', va = 'center', fontsize = 6, color = 'blue',
            bbox = dict(boxstyle = "round,pad=0.3", facecolor = "lightblue", alpha = 0.8))

    #### DELTA CAMBER ####
    top_ = TG_Elev[mid_point, GL]
    bot_ = (TG_Elev[end_index, GL] - TG_Elev[start_index, GL]) / 2 + TG_Elev[start_index, GL]
    delta_camber = np.max(results.final_haunch_obj.defl_final, axis = 0)[GL] / 12

    x_camber = sta_G[mid_point, GL]

    ax.plot([x_camber, x_camber], [top_, bot_], 'g-', linewidth = 1)
    ax.plot([x_camber - 1, x_camber + 1], [top_, top_], 'g-', linewidth = 1)
    ax.plot([x_camber - 1, x_camber + 1], [bot_, bot_], 'g-', linewidth = 1)

    ax.text(x_camber + 5, (top_ + bot_) / 2, f'δ max camber\n = {delta_camber:.3f}',
            ha = 'center', va = 'center', fontsize = 6, color = 'green',
            bbox = dict(boxstyle = "round,pad=0.3", facecolor = "lightgreen", alpha = 0.8))

    #### SET LIMITS AND LABELS ####
    y_min = np.min(TG_Elev) - 0.5
    y_max = np.max(TS_Elev) + 1
    ax.set_ylim(y_min, y_max)
    ax.set_xlabel('Station (ft)', fontsize = 12, fontweight = 'bold')
    ax.set_ylabel('Elevation (ft)', fontsize = 12, fontweight = 'bold')

    ax.grid(True, alpha = 0.3)

    #### STYLING ####
    ax.spines['top'].set_linewidth(2)
    ax.spines['bottom'].set_linewidth(2)
    ax.spines['left'].set_linewidth(2)
    ax.spines['right'].set_linewidth(2)
    plt.subplots_adjust(left=0.1, bottom=0.1, right=0.95, top=0.95)

    imgdata = BytesIO()
    fig.savefig(imgdata, format='png', bbox_inches='tight', pad_inches=0.05, dpi=150)
    imgdata.seek(0)  # rewind the data
    beam_elev = ImageReader(imgdata)
    img_ht, img_wdt = height - 6.5 * inch, width - 1.2 * inch
    c.drawImage(beam_elev, 0.6 * inch, line_y - 15 - img_ht, img_wdt, img_ht)
    plt.close(fig)

    #### TITLE FOR BEAM HAUNCHES IN SPAN ####
    line_y = draw_title(c, f"Span {span+1} Beams", inch, line_y - img_ht - 40)

    #### MAX CAMBER, MAX PROFILE GRADE DROP/INCREASE, MAX HAUNCH & LOCATION TITLES ####
    camber_title_x, camber_title_y = 1.5 * inch, line_y - 15
    c.setFont("Times-Bold", 12)
    c.drawString(camber_title_x, camber_title_y, f"Max Camber")
    profile_title_x, profile_title_y = 3 * inch, line_y - 15
    c.setFont("Times-Bold", 12)
    c.drawString(profile_title_x, profile_title_y, f"Max Profile Drop")
    haunch_title_x, haunch_title_y = 4.5 * inch, line_y - 15
    c.setFont("Times-Bold", 12)
    c.drawString(haunch_title_x, haunch_title_y, f"Max Variable Haunch")
    haunch_loc_title_x, haunch_loc_title_y = 6.5 * inch, line_y - 15
    c.setFont("Times-Bold", 12)
    c.drawString(haunch_loc_title_x, haunch_loc_title_y, f"Location")

    line_y -= 18
    c.setStrokeColor(colors.black)
    c.setLineWidth(0.8)
    c.line(0.7 * inch, line_y, width - 0.7 * inch, line_y)
    #### PRINT MAX HAUNCHES ####
    for i in range(inputs.bridge_info.n_beams):
      text_x = 1.5 * inch
      line_y -= 15
      c.setFont("Times-Bold", 12)
      c.drawString(0.7*inch, line_y, f"Beam {i+1}:")
      c.setFont("Times-Roman", 12)
      c.drawString(text_x, line_y, f"{np.max(results.final_haunch_obj.defl_final[start_index:end_index, 2 * i + 1]) / 12:.2f}")
      text_x = 3 * inch
      c.drawString(text_x, line_y, f"{np.max(results.final_haunch_obj.profile_deflections[start_index:end_index, 2 * i + 1]):.2f}")
      text_x = 4.5 * inch
      c.drawString(text_x, line_y, f"{np.max(results.final_haunch_obj.var_haunch_i[start_index:end_index, 2 * i + 1]):.2f}")
      text_x = 6.5 * inch
      haunch_loc = "Midspan" if results.final_haunch_obj.check_control_haunch[span, 2 * i] == 1 else "Span Ends"
      c.drawString(text_x, line_y, f"{haunch_loc}")

def master_create_PDF(inputs, results):
    pdf = "Bridge Deflections.pdf"
    c = canvas.Canvas(pdf, pagesize=letter)
    profile_curve_pdf(c, inputs, results)
    c.showPage()
    deck_section(c, inputs, results)
    c.showPage()
    generate_multi_page_pdf(c, inputs, results)
    c.showPage()
    create_beam_haunch_pdf(c, inputs, results)

    c.save()
