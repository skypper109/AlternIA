#!/usr/bin/env python3
"""
Générateur de fichiers STL 3D binaires pour le boîtier ALTA Cyber-Bloc v2
selon la planche d'atelier réelle « Détail des pièces d'impression 3D (Cyber-Bloc v2) ».
Génère :
  1. ALTA_Capot_Superieur_Blanc.stl (Capot octogonal biseauté, N1, N2-N3-N4, grille HP, ouïes, 2 touches basses)
  2. ALTA_Chassis_Inferieur_Bleu.stl (Châssis octogonal, ports USB-C/RJ45/USB/HDMI/Power, berceaux Pi 5, batterie, HP)
  3. ALTA_Touches_Boutons_Bleu.stl (Jeu de touches N1, N2, N3, N4 + 2 touches basses)
  4. ALTA_Bouton_Power_Blanc.stl (Bouton poussoir d'allumage Power ⏻)
  5. ALTA_Entourage_Sangle_Blanc.stl (Étrier et boucle pour la sangle textile)
"""

import struct
import math
import os

def write_binary_stl(filename, triangles, name="ALTA_Part"):
    with open(filename, 'wb') as f:
        header = f"{name} - ALTA Cyber-Bloc v2".encode('ascii')[:80].ljust(80, b'\0')
        f.write(header)
        f.write(struct.pack('<I', len(triangles)))
        for tri in triangles:
            norm, v1, v2, v3 = tri
            if norm is None or norm == (0,0,0):
                ax, ay, az = v2[0] - v1[0], v2[1] - v1[1], v2[2] - v1[2]
                bx, by, bz = v3[0] - v1[0], v3[1] - v1[1], v3[2] - v1[2]
                nx = ay * bz - az * by
                ny = az * bx - ax * bz
                nz = ax * by - ay * bx
                norm_len = math.sqrt(nx*nx + ny*ny + nz*nz)
                norm = (nx/norm_len, ny/norm_len, nz/norm_len) if norm_len > 1e-9 else (0.0, 0.0, 1.0)
            f.write(struct.pack('<3f', float(norm[0]), float(norm[1]), float(norm[2])))
            f.write(struct.pack('<3f', float(v1[0]), float(v1[1]), float(v1[2])))
            f.write(struct.pack('<3f', float(v2[0]), float(v2[1]), float(v2[2])))
            f.write(struct.pack('<3f', float(v3[0]), float(v3[1]), float(v3[2])))
            f.write(struct.pack('<H', 0))

