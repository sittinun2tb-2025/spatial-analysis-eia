import os
import numpy as np
import qrcode as qr
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import contextily as ctx

plt.rcParams["font.family"] = "TH Sarabun New"
plt.rcParams["font.size"] = 16

dir_app = os.path.dirname(os.path.abspath(__file__))

def load(name, layer=None):
    return gpd.read_file(os.path.join(dir_app, "data", name), layer=layer).to_crs(epsg=3857)

def _kind(layer_name):
    if layer_name.startswith("point_"): return "point"
    if layer_name.startswith("line_"):  return "line"
    return "patch"

# ── รายการข้อมูล ───────────────────────────────────────────────────
layer_analysis = [
    {"name": "water_natural", "file": "แหล่งน้ำธรรมชาติ.gpkg", "layer": "point_แหล่งน้ำธรรมชาติ",  "label": "แหล่งน้ำธรรมชาติ",        "color": "#0015ff", "visible": True, "zIndex": 10},
    {"name": "arts_point",    "file": "แหล่งศิลปกรรม1.gpkg",   "layer": "point_แหล่งศิลปกรรม",    "label": "แหล่งศิลปกรรม (จุด)",    "color": "#ff0000", "visible": True, "zIndex": 9},
    {"name": "water",         "file": "แหล่งน้ำ.gpkg",          "layer": "line_แหล่งน้ำ",           "label": "แหล่งน้ำ",                "color": "#0328fc", "visible": True, "zIndex": 8},
    {"name": "bioregion",     "file": "ผังภูมินิเวศ.gpkg",      "layer": "polygon_ผังภูมินิเวศ",    "label": "ผังภูมินิเวศ",            "color": "#40ff00", "visible": True, "zIndex": 7},
    {"name": "heritage",      "file": "แหล่งมรดกโลก.gpkg",     "layer": "polygon_แหล่งมรดกโลก",   "label": "แหล่งมรดกโลก",           "color": "#eaff00", "visible": True, "zIndex": 6},
    {"name": "arts_polygon",  "file": "แหล่งศิลปกรรม2.gpkg",   "layer": "polygon_แหล่งศิลปกรรม",  "label": "แหล่งศิลปกรรม (พื้นที่)", "color": "#c45911", "visible": True, "zIndex": 5}
]

# ── โหลดข้อมูล ───────────────────────────────────────────────────
gdf_project = load("โครงการ.gpkg", layer="โครงการ")
gdf_loads = {
    item["name"]: load(item["file"], layer=item["layer"])
    for item in layer_analysis
    if item["visible"]
}

# # ── Buffer รอบโครงการ ────────────────────────────────────────────
buf_m = 2000
project_union = gdf_project.geometry.union_all()
buf_km = project_union.buffer(buf_m)
gdf_buf_km = gpd.GeoDataFrame(geometry=[buf_km], crs=3857)

# # ── Map extent จาก 5 km buffer ───────────────────────────────────
minx, miny, maxx, maxy = buf_km.bounds #EPSG:3857
pad = (maxx - minx) * 0.05
ext_x0, ext_x1 = minx - pad, maxx + pad
ext_y0, ext_y1 = miny - pad, maxy + pad

all_layers = pd.concat([
    gdf_loads[item["name"]][gdf_loads[item["name"]].intersects(buf_km)][["geometry"]].assign(label=item["label"])
    for item in layer_analysis if item["visible"]
], ignore_index=True)

category_counts = all_layers.groupby("label").size().sort_values(ascending=False)


# ── Map Plot ───────────────────────────────────
# First subplot (row 1, col 1, index 1=left 2=right)
A4_W, A4_H = 10, 6
map_aspect   = (ext_x1 - ext_x0) / (ext_y1 - ext_y0)
map_w_in     = map_aspect * (A4_H * 0.9)
info_w_in    = A4_W - map_w_in

fig = plt.figure(figsize=(A4_W, A4_H), dpi=100)

gs = gridspec.GridSpec(
    2, 2,
    figure=fig,
    height_ratios=[0.1, 0.9],
    width_ratios=[map_w_in, info_w_in],
    hspace=0.0, wspace=0.0
)
fig.subplots_adjust(left=0.0, right=1.0, top=1.0, bottom=0.0, wspace=0.0, hspace=0.0)

