"""Reproduce the fan selection study; these are scaling calculations, not CFD.

Run from any directory with a Python environment containing matplotlib/numpy.
No CAD, firmware, ESC configuration, or existing design parameters are changed.
"""

from pathlib import Path
import csv
import hashlib
import json
import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch, PathPatch, Rectangle
from matplotlib.path import Path as MplPath
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "fan-shape-study-2026-10-09"
OUT.mkdir(parents=True, exist_ok=True)


def read(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


rotor = read("cad/rev_c/rotor-parameters.json")
head = read("cad/rev_c/head-parameters.json")
electrical = read("hardware/rev_c/motor-esc-specification.json")
assembly = read("cad/rev_c/head-validation.json")
export = read("cad/rev_c/integration-export-validation.json")
included = {p["name"] for p in export["components"]}
parts = [p for p in assembly["parts"] if p["name"] in included]
assert included <= {p["name"] for p in parts}, "Exported parts missing bounds"
zmin = min(p["bounds_xyz_mm"][4] for p in parts)
zmax = max(p["bounds_xyz_mm"][5] for p in parts)
height = zmax - zmin
geometry_inputs = {}
for relative, expected in assembly["input_sha256"].items():
    if "rev_c" in relative or "impeller" in relative:
        path = ROOT / relative
        geometry_inputs[relative] = path.is_file() and sha(path) == expected
assert all(geometry_inputs.values()), "Assembly report has stale Rev C geometry inputs"

d0 = rotor["rotor_diameter_mm"]
n0 = rotor["pitch_design_rpm"]
kv = electrical["motor"]["kv_rpm_per_volt"]
kt_low = 8.27 / kv  # ODrive's phase-current convention, illustrative only.
kt_high = 60 / (2 * math.pi * kv)  # SI-equivalent current convention.
phase_a = electrical["power_targets"]["motor_phase_current_initial_ceiling_a"]
input_w = electrical["power_targets"]["motor_esc_input_ceiling_w"]
rho = 1.2
a_open = head["outlet_width"] * head["outlet_height"] * 1e-6
area_floor = head["minimum_gross_outlet_ratio"]
a_boost = a_open * area_floor

diameters = [112, 125, 140, 150, 160, 170]
scaling = []
for d in diameters:
    ratio = d / d0
    n = n0 / ratio**3
    scaling.append({
        "diameter_mm": d,
        "rpm_equal_flow_similar_fan": n,
        "tip_speed_equal_flow_m_s": math.pi * d * 1e-3 * n / 60,
        "pressure_fraction_equal_flow": ratio**-4,
        "shaft_power_fraction_equal_flow": ratio**-4,
        "shaft_torque_fraction_equal_flow": ratio**-1,
        "shaft_power_multiplier_equal_rpm": ratio**5,
    })

boost = []
for retention in [1.0, .95, .90, .85, .80, .75, .70]:
    boost.append({
        "measured_flow_retention_at_same_rpm": retention,
        "outlet_area_fraction": area_floor,
        "mean_velocity_ratio": retention / area_floor,
        "velocity_gain_percent": 100 * (retention / area_floor - 1),
    })

motor = []
for rpm in [1500, 2000, 2500, 3000]:
    omega = rpm * 2 * math.pi / 60
    motor.append({
        "rpm": rpm,
        "estimated_electromagnetic_power_low_w_at_3a": kt_low * phase_a * omega,
        "estimated_electromagnetic_power_high_w_at_3a": kt_high * phase_a * omega,
        "illustrative_current_low_a_for_10w_shaft": 10 / (omega * kt_high),
        "illustrative_current_high_a_for_10w_shaft": 10 / (omega * kt_low),
    })

candidate = {
    "status": "Analytical candidate, not CAD or operating qualification",
    "architecture": "Ducted swept/twisted five-blade axial rotor with pressure bias",
    "rotor_diameter_mm": 150,
    "hub_diameter_mm": 40,
    "nominal_radial_tip_gap_mm_for_fit_study": 1,
    "throat_diameter_mm": 152,
    "inlet_lip_radius_mm": 12,
    "wall_mm": 2.4,
    "calculated_inlet_outer_diameter_mm": 152 + 2 * 12 + 2 * 2.4,
    "head_vertical_budget_including_guards_and_linkage_mm": 185,
    "base_and_feet_extension_below_head_mm": 10,
    "target_total_height_mm": 195,
    "height_reserve_to_200_mm": 5,
    "screen_controls_location": "Below outlet at front, within lower head envelope",
    "electronics_location": "Outside duct in downstream lower/side pockets",
    "normal_maximum_fraction_of_qualified_boost_rpm": .8,
    "blade_count_comparator": 7,
    "architecture_comparator": "Mild mixed-flow rotor if axial stage loses flow in boost",
    "fan_curve_available": False,
    "noise_measurements_available": False,
    "absolute_velocity_prediction_available": False,
}
candidate["rotor_annulus_area_m2"] = math.pi / 4 * (.150**2 - .040**2)
candidate["open_outlet_to_rotor_annulus_area_ratio"] = a_open / candidate["rotor_annulus_area_m2"]
candidate["minimum_outlet_to_rotor_annulus_area_ratio"] = a_boost / candidate["rotor_annulus_area_m2"]

ideal_power = motor[-1]["estimated_electromagnetic_power_high_w_at_3a"]
result = {
    "study_date": "2026-10-09",
    "method": "Similarity laws, torque/power estimate, continuity and envelope arithmetic",
    "limitations": [
        "No CFD, blade-element validation, motor loss map, fan curve, acoustic prediction or physical test.",
        "Similarity cases scale every dimension; fixed motor/hub/outlet of real candidates violate exact similarity.",
        "Kt range represents two current conventions, not a measured tolerance or validated VESC conversion.",
        "Electromagnetic power estimates omit motor friction/core losses and are not measured shaft output.",
        "Pressure and torque at the actual nozzle require fan/system curves, not free-flow scaling.",
        "Height proposal is a budget; screen, cables, cooling and linkage have not been placed in revised CAD.",
        "3000 RPM remains a historical guarded trial ceiling; a larger rotor has no approved operating RPM.",
    ],
    "sources": {
        "motor": "https://www.ligpower.com/product/p2406-fpv-freestyle-motor.html",
        "esc": "https://teamtriforceuk.com/a50s-v2/",
        "fan_laws": "https://beckettair.com/resources/fan-laws/",
        "similarity_conditions": "https://ansyshelp.ansys.com/public/Views/Secured/MotorCAD/v252/en/Motor-CAD_UG/MotorCAD/topics/airflow.html",
        "phase_current_torque_convention": "https://newdocs.odriverobotics.com/v/latest/guides/odrivetool-setup.html",
        "fan_architectures": "https://mag.ebmpapst.com/en/insights/axial-diagonal-centrifugal_2447/",
        "tip_noise": "https://mag.ebmpapst.com/en/products/fans/the-formula-for-vorticity_11766/",
        "stator_interaction": "https://ntrs.nasa.gov/citations/19850011481",
    },
    "current_design": {
        "motor": electrical["motor"]["model"],
        "kv_rpm_per_v": kv,
        "esc_input_limit_w": input_w,
        "initial_phase_current_limit_a": phase_a,
        "included_export_part_groups": len(included),
        "recorded_min_z_mm": zmin,
        "recorded_max_z_mm": zmax,
        "recorded_total_height_mm": height,
        "tallest_part": max(parts, key=lambda p: p["bounds_xyz_mm"][5])["name"],
        "lowest_part": min(parts, key=lambda p: p["bounds_xyz_mm"][4])["name"],
        "report_rev_c_geometry_hash_matches": geometry_inputs,
    },
    "similar_fan_equal_flow_cases": scaling,
    "same_rpm_boost_cases": boost,
    "motor_estimates": motor,
    "candidate": candidate,
    "outlet": {"open_gross_area_m2": a_open, "minimum_gross_area_m2": a_boost},
    "ideal_energy_bounds_not_predictions": {
        "assumptions": "Uniform ambient-pressure jet, rho=1.2, all power becomes jet kinetic energy; real mean velocity is lower. Gross area includes blocked regions.",
        "open_velocity_m_s_from_18w_input": (2 * input_w / (rho * a_open))**(1/3),
        "boost_velocity_m_s_from_18w_input": (2 * input_w / (rho * a_boost))**(1/3),
        "open_velocity_m_s_from_3a_high_kt_3000rpm": (2 * ideal_power / (rho * a_open))**(1/3),
        "boost_velocity_m_s_from_3a_high_kt_3000rpm": (2 * ideal_power / (rho * a_boost))**(1/3),
    },
    "input_sha256": {},
}
for relative in ["cad/rev_c/rotor-parameters.json", "cad/rev_c/head-parameters.json",
                 "hardware/rev_c/motor-esc-specification.json", "cad/rev_c/head-validation.json",
                 "cad/rev_c/integration-export-validation.json", "firmware/WindflowRevC/Config.h",
                 "firmware/WindflowRevC/Control.cpp", "tools/analyse_fan_shapes.py"]:
    result["input_sha256"][relative] = sha(ROOT / relative)

for filename, rows in [("diameter-scaling.csv", scaling), ("boost-retention.csv", boost),
                       ("motor-power-estimates.csv", motor)]:
    with (OUT / filename).open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                    "axes.spines.top": False, "axes.spines.right": False,
                    "axes.titleweight": "bold", "axes.grid": True,
                    "grid.alpha": .16, "figure.facecolor": "#f6f8fb",
                    "axes.facecolor": "white"})