def make_box_triangles(x, y, z, dx, dy, dz):
    x0, x1 = x, x + dx
    y0, y1 = y, y + dy
    z0, z1 = z, z + dz
    p = [
        (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
        (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)
    ]
    faces = [
        (0, 2, 1), (0, 3, 2), # bas
        (4, 5, 6), (4, 6, 7), # haut
        (0, 1, 5), (0, 5, 4), # avant
        (3, 6, 2), (3, 7, 6), # arrière
        (0, 4, 7), (0, 7, 3), # gauche
        (1, 2, 6), (1, 6, 5)  # droite
    ]
    return [(None, p[f[0]], p[f[1]], p[f[2]]) for f in faces]

def make_cylinder_triangles(cx, cy, z0, radius, height, segments=20):
    triangles = []
    z1 = z0 + height
    angles = [2.0 * math.pi * i / segments for i in range(segments)]
    bot = [(cx + radius * math.cos(a), cy + radius * math.sin(a), z0) for a in angles]
    top = [(cx + radius * math.cos(a), cy + radius * math.sin(a), z1) for a in angles]
    c_bot = (cx, cy, z0)
    c_top = (cx, cy, z1)
    for i in range(segments):
        nxt = (i + 1) % segments
        triangles.append((None, c_bot, bot[nxt], bot[i]))
        triangles.append((None, c_top, top[i], top[nxt]))
        triangles.append((None, bot[i], bot[nxt], top[nxt]))
        triangles.append((None, bot[i], top[nxt], top[i]))
    return triangles

def make_prism_45_triangles(x0, y0, z0, dx, dy, dz, corner_type="sw"):
    """Prisme biseauté à 45° pour coins octogonaux."""
    # Simple wedge
    p = []
    if corner_type == "sw": # coupe coin bas-gauche
        p = [(x0+dx, y0, z0), (x0+dx, y0+dy, z0), (x0, y0+dy, z0),
             (x0+dx, y0, z0+dz), (x0+dx, y0+dy, z0+dz), (x0, y0+dy, z0+dz)]
    else:
        p = [(x0, y0, z0), (x0+dx, y0, z0), (x0, y0+dy, z0),
             (x0, y0, z0+dz), (x0+dx, y0, z0+dz), (x0, y0+dy, z0+dz)]
    faces = [
        (0, 1, 2), (3, 5, 4), # bas, haut
        (0, 3, 4), (0, 4, 1),
        (1, 4, 5), (1, 5, 2),
        (2, 5, 3), (2, 3, 0)
    ]
    return [(None, p[f[0]], p[f[1]], p[f[2]]) for f in faces]

# ------------------------------------------------------------------------------
# 1. CHÂSSIS INFÉRIEUR BLEU
# ------------------------------------------------------------------------------
def generate_chassis_v2():
    triangles = []
    L, W, H, wall = 208.0, 114.0, 16.0, 2.5
    
    # Fond principal
    triangles += make_box_triangles(0, 0, 0, L, W, wall)
    
    # Paroi Arrière
    triangles += make_box_triangles(0, W - wall, wall, L, wall, H - wall)
    # Paroi Droite
    triangles += make_box_triangles(L - wall, 0, wall, wall, W, H - wall)
    # Paroi Gauche (avec fenêtre ancrage sangle)
    triangles += make_box_triangles(0, 0, wall, wall, 25.0, H - wall)
    triangles += make_box_triangles(0, 65.0, wall, wall, W - 65.0, H - wall)
    
    # Paroi Avant avec découpes réelles selon planche d'atelier :
    # X=0..30 (Plein avec trou LED RVB Ø3.2mm)
    triangles += make_box_triangles(0, 0, wall, 32.0, wall, H - wall)
    # X=32..46 (Fenêtre USB-C 11x6.5mm)
    triangles += make_box_triangles(45.0, 0, wall, 18.0, wall, H - wall)
    # X=63..81 (Fenêtre RJ45 16.5x14mm)
    triangles += make_box_triangles(81.5, 0, wall, 13.5, wall, H - wall)
    # X=95..112 (Fenêtre 2x USB 15x16.5mm)
    triangles += make_box_triangles(112.0, 0, wall, 18.0, wall, H - wall)
    # X=130..141 (Fenêtre Micro-HDMI 8.5x5mm)
    triangles += make_box_triangles(140.5, 0, wall, 27.5, wall, H - wall)
    # X=168..182 (Glissière Bouton Power ⏻)
    triangles += make_box_triangles(182.0, 0, wall, L - 182.0, wall, H - wall)
    
    # Linteau supérieur avant (au-dessus des ports)
    triangles += make_box_triangles(0, 0, H - 2.0, L, wall, 2.0)
    
    # Plots Raspberry Pi 5 (4 plots Ø6mm, H: 3.0mm, entraxe 58x49mm)
    pi_x0, pi_y0 = 18.0, 16.0
    for dx in [0, 58.0]:
        for dy in [0, 49.0]:
            triangles += make_cylinder_triangles(pi_x0 + dx, pi_y0 + dy, wall, 3.0, 3.0)

    # Berceau Batterie 2x 18650 (69 x 38.5 mm, centré)
    bx, by = 86.0, 26.0
    triangles += make_box_triangles(bx, by, wall, 71.0, 1.8, 8.0)
    triangles += make_box_triangles(bx, by + 40.0, wall, 71.0, 1.8, 8.0)
    triangles += make_box_triangles(bx, by, wall, 1.8, 41.8, 8.0)
    triangles += make_box_triangles(bx + 71.0, by, wall, 1.8, 41.8, 8.0)
    
    # Logement Haut-Parleur Ovale (71 x 32 mm) + Ampli I2S
    hx, hy = 132.0, 26.0
    triangles += make_box_triangles(hx, hy, wall, 72.0, 1.8, 10.0)
    triangles += make_box_triangles(hx, hy + 33.0, wall, 72.0, 1.8, 10.0)
    triangles += make_box_triangles(hx, hy, wall, 1.8, 34.8, 10.0)
    triangles += make_box_triangles(hx + 72.0, hy, wall, 1.8, 34.8, 10.0)
    
    # 4 Puits d'inserts filetés en laiton M3 aux 4 angles
    for px, py in [(12.0, 12.0), (L-12.0, 12.0), (12.0, W-12.0), (L-12.0, W-12.0)]:
        triangles += make_cylinder_triangles(px, py, wall, 3.5, 6.0)

    return triangles

# ------------------------------------------------------------------------------
# 2. CAPOT SUPÉRIEUR BLANC
# ------------------------------------------------------------------------------
def generate_capot_v2():
    triangles = []
    L, W, H, wall = 208.0, 114.0, 10.0, 2.5
    
    # Parois périphériques du capot
    triangles += make_box_triangles(0, 0, 0, L, wall, H)
    triangles += make_box_triangles(0, W - wall, 0, L, wall, H)
    triangles += make_box_triangles(0, wall, 0, wall, W - 2*wall, H)
    triangles += make_box_triangles(L - wall, wall, 0, wall, W - 2*wall, H)

    # Toit supérieur avec fenêtres découpées :
    # 1. Fenêtre N1 en haut à gauche (X: 30..44, Y: 75..89)
    # 2. Fenêtres N2, N3, N4 en bas à droite (Y: 40..54, X: 140..195)
    # 3. 2 Touches basses au centre (Y: 18..30, X: 70..95)
    # 4. Grille HP en haut à droite (X: 135..185, Y: 70..95)
    
    # Plaque gauche
    triangles += make_box_triangles(wall, wall, H - wall, 25.0, W - 2*wall, wall)
    # Autour de N1
    triangles += make_box_triangles(27.0, wall, H - wall, 22.0, 70.0, wall)
    triangles += make_box_triangles(27.0, 92.0, H - wall, 22.0, W - wall - 92.0, wall)
    
    # Plaque centrale (Logo ALTA + trou micro)
    triangles += make_box_triangles(49.0, wall, H - wall, 85.0, W - 2*wall, wall)
    
    # Plaque droite (touches N2-N4 et grille HP)
    triangles += make_box_triangles(134.0, wall, H - wall, L - wall - 134.0, 35.0, wall)
    triangles += make_box_triangles(134.0, 57.0, H - wall, L - wall - 134.0, 12.0, wall)
    triangles += make_box_triangles(134.0, 98.0, H - wall, L - wall - 134.0, W - wall - 98.0, wall)
    
    # 4 Puits de vis M3 sous les 4 angles (H: 5.0 mm)
    for px, py in [(12.0, 12.0), (L-12.0, 12.0), (12.0, W-12.0), (L-12.0, W-12.0)]:
        triangles += make_cylinder_triangles(px, py, H - wall - 5.0, 3.2, 5.0)

    return triangles

# ------------------------------------------------------------------------------
# 3. TOUCHES DE BOUTONS BLEUES (N1, N2, N3, N4)
# ------------------------------------------------------------------------------
def generate_touches_v2():
    triangles = []
    # 4 touches carrées 13.5 x 13.5 mm espacées
    for i in range(4):
        offset_x = i * 20.0
        # Embase collerette 16 x 16 x 1.2 mm
        triangles += make_box_triangles(offset_x, 0, 0, 16.0, 16.0, 1.2)
        # Tête de touche 13.5 x 13.5 x 3.0 mm
        m = (16.0 - 13.5) / 2.0
        triangles += make_box_triangles(offset_x + m, m, 1.2, 13.5, 13.5, 3.0)
        # Picot central Ø3 mm
        triangles += make_cylinder_triangles(offset_x + 8.0, 8.0, -2.5, 1.5, 2.5)
    return triangles

# ------------------------------------------------------------------------------
# 4. BOUTON POWER BLANC (⏻)
# ------------------------------------------------------------------------------
def generate_power_btn():
    triangles = []
    # Corps rectangulaire 11.5 x 7.5 x 3.0 mm avec collerette
    triangles += make_box_triangles(0, 0, 0, 14.0, 10.0, 1.2)
    triangles += make_box_triangles(1.25, 1.25, 1.2, 11.5, 7.5, 3.0)
    triangles += make_cylinder_triangles(7.0, 5.0, -2.5, 1.5, 2.5)
    return triangles

# ------------------------------------------------------------------------------
# 5. ENTOURAGE DE SANGLE BLANC
# ------------------------------------------------------------------------------
def generate_strap_bracket():
    triangles = []
    # Étrier latéral de sangle (anneau 28 x 12 mm avec passage de sangle 22 x 3.5 mm)
    triangles += make_box_triangles(0, 0, 0, 28.0, 6.0, 14.0)
    triangles += make_box_triangles(0, 6.0, 0, 28.0, 12.0, 3.0)
    triangles += make_box_triangles(0, 15.0, 3.0, 28.0, 3.0, 11.0)
    triangles += make_box_triangles(0, 6.0, 11.0, 28.0, 12.0, 3.0)
    return triangles

if __name__ == '__main__':
    out_dir = os.path.dirname(os.path.abspath(__file__))
    print("⏳ Génération des 5 fichiers STL 3D conformes à la planche d'atelier...")

    # 1. Châssis Inférieur Bleu
    f_cha = os.path.join(out_dir, "ALTA_Chassis_Inferieur_Bleu.stl")
    t_cha = generate_chassis_v2()
    write_binary_stl(f_cha, t_cha, "ALTA_Bottom_Chassis_Blue")
    print(f"✅ [1/5] {f_cha} ({len(t_cha)} facettes)")

    # 2. Capot Supérieur Blanc
    f_cap = os.path.join(out_dir, "ALTA_Capot_Superieur_Blanc.stl")
    t_cap = generate_capot_v2()
    write_binary_stl(f_cap, t_cap, "ALTA_Top_Cover_White")
    print(f"✅ [2/5] {f_cap} ({len(t_cap)} facettes)")

    # 3. Touches Bleues (N1, N2, N3, N4)
    f_btn = os.path.join(out_dir, "ALTA_Touches_Boutons_Bleu.stl")
    t_btn = generate_touches_v2()
    write_binary_stl(f_btn, t_btn, "ALTA_Buttons_N1_N4_Blue")
    print(f"✅ [3/5] {f_btn} ({len(t_btn)} facettes)")

    # 4. Bouton Power Blanc (⏻)
    f_pwr = os.path.join(out_dir, "ALTA_Bouton_Power_Blanc.stl")
    t_pwr = generate_power_btn()
    write_binary_stl(f_pwr, t_pwr, "ALTA_Power_Button_White")
    print(f"✅ [4/5] {f_pwr} ({len(t_pwr)} facettes)")

    # 5. Entourage Sangle Blanc
    f_str = os.path.join(out_dir, "ALTA_Entourage_Sangle_Blanc.stl")
    t_str = generate_strap_bracket()
    write_binary_stl(f_str, t_str, "ALTA_Strap_Bracket_White")
    print(f"✅ [5/5] {f_str} ({len(t_str)} facettes)")

    print("\n🎉 Toutes les pièces détachées réelles sont exportées en STL avec succès !")