ax_title = fig.add_subplot(gs[0, :])    # title (บนกว้างเต็ม)
ax_map   = fig.add_subplot(gs[1, 0])    # map   (ล่างซ้าย)
ax_info  = fig.add_subplot(gs[1, 1])    # info  (ล่างขวา)

ax_title.axis("off")

ax_map.axis("off")

ax_info.axis("off")
ax_info.set_xlim(0, 1)
ax_info.set_ylim(0, 1)
ax_info.set_autoscale_on(False)

#ax_title.add_patch(mpatches.FancyBboxPatch((0, 0), 1, 1, boxstyle="square,pad=0",
#    facecolor="white", edgecolor="black", lw=1, transform=ax_title.transAxes, clip_on=False))
ax_title.text(0.5, 0.5, "แผนที่แสดงแหล่งธรรมชาติและแหล่งศิลปกรรมอันควรอนุรักษ์ ในระยะ %s กิโลเมตร" % int(buf_m / 1000),
    ha="center", va="center", fontsize=20, fontweight="bold")

ax_map.add_patch(mpatches.FancyBboxPatch(
                                        (0, 0), 1, 1, #box with (x, y), width, and height
                                         boxstyle="square,pad=0",
                                         facecolor="white", edgecolor="black", lw=1, transform=ax_map.transAxes, clip_on=False))
    
ax_info.add_patch(mpatches.FancyBboxPatch((0, 0), 1, 1, boxstyle="square,pad=0",
    facecolor="white", edgecolor="black", lw=1, transform=ax_info.transAxes, clip_on=False))


# ══════════════════════════════════════════════════════════════════
#  Map layers  (วาดจาก ล่าง → บน)
# ══════════════════════════════════════════════════════════════════
max_z = max(item["zIndex"] for item in layer_analysis if item["visible"])

# 1. แนวเส้นทางโครงการ
gdf_project.plot(ax=ax_map, color="#ff0000", lw=2.5, zorder=max_z + 2)

# 2. Buffer km – เส้นประแดง
gdf_buf_km.plot(ax=ax_map, facecolor="none", edgecolor="red", lw=1.8, linestyle="--", zorder=max_z + 1)

# 3. Analysis layers (visible=True จาก layer_analysis)
for item in [i for i in layer_analysis if i["visible"]]:
    gdf_loads[item["name"]].plot(ax=ax_map, color=item["color"], alpha=0.6, zorder=item["zIndex"])

# 4. Satellite basemap
ctx.add_basemap(ax_map, source=ctx.providers.Esri.WorldImagery, zoom="auto", zorder=1)

ax_map.set_xlim(ext_x0, ext_x1)
ax_map.set_ylim(ext_y0, ext_y1)

# ══════════════════════════════════════════════════════════════════
# ── Table (dynamic จาก site_category_name) ──
# ══════════════════════════════════════════════════════════════════
table_rows = [("ประเภทแหล่ง", "จำนวนแหล่ง", "#3a7ebf", "white", True)]
for idx, (cat, cnt) in enumerate(category_counts.items()):
    table_rows.append((cat, str(cnt), "white", "black", False))
table_rows.append(("รวม", str(category_counts.sum()), "white", "black", True))

t_top = 1.0 #0.97
row_h = 0.06
col_w = [0.67, 0.33]

for i, (label, value, bg, fg, bold) in enumerate(table_rows):
    y_bot = t_top - (i + 1) * row_h
    fw = "bold" if bold else "normal"
    for j, (w, txt) in enumerate(zip(col_w, [label, value])):
        x_left = sum(col_w[:j])
        ax_info.add_patch(mpatches.Rectangle(
            (x_left, y_bot), w, row_h, facecolor=bg, edgecolor="#aaaaaa", lw=0.5, zorder=2))
        ax_info.text(x_left + w / 2, y_bot + row_h / 2, txt,
            ha="center", va="center", fontsize=14, color=fg, fontweight=fw, zorder=3)