fig, axes = plt.subplots(2, 2, figsize=(13.4, 10))
fig.suptitle("Windflow: rotor size, motor loading and useful boost", fontsize=19, fontweight="bold", y=.98)
fig.text(.5, .945, "Analytical comparisons • existing P2406 2060KV motor • no measured fan/noise curve", ha="center", color="#536176")

ax = axes[0, 0]
ax.plot(diameters, [r["rpm_equal_flow_similar_fan"] for r in scaling], "o-", color="#126c8e", linewidth=2)
ax.set(xlabel="Rotor diameter (mm)", ylabel="RPM for equal flow", title="Larger rotors can lower RPM")
right = ax.twinx()
right.plot(diameters, [r["pressure_fraction_equal_flow"] * 100 for r in scaling], "s--", color="#b85d21", linewidth=2)
right.set_ylabel("Pressure retained (%)", color="#b85d21")
right.spines["top"].set_visible(False)
right.grid(False)
right.set_ylim(0, 110)
ax.annotate("150 mm: ~1,249 RPM\n31% of reference pressure", xy=(150, scaling[3]["rpm_equal_flow_similar_fan"]), xytext=(133, 2700), arrowprops={"arrowstyle": "->", "color": "#536176"}, fontsize=9)
ax.text(.02, .03, "Exact geometric similarity only; reference = 112 mm / 3,000 RPM", transform=ax.transAxes, fontsize=8, color="#536176")

