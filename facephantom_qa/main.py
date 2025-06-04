# face_phantom_field_coincidence_v2.0.py
# ------------------------------------------------------
# PyLinac Integration Module - Light & Radiation Field Coincidence QA
# Developed by: Alex Hastava
#
# Description:
# This script performs field coincidence quality assurance by comparing the light field
# (constructed from BB marker detection) and radiation field (via PyLinac's FieldAnalysis)
# on EPID-acquired DICOM images. Results are output to a summary PDF and CSV.
#
# Requirements: OpenCV, NumPy, PyDICOM, PyLinac, Matplotlib
# Hardware: Requires use of the proprietary FacePhantom device for BB marker detection

import os
import re
import cv2
import numpy as np
import pydicom
import tkinter as tk
from tkinter import filedialog
from pylinac import Edge, FieldAnalysis, Centering, Interpolation, Protocol
from matplotlib import pyplot as plt
from matplotlib import image as mpimg
from matplotlib.backends.backend_pdf import PdfPages
import csv
import warnings

warnings.filterwarnings("ignore", message=".*missing from font.*", category=UserWarning)

csv_results = []

def enhance_image(img_array):
    """Enhance DICOM image for BB detection using CLAHE and Gaussian blur."""
    img = img_array.astype('uint16')
    img_norm = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX).astype('uint8')
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    img_clahe = clahe.apply(img_norm)
    img_blur = cv2.GaussianBlur(img_clahe, (5, 5), 0)
    return img_blur

def find_bb_markers(enhanced_img, px_spacing, sid, sod):
    """Detect BBs using Hough Circle Transform, scaled to expected size at SID."""
    bb_radius_mm = 7.5
    scale_imgr = sid / sod
    effective_radius_mm = bb_radius_mm * scale_imgr

    px_size = px_spacing[0]  # assume square pixels
    radius_px = effective_radius_mm / px_size
    min_radius_px = int(radius_px * 0.85)
    max_radius_px = int(radius_px * 1.15)
    min_dist_px = int(radius_px * 2.0 * 0.9)

    circles = cv2.HoughCircles(
        enhanced_img,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=min_dist_px,
        param1=20,
        param2=40,
        minRadius=min_radius_px,
        maxRadius=max_radius_px
    )

    if circles is not None:
        return np.uint16(np.around(circles[0]))
    return []

def extract_metadata(ds):
    """Extract relevant DICOM metadata fields."""
    return {
        'RT Image Description': ds.get('RTImageDescription', ''),
        'Radiation Machine Name': ds.get('RadiationMachineName', ''),
        'SAD': ds.get('RadiationMachineSAD', 'N/A'),
        'SID': ds.get('RTImageSID', 'N/A')
    }