# ══════════════════════════════════════════════════════════════════
# # ── Legend ──
# ══════════════════════════════════════════════════════════════════
leg_top = t_top - len(table_rows) * row_h #- 0.035
# Header box
ax_info.add_patch(mpatches.FancyBboxPatch(
    (0, leg_top - 0.075), 1.0, 0.075, boxstyle="square, pad=0", facecolor="#3a7ebf", edgecolor="#aaaaaa", lw=0.8))
ax_info.text(0.5, leg_top - 0.037, "คำอธิบายสัญลักษณ์",
    ha="center", va="center", fontsize=14, color="white", fontweight="bold")


_kind_order = {"point": 0, "line": 1, "dash": 2, "patch": 3}

legend_items = sorted([
    (_kind(item["layer"]), item["color"], None, item["label"])
    for item in layer_analysis if item["visible"]
] + [
    ("dash", "red",     None, "รัศมีโครงการ %s กิโลเมตร" % int(buf_m / 1000)),
    ("line", "#ff0000", None, "แนวเส้นทางโครงการ"),
], key=lambda x: _kind_order.get(x[0], 99))

n_leg       = len(legend_items)
leg_avail   = leg_top - 0.075 - 0.02
row_h_leg   = min(0.075, leg_avail / n_leg)
scale       = row_h_leg / 0.075
fontsize_leg = max(8, round(14 * scale))
markersize  = max(3, 8 * scale)
lw_leg      = max(1.0, 2.5 * scale)
rect_h      = max(0.01, 0.036 * scale)

ly = leg_top - 0.075 - row_h_leg / 2
for kind, color, edgecolor, label in legend_items:
    if kind == "point":
        ax_info.plot(0.09, ly, "o", color=color, markersize=markersize, zorder=3)
    elif kind == "line":
        ax_info.plot([0.02, 0.17], [ly, ly], color=color, lw=lw_leg, zorder=3, solid_capstyle="butt")
    elif kind == "patch":
        ec = edgecolor if edgecolor else color
        ax_info.add_patch(mpatches.Rectangle(
            (0.02, ly - rect_h / 2), 0.15, rect_h,
            facecolor=color, edgecolor=ec, lw=0.8, zorder=3))
    elif kind == "dash":
        ax_info.plot([0.02, 0.17], [ly, ly], color=color, lw=lw_leg * 0.8, linestyle="--", zorder=3)
    ax_info.text(0.21, ly, label, ha="left", va="center", fontsize=fontsize_leg)
    ly -= row_h_leg

# ══════════════════════════════════════════════════════════════════
# ── QR Code ──
# ══════════════════════════════════════════════════════════════════
url_data = "https://www.google.com"
qr_obj = qr.QRCode(box_size=4, border=1)
qr_obj.add_data(url_data)
qr_obj.make(fit=True)
qr_img = np.array(qr_obj.make_image(fill_color="black", back_color="white").convert("RGB"))
qr_size = 0.20
qr_x    = 0.62
qr_y    = leg_top - 0.085 - qr_size
ax_info.imshow(qr_img,
    extent=[qr_x, qr_x + qr_size, qr_y, qr_y + qr_size],
    aspect="auto", origin="upper", zorder=5, clip_on=True)
ax_info.text(qr_x + qr_size / 2, qr_y, "ดาวน์โหลดข้อมูล",
    ha="center", va="top", fontsize=14, transform=ax_info.transAxes, clip_on=True)

# ══════════════════════════════════════════════════════════════════
# ── Logo ──
# ══════════════════════════════════════════════════════════════════
logo_path = os.path.join(dir_app, "logo.png")
logo_img  = plt.imread(logo_path)
logo_size = 0.10
logo_x    = qr_x + (qr_size - logo_size) / 2
logo_y    = qr_y - 0.06 - logo_size
ax_info.imshow(logo_img,
    extent=[logo_x, logo_x + logo_size, logo_y, logo_y + logo_size],
    aspect="auto", origin="upper", zorder=5, clip_on=True)

ax_info.text(qr_x + qr_size / 2, logo_y - 0.01,
    "สำนักงานนโยบายและแผนก\nทรัพยากรธรรมชาติและสิ่งแวดล้อม (สผ.)",
    ha="center", va="top", fontsize=10, transform=ax_info.transAxes, linespacing=1.4, clip_on=True)

plt.show()