ax = axes[0, 1]
ns = np.linspace(1000, 3000, 100)
lo = kt_low * phase_a * ns * 2 * math.pi / 60
hi = kt_high * phase_a * ns * 2 * math.pi / 60
ax.fill_between(ns, lo, hi, color="#126c8e", alpha=.20)
ax.plot(ns, hi, color="#126c8e", linewidth=2, label="3 A: two Kt/current conventions")
ax.axhline(input_w, color="#b85d21", linestyle="--", label="18 W ESC input budget")
ax.set(xlabel="Mechanical RPM", ylabel="Power (W)", title="The current torque limit matters", ylim=(0, 20))
ax.legend(loc="upper left", frameon=True, facecolor="white", edgecolor="none", framealpha=1, fontsize=9)
ax.text(.05, .33, "At 3,000 RPM: ~3.8–4.4 W electromagnetic\npower before friction/core losses.\nInput watts and shaft watts differ.", transform=ax.transAxes, fontsize=9)
ax.text(.02, .03, "Illustrative convention range, not a measured VESC torque map", transform=ax.transAxes, fontsize=8, color="#536176")

ax = axes[1, 0]
retention = np.linspace(.65, 1, 100)
for fraction, color in [(1, "#8793a3"), (.85, "#629d73"), (.8, "#126c8e"), (.75, "#b85d21")]:
    ax.plot(retention * 100, (retention / fraction - 1) * 100, color=color, linewidth=2, label=f"{fraction:.0%} outlet area")