def process_and_plot(filepath, pdf):
    """Process a single DICOM file: analyze fields, overlay visuals, and write to PDF."""
    ds = pydicom.dcmread(filepath)
    img = ds.pixel_array.astype(float)
    px_spacing = ds.get('PixelSpacing', ds.get('ImagePlanePixelSpacing', [1.0, 1.0]))
    enhanced = enhance_image(img)
    metadata = extract_metadata(ds)

    sid = float(metadata.get('SID', 1500))
    sod = float(metadata.get('SAD', 1000))
    gantry_angle = float(ds.get("GantryAngle", 0.0))

    def extract_couch_angle_from_filename(filepath):
        """Determine couch angle from filename tag."""
        filename = os.path.basename(filepath).lower()
        angle_map = {
            "45_couch": 45, "90_couch": 90, "180_couch": 180,
            "45m_couch": -45, "90m_couch": -90, "180m_couch": -180,
        }
        for key, angle in angle_map.items():
            if key in filename:
                return angle
        return 0.0

    couch_angle = extract_couch_angle_from_filename(filepath)
    scale_imgr = sid / sod  # EPID/SAD
    scale_couch = 1.0 / scale_imgr

    # Radiation field analysis (in SAD space)
    analyzer = FieldAnalysis(filepath)
    analyzer.analyze(
        centering=Centering.BEAM_CENTER,
        edge_detection_method=Edge.INFLECTION_DERIVATIVE,
        interpolation=Interpolation.LINEAR,
        interpolation_resolution_mm=0.1,
        protocol=Protocol.VARIAN,
    )
    results = analyzer.results_data()
    rad_cx_px, rad_cy_px = results.beam_center_index_x_y
    rad_cx_mm = rad_cx_px * px_spacing[1]
    rad_cy_mm = rad_cy_px * px_spacing[0]

    fig, (ax_img, ax_table) = plt.subplots(2, 1, figsize=(9, 12), gridspec_kw={'height_ratios': [9, 3], 'hspace': 0.5})
    ax_img.imshow(img, cmap='gray')
    ax_img.plot(rad_cx_px, rad_cy_px, marker='+', color='magenta', markersize=10, markeredgewidth=2, label='Radiation Center')

    csv_row = {'Filename': os.path.basename(filepath)}
    table_data = []
    col_labels = ['Edge', 'LF→LF-Center (mm)', 'RF→CAX (mm)', 'Δ (mm)', 'Result']
    max_diff = 0

    # BB marker detection and pairing
    markers = find_bb_markers(enhanced, px_spacing, sid, sod)
    if markers is None or len(markers) < 4:
        print(f"Insufficient BBs: {filepath}")
        return

    top = sorted(markers, key=lambda m: m[1])[:2]
    bottom = sorted(markers, key=lambda m: m[1])[-2:]
    left = sorted(markers, key=lambda m: m[0])[:2]
    right = sorted(markers, key=lambda m: m[0])[-2:]

    def shifted_midpoint_mm(pair, axis, direction):
        """Return midpoint shifted 15mm in a given direction (SID plane)."""
        x_px = np.mean([p[0] for p in pair])
        y_px = np.mean([p[1] for p in pair])
        shift_mm = 15
        if axis == 'x':
            x_mm = x_px * px_spacing[1] + direction * shift_mm * scale_imgr
            y_mm = y_px * px_spacing[0]
        else:
            x_mm = x_px * px_spacing[1]
            y_mm = y_px * px_spacing[0] + direction * shift_mm * scale_imgr
        return x_mm, y_mm

    # Get light field edges (in mm @ SID)
    corners_mm = {
        'Top': shifted_midpoint_mm(top, 'y', -1),
        'Bottom': shifted_midpoint_mm(bottom, 'y', 1),
        'Left': shifted_midpoint_mm(left, 'x', -1),
        'Right': shifted_midpoint_mm(right, 'x', 1),
    }

    # Light field center (in mm @ SID)
    lf_cx_mm = (corners_mm['Left'][0] + corners_mm['Right'][0]) / 2
    lf_cy_mm = (corners_mm['Top'][1] + corners_mm['Bottom'][1]) / 2
    ax_img.plot(lf_cx_mm / px_spacing[1], lf_cy_mm / px_spacing[0], marker='x', color='cyan', label='LF Center')

    # Radiation edges (in mm @ SAD)
    rad_edges = {
        'Left': rad_cx_mm - results.beam_center_to_left_mm,
        'Right': rad_cx_mm + results.beam_center_to_right_mm,
        'Top': rad_cy_mm - results.beam_center_to_top_mm,
        'Bottom': rad_cy_mm + results.beam_center_to_bottom_mm,
    }

    # Compare LF and RF edge distances to respective centers
    for label, (lf_x_mm, lf_y_mm) in corners_mm.items():
        lf_to_center = np.hypot(lf_x_mm - lf_cx_mm, lf_y_mm - lf_cy_mm) * scale_couch  # scaled to SAD
        rf_to_center = abs(rad_edges[label] - (rad_cx_mm if label in ['Left', 'Right'] else rad_cy_mm))
        delta = abs(lf_to_center - rf_to_center)
        result = 'PASS' if delta <= 2.0 else 'FAIL'
        max_diff = max(max_diff, delta)
        ax_img.plot(lf_x_mm / px_spacing[1], lf_y_mm / px_spacing[0], marker='x',
                    color='#ff7f0e' if result == 'PASS' else '#d62728', markersize=9, markeredgewidth=2)
        table_data.append([label, f"{lf_to_center:.2f}", f"{rf_to_center:.2f}", f"{delta:.2f}", result])

    # Center offset distance
    center_dist = np.hypot(rad_cx_mm - lf_cx_mm, rad_cy_mm - lf_cy_mm) * scale_couch
    table_data.append(["Center Δ", f"{center_dist:.2f}", "-", "-", "PASS" if center_dist <= 2.0 else "FAIL"])

    def draw_box(ax, pts, color, label):
        box = pts + [pts[0]]
        ax.plot(*zip(*box), linestyle='--', linewidth=1.5, color=color, label=label)

    # Construct and draw LF box (at SID)
    lf_box_pts_mm = [
        (corners_mm['Left'][0], corners_mm['Top'][1]),
        (corners_mm['Right'][0], corners_mm['Top'][1]),
        (corners_mm['Right'][0], corners_mm['Bottom'][1]),
        (corners_mm['Left'][0], corners_mm['Bottom'][1])
    ]
    lf_box_pts_px = [(x / px_spacing[1], y / px_spacing[0]) for x, y in lf_box_pts_mm]

    # Construct RF box from midlines (SAD → scaled to SID)
    rad_edge_pts_mm = {
        'Top':    (rad_cx_mm, rad_cy_mm - results.beam_center_to_top_mm),
        'Bottom': (rad_cx_mm, rad_cy_mm + results.beam_center_to_bottom_mm),
        'Left':   (rad_cx_mm - results.beam_center_to_left_mm, rad_cy_mm),
        'Right':  (rad_cx_mm + results.beam_center_to_right_mm, rad_cy_mm),
    }
    rf_box_pts_mm = [
        (rad_edge_pts_mm['Left'][0], rad_edge_pts_mm['Top'][1]),
        (rad_edge_pts_mm['Right'][0], rad_edge_pts_mm['Top'][1]),
        (rad_edge_pts_mm['Right'][0], rad_edge_pts_mm['Bottom'][1]),
        (rad_edge_pts_mm['Left'][0], rad_edge_pts_mm['Bottom'][1])
    ]
    rf_box_pts_mm_scaled = [
        (rad_cx_mm + (x - rad_cx_mm) * scale_imgr, rad_cy_mm + (y - rad_cy_mm) * scale_imgr)
        for (x, y) in rf_box_pts_mm
    ]
    rf_box_pts_px = [(x / px_spacing[1], y / px_spacing[0]) for x, y in rf_box_pts_mm_scaled]

    draw_box(ax_img, lf_box_pts_px, 'blue', 'Light Field Boundary')
    draw_box(ax_img, rf_box_pts_px, 'magenta', 'Radiation Field Boundary')

    # Draw BBs
    for (x, y, r) in markers:
        ax_img.add_patch(plt.Circle((x, y), r, edgecolor='lime', fill=False, linewidth=1.5))

    # Table formatting
    ax_table.axis('off')
    table = ax_table.table(cellText=table_data, colLabels=col_labels, loc='center', cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(9.5)
    table.scale(1.1, 2.5)
    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_text_props(weight='bold')
        elif col == 4:
            val = cell.get_text().get_text()
            cell.set_facecolor('#d0f0c0' if val == 'PASS' else '#f8d7da')

    # Final layout and save
    ax_img.legend(loc='lower right', fontsize=7)
    ax_img.axis('off')
    fig.subplots_adjust(left=0.1, right=0.9, top=0.60, bottom=0.06)
    fig.suptitle(
        f"Field Coincidence QA: {os.path.basename(filepath)}\n"
        f"Machine: {metadata['Radiation Machine Name']} | Energy: {metadata['RT Image Description']}\n"
        f"Gantry: {gantry_angle:.1f}° | Couch: {couch_angle:.1f}° | Pixel Spacing: {px_spacing[1]:.3f} mm (X), {px_spacing[0]:.3f} mm (Y)",
        fontsize=10, y=0.91
    )

    pdf.savefig(fig)
    plt.close(fig)
    csv_row['QA Result'] = 'PASS' if max_diff <= 2.0 else 'FAIL'
    csv_row['Max Delta (mm)'] = f"{max_diff:.2f}"
    csv_results.append(csv_row)

def main():
    """Main entry: process user-selected DICOMs and output PDF/CSV."""
    root = tk.Tk()
    root.withdraw()
    files = filedialog.askopenfilenames(filetypes=[("DICOM files", "*.dcm")], title="Select DICOM QA Images")
    if not files:
        print("No files selected.")
        return

    with PdfPages("FieldCoincidenceQA_Report.pdf") as pdf:
        for file in files:
            process_and_plot(file, pdf)

    if csv_results:
        keys = csv_results[0].keys()
        with open("FieldCoincidenceQA_Results.csv", "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(csv_results)

    print("Analysis complete. Results saved to FieldCoincidenceQA_Report.pdf and FieldCoincidenceQA_Results.csv")

if __name__ == "__main__":
    main()