ax.axhline(20, color="#8994a3", linestyle=":")
ax.plot([90], [20], "o", color="#b85d21")
ax.set(xlabel="Flow retained after closure at same RPM (%)", ylabel="Average outlet speed gain (%)", title="A smaller outlet works only if flow holds up", ylim=(-40, 40))
ax.legend(frameon=False, fontsize=9)
ax.text(.03, .08, "75% area + 90% retained flow = 20% speed increase", transform=ax.transAxes, fontsize=9)

ax = axes[1, 1]
ax.barh([1], [height], color="#b85d21", height=.40)
ax.barh([0], [185], color="#126c8e", height=.40, label="Head incl. inlet, guards and linkage")
ax.barh([0], [10], left=[185], color="#629d73", height=.40, label="Base / feet extension")
ax.axvline(200, color="#414e63", linestyle="--")
ax.set(yticks=[0, 1], yticklabels=["Proposed budget", "Current CAD report"], xlabel="Complete product height (mm)", title="Fit the controls inside the head's height", xlim=(0, 230), ylim=(-.7, 1.7))
ax.text(height - 4, 1, f"{height:.1f} mm", ha="right", va="center", color="white", fontweight="bold")
ax.text(100, 0, "185 + 10 = 195 mm", ha="center", va="center", color="white", fontweight="bold")
ax.text(201, 1.45, "200 mm limit", color="#414e63", fontsize=9)
ax.legend(loc="upper left", frameon=False, fontsize=8)
ax.text(.02, .03, "Proposed packaging arithmetic; revised 3D fit is unverified", transform=ax.transAxes, fontsize=8, color="#536176")

fig.text(.5, .02, "Similarity laws show tradeoffs. They do not predict a new rotor's operating point, safe speed or sound level.", ha="center", color="#536176", fontsize=10)
fig.subplots_adjust(left=.075, right=.91, top=.89, bottom=.09, hspace=.42, wspace=.40)
fig.savefig(OUT / "fan-tradeoffs.png", dpi=180)
fig.savefig(OUT / "fan-tradeoffs.svg")
plt.close(fig)

# A schematic communicates the selected planform and vertical packaging concept.
# It is deliberately separate from the manufactured CAD and aerodynamic geometry.
fig, (ax, layout) = plt.subplots(1, 2, figsize=(12, 6.2))
fig.suptitle("Proposed rotor and 195 mm layout concept", fontsize=19, fontweight="bold", y=.97)
fig.text(.5, .91, "Concept schematic: blade profiles and component placement require detailed design", ha="center", color="#536176")
ax.set_aspect("equal")
ax.add_patch(Circle((0, 0), 76, fill=False, linewidth=2, color="#8793a3", linestyle="--"))
# One smoothly swept blade, repeated with exact rotational symmetry.
vertices = [(18, -9), (33, -17), (51, -9), (68, 12),
            (77, 23), (71, 35), (63, 31),
            (49, 24), (34, 12), (18, 10), (18, -9)]
codes = [MplPath.MOVETO] + [MplPath.CURVE4] * 9 + [MplPath.CLOSEPOLY]
for angle in np.linspace(0, 2 * math.pi, 5, endpoint=False):
    matrix = np.array([[math.cos(angle), -math.sin(angle)], [math.sin(angle), math.cos(angle)]])
    coords = np.array(vertices) @ matrix.T
    ax.add_patch(PathPatch(MplPath(coords, codes), facecolor="#6ca9bb", edgecolor="#126c8e", linewidth=1.6))
ax.add_patch(Circle((0, 0), 20, color="#126c8e"))
ax.add_patch(Circle((0, 0), 2.6, color="white"))
ax.annotate("~40 mm hub", xy=(0, 0), xytext=(-86, -92), arrowprops={"arrowstyle": "->", "color": "#536176"}, fontsize=10)
ax.annotate("Cambered, twisted\nsections along each blade", xy=(50, 14), xytext=(13, 85), arrowprops={"arrowstyle": "->", "color": "#536176"}, fontsize=10)
ax.annotate("", xy=(-75, -80), xytext=(75, -80), arrowprops={"arrowstyle": "<->", "color": "#536176"})
ax.text(0, -89, "150 mm swept rotor", ha="center", fontsize=10)
ax.set(xlim=(-105, 105), ylim=(-104, 112), title="Five evenly spaced blades")
ax.axis("off")

layout.set_aspect("equal")
layout.add_patch(FancyBboxPatch((-95, 10), 190, 185, boxstyle="round,pad=0,rounding_size=25", facecolor="#e8edf3", edgecolor="#536176", linewidth=2))
layout.add_patch(Circle((0, 102.5), 90.4, fill=False, edgecolor="#8793a3", linestyle="--", linewidth=1.2))
layout.add_patch(FancyBboxPatch((-52, 55.5), 104, 94, boxstyle="round,pad=0,rounding_size=3", facecolor="white", edgecolor="#126c8e", linewidth=2))
layout.text(0, 105, "104 × 94 mm\noutlet", ha="center", va="center", color="#126c8e", fontsize=12)
layout.add_patch(FancyBboxPatch((-29, 10.5), 78, 39.6, boxstyle="round,pad=0,rounding_size=3", facecolor="#24384e", edgecolor="#24384e"))
layout.add_patch(Rectangle((-12.5, 35.5), 45, 8, color="#6ca9bb"))
layout.text(10, 24, "Screen", ha="center", va="center", color="white", fontsize=10)
layout.add_patch(Circle((-66, 31), 15, facecolor="#6ca9bb", edgecolor="#126c8e", linewidth=2))
layout.add_patch(FancyBboxPatch((-95, 0), 190, 10, boxstyle="round,pad=0,rounding_size=3", facecolor="#629d73", edgecolor="#629d73"))
layout.annotate("", xy=(111, 0), xytext=(111, 195), arrowprops={"arrowstyle": "<->", "color": "#536176"})
layout.text(119, 97.5, "195 mm total", rotation=90, va="center", fontsize=11)
layout.axhline(200, color="#b85d21", linestyle="--", linewidth=1)
layout.text(-94, 204, "200 mm limit: 5 mm reserve", color="#b85d21", fontsize=10)
layout.annotate("Inlet envelope at rear\n180.8 mm outer diameter", xy=(64, 160), xytext=(-92, 174), arrowprops={"arrowstyle": "->", "color": "#536176"}, fontsize=9)
layout.text(0, -14, "Screen/encoder at front below outlet;\nelectronics in lower/side pockets outside duct", ha="center", fontsize=9, color="#536176")
layout.set(xlim=(-115, 144), ylim=(-30, 221), title="Controls share the head's height")
layout.axis("off")
fig.text(.5, .025, "Planform is illustrative. Front layout uses width/depth for electronics; this is not a clearance-checked assembly.", ha="center", color="#536176", fontsize=9)
fig.subplots_adjust(left=.04, right=.95, top=.83, bottom=.10, wspace=.20)
fig.savefig(OUT / "rotor-and-layout-concept.png", dpi=180)
fig.savefig(OUT / "rotor-and-layout-concept.svg")
plt.close(fig)

assert abs(height - 215.8510021439355) < .01
assert candidate["target_total_height_mm"] <= 200
assert math.isclose(boost[2]["mean_velocity_ratio"], 1.2)
assert math.isclose(scaling[3]["pressure_fraction_equal_flow"], (112 / 150)**4)
assert 3.7 < motor[-1]["estimated_electromagnetic_power_low_w_at_3a"] < 3.9
assert 4.3 < motor[-1]["estimated_electromagnetic_power_high_w_at_3a"] < 4.5
result["verification"] = "PASS: geometry provenance, envelope and numerical identities; no physical validation"
(OUT / "calculations.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"result": result["verification"], "current_height_mm": height,
                  "candidate_height_budget_mm": 195, "150mm_equal_flow_rpm": scaling[3]["rpm_equal_flow_similar_fan"],
                  "phase_3a_electromagnetic_power_at_3000rpm_w": [motor[-1]["estimated_electromagnetic_power_low_w_at_3a"], ideal_power],
                  "output": str(OUT)}, indent=2))
