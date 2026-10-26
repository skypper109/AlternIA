// ============================================================================
// PROJET : Boîtier Éducatif ALTA - Cyber-Bloc v2 (Raspberry Pi 5)
// CONCEPTION : CAO Paramétrique Haute Précision (Zéro approximation cubique)
// DIMENSIONS HORS-TOUT : 208 mm (L) x 114 mm (l) x 26 mm (H)
// ============================================================================

$fn = 60; // Résolution circulaire lisse pour impression 3D finale

// ----------------------------------------------------------------------------
// SÉLECTEUR D'EXPORTATION STL (Changez la valeur ci-dessous puis F6 -> F7)
// Options : "plateau_complet", "assemblage", "capot", "chassis", 
//           "touches_N", "touche_power", "touches_bas", "sangle", "bumper_droit"
// ----------------------------------------------------------------------------
PIECE_A_EXPORTER = "assemblage"; 

// --- PARAMÈTRES GÉNÉRAUX & COTES RÉELLES ---
L_tot = 208.0;          // Longueur hors-tout (X)
W_tot = 114.0;          // Largeur hors-tout (Y)
H_chassis = 16.0;       // Hauteur cuve châssis inférieur
H_capot = 10.0;         // Hauteur coque supérieure
Ep_paroi = 2.5;         // Épaisseur des parois
Chanfrein_coin = 18.0;  // Chanfrein octogonal des 4 coins à 45°
Rayon_conge = 3.0;      // Rayon de lissage des arêtes verticales
Chanfrein_haut = 3.0;   // Chanfrein périphérique supérieur 45° (3 mm)
Tol = 0.25;             // Jeu fonctionnel d'assemblage (impression FDM)

// Couleurs de prévisualisation (Filaments Blanc & Bleu Roi)
Col_Blanc = [0.96, 0.96, 0.98];
Col_Bleu  = [0.08, 0.30, 0.72];

// ============================================================================
// FONCTIONS UTILITAIRES GÉOMÉTRIQUES (Profils Octogonaux & Congés Lisses)
// ============================================================================

// Génère un profil 2D octogonal centré avec coins chanfreinés à 45° et congés lisses
module profil_octogone_2d(L, W, ch, r_smooth=Rayon_conge) {
    l = L/2 - r_smooth;
    w = W/2 - r_smooth;
    c = ch - r_smooth * 0.414; 
    offset(r = r_smooth) {
        polygon(points=[
            [-l + c, -w],
            [ l - c, -w],
            [ l,     -w + c],
            [ l,      w - c],
            [ l - c,  w],
            [-l + c,  w],
            [-l,      w - c],
            [-l,     -w + c]
        ]);
    }
}

// Génère un volume 3D octogonal avec chanfrein supérieur fluide à 45°
module solide_octogonal_chanfreine(L, W, H, ch_coin, ch_top, r_smooth=Rayon_conge) {
    hull() {
        // Base jusqu'au début du chanfrein
        linear_extrude(height = H - ch_top)
            profil_octogone_2d(L, W, ch_coin, r_smooth);
        // Sommet réduit de ch_top sur tout le périmètre (pente à 45°)
        translate([0, 0, H - 0.01])
            linear_extrude(height = 0.01)
                profil_octogone_2d(L - 2*ch_top, W - 2*ch_top, ch_coin - ch_top*0.5, r_smooth);
    }
}

// Génère un pavé à coins arrondis (pour découpes propres et touches)
module boite_arrondie(dx, dy, dz, r=2.0, center_xy=true) {
    translate([center_xy ? 0 : dx/2, center_xy ? 0 : dy/2, 0])
    linear_extrude(height = dz)
        offset(r = r)
            square([dx - 2*r, dy - 2*r], center=true);
}

// Boîte avec biseau supérieur à 45° (pour le dôme des touches)
module touche_biseautee_3d(dx, dy, dz, biseau=1.0, r=2.0) {
    hull() {
        boite_arrondie(dx, dy, dz - biseau, r);
        translate([0, 0, dz - 0.01])
            boite_arrondie(dx - 2*biseau, dy - 2*biseau, 0.01, max(0.5, r - biseau));
    }
}

// Position des 4 vis d'assemblage M3 dans les angles
function pos_vis_angles() = [
    [-L_tot/2 + 22, -W_tot/2 + 12],
    [ L_tot/2 - 22, -W_tot/2 + 12],
    [ L_tot/2 - 22,  W_tot/2 - 12],
    [-L_tot/2 + 22,  W_tot/2 - 12]
];

// ============================================================================
// 1. MODULE : CAPOT SUPÉRIEUR (Filament Blanc)
// ============================================================================
module capot() {
    color(Col_Blanc)
    difference() {
        union() {
            // Coque extérieure de 10 mm avec chanfrein périphérique fluide de 3 mm à 45°
            solide_octogonal_chanfreine(L_tot, W_tot, H_capot, Chanfrein_coin, Chanfrein_haut);
            
            // Lèvre d'emboîtement inférieure (feuillure) rentrant dans le châssis
            translate([0, 0, -2.0])
                linear_extrude(height = 2.0)
                    difference() {
                        profil_octogone_2d(L_tot - 2*Ep_paroi - 2*Tol, W_tot - 2*Ep_paroi - 2*Tol, Chanfrein_coin - Ep_paroi);
                        profil_octogone_2d(L_tot - 2*Ep_paroi - 4.0, W_tot - 2*Ep_paroi - 4.0, Chanfrein_coin - Ep_paroi - 2.0);
                    }
        }

        // --- ÉVIDEMENT INTÉRIEUR DU CAPOT (Coque creuse ép. 2.5 mm) ---
        translate([0, 0, -2.1])
            solide_octogonal_chanfreine(
                L_tot - 2*Ep_paroi - 4.0, 
                W_tot - 2*Ep_paroi - 4.0, 
                H_capot - Ep_paroi + 2.1, 
                Chanfrein_coin - Ep_paroi - 2.0, 
                Chanfrein_haut
            );

        // --- ENCOCHES LATÉRALES POUR PASSAGE DE SANGLE (Gauche) & BUMPER (Droite) ---
        translate([-L_tot/2 - 1, 0, -3])
            boite_arrondie(16, 48, H_capot + 6, r=2);
        translate([L_tot/2 + 1, 0, -3])
            boite_arrondie(12, 54, H_capot + 6, r=2);

        // --- BISEAU AVANT-GAUCHE : 6 OUÏES D'AÉRATION INCLINÉES À 45° TRAVERSANTES ---
        for (i = [0:5]) {
            // Série sur le pan coupé avant-gauche
            translate([-L_tot/2 + 12 + i*3.8, -W_tot/2 + 12 - i*1.5, H_capot - 4])
                rotate([0, 0, 45])
                rotate([45, 0, 0])
                    boite_arrondie(1.8, 12, 12, r=0.6);
            // Seconde série sur le flanc biseauté avant-gauche (comme sur la photo)
            translate([-L_tot/2 + 26 + i*4.2, -W_tot/2 + 4, H_capot - 4])
                rotate([0, 20, -15])
                    boite_arrondie(1.8, 10, 12, r=0.6);
        }

        // --- HAUT À GAUCHE : DÉCOUPE CARRÉE BOUTON ISOLÉ N1 (14.2 x 14.2 mm) + REBORD BISEAUTÉ ---
        pos_N1 = [-L_tot/2 + 36, W_tot/2 - 26];
        translate([pos_N1[0], pos_N1[1], -3]) {
            boite_arrondie(14.2, 14.2, H_capot + 6, r=1.8);
            // Chanfrein d'entrée supérieur autour du bouton N1
            translate([0, 0, H_capot + 1.8])
                hull() {
                    boite_arrondie(14.2, 14.2, 0.1, r=1.8);
                    translate([0, 0, 1.5])
                        boite_arrondie(16.8, 16.8, 0.1, r=2.2);
                }
        }

        // --- AU CENTRE : EMPREINTE LOGO ALTA (0.8 mm) + ORIFICE MICRO MEMS (Ø2.0 mm chanfreiné) ---
        // Orifice Micro MEMS Ø2.0 mm au-dessus du logo
        translate([-5, 22, -1]) {
            cylinder(d=2.0, h=H_capot + 3);
            translate([0, 0, H_capot - 1.2])
                cylinder(d1=2.0, d2=4.2, h=1.3); // Chanfrein acoustique supérieur
        }
        // Gravure Vortex ALTA (3 pales en rotation formant le triangle sphérique)
        translate([0, 6, H_capot - 0.8]) {
            for (a = [0, 120, 240]) {
                rotate([0, 0, a + 15])
                translate([3.5, 0, 0])
                linear_extrude(height = 1.2)
                    difference() {
                        hull() {
                            translate([0, 0]) circle(r=6.5);
                            translate([11, 5]) circle(r=1.2);
                        }
                        translate([2, -5]) circle(r=7.5);
                        translate([-4, 0]) circle(r=4.2);
                    }
            }
        }
        // Lettrage "ALTA" gravé (0.8 mm de profondeur)
        translate([0, -14, H_capot - 0.8])
            linear_extrude(height = 1.2)
                text("ALTA", size = 10.5, font = "Arial:style=Bold", halign = "center", valign = "center", spacing = 1.15);

        // --- HAUT À DROITE : GRILLE ACOUSTIQUE HAUT-PARLEUR (Matrice circulaire de trous Ø2.2 mm) ---
        pos_HP = [L_tot/2 - 48, W_tot/2 - 28];
        translate([pos_HP[0], pos_HP[1], -1]) {
            for (gx = [-5:5]) {
                for (gy = [-5:5]) {
                    px = gx * 3.6;
                    py = gy * 3.6;
                    // Découpe dans un disque de rayon 19 mm pour reproduire la rosace de la photo
                    if (sqrt(px*px + py*py) <= 19.0) {
                        translate([px, py, 0])
                            cylinder(d = 2.2, h = H_capot + 3);
                    }
                }
            }
        }
        // Micro-grille secondaire d'équilibre acoustique en haut à droite
        translate([L_tot/2 - 72, W_tot/2 - 12, -1]) {
            for (gx = [0:4])
                for (gy = [0:1])
                    translate([gx*2.8, gy*2.8, 0])
                        cylinder(d = 1.4, h = H_capot + 3);
        }

        // --- BAS À DROITE (SOUS LA GRILLE) : DÉCROCHÉ EN CREUX + 3 BOUTONS ALIGNÉS N2, N3, N4 ---
        pos_N_row = [L_tot/2 - 48, -W_tot/2 + 24];
        // Cuvette oblongue en creux sur le dessus du capot
        translate([pos_N_row[0], pos_N_row[1], H_capot - 1.8])
            boite_arrondie(56.0, 18.0, 2.5, r=4.0);
        // 3 traversées carrées 14.2 x 14.2 mm pour N2, N3, N4
        for (i = [-1, 0, 1]) {
            translate([pos_N_row[0] + i * 18.0, pos_N_row[1], -3])
                boite_arrondie(14.2, 14.2, H_capot + 6, r=1.8);
        }

        // --- BAS AU CENTRE : 2 OUVERTURES CARRÉES POUR LES 2 TOUCHES INFÉRIEURES ---
        pos_pads = [-18, -W_tot/2 + 22];
        for (i = [0, 1]) {
            translate([pos_pads[0] + i * 18.0, pos_pads[1], -3]) {
                boite_arrondie(14.2, 14.2, H_capot + 6, r=1.8);
                translate([0, 0, H_capot - 1.2])
                    boite_arrondie(15.6, 15.6, 2.0, r=2.2);
            }
        }

        // --- 4 TROUS D'ANGLE POUR VIS M3 FRAISÉES ---
        for (p = pos_vis_angles()) {
            translate([p[0], p[1], -3]) {
                cylinder(d = 3.4, h = H_capot + 6); // Passage M3
                translate([0, 0, H_capot + 0.6])
                    cylinder(d1 = 3.4, d2 = 6.6, h = 2.6); // Fraisure 90° M3
            }
        }
    }
}

// ============================================================================
// 2. MODULE : CHÂSSIS INFÉRIEUR (Filament Bleu Roi)
// ============================================================================
module chassis() {
    color(Col_Bleu)
    difference() {
        union() {
            // Cuve extérieure de 16 mm de hauteur avec coins octogonaux et chanfrein bas de 1.5 mm
            mirror([0, 0, 1])
            translate([0, 0, -H_chassis])
                solide_octogonal_chanfreine(L_tot, W_tot, H_chassis, Chanfrein_coin, 1.5);
                
            // Jupe/Rebord esthétique latéral en relief sur la façade avant (style Cyber-Bloc)
            translate([22, -W_tot/2 + 2, 0])
                boite_arrondie(132, 6, H_chassis, r=2.0);
        }

        // --- CUVE INTÉRIEURE ÉVIDÉE (Parois de 2.5 mm, fond de 2.5 mm) ---
        translate([0, 0, Ep_paroi])
            linear_extrude(height = H_chassis + 1)
                profil_octogone_2d(L_tot - 2*Ep_paroi, W_tot - 2*Ep_paroi, Chanfrein_coin - Ep_paroi);

        // --- FLANC AVANT : BAIE DE CONNECTIQUE PRÉCISE (RPi 5 + LED + Power) ---
        // Encoche esthétique de façade encadrant les ports
        translate([22, -W_tot/2 - 1, 2.0])
            boite_arrondie(126, 4.0, H_chassis - 4.0, r=2.0);

        // 1. Orifice pour LED RVB d'état (Ø3.2 mm) + petit chanfrein
        translate([-32, -W_tot/2 + 4, 7.5])
            rotate([90, 0, 0]) {
                cylinder(d = 3.2, h = 10);
                translate([0, 0, 3.5]) cylinder(d1 = 3.2, d2 = 5.5, h = 2.5);
            }

        // 2. Fenêtre USB-C alimentation (11 x 6.5 mm) avec bords arrondis
        translate([-16, -W_tot/2, 7.5])
            rotate([90, 0, 0])
                boite_arrondie(11.0, 6.5, 12, r=2.0);

        // 3. Fenêtre RJ45 Ethernet (16.5 x 14 mm)
        translate([8, -W_tot/2, 9.5])
            rotate([90, 0, 0])
                boite_arrondie(16.5, 14.0, 12, r=1.0);

        // 4. Fenêtre double port USB (15 x 16.5 mm)
        translate([32, -W_tot/2, 10.2])
            rotate([90, 0, 0])
                boite_arrondie(15.0, 16.5, 12, r=1.0);

        // 5. Fenêtre Micro-HDMI (8.5 x 5 mm)
        translate([52, -W_tot/2, 7.2])
            rotate([90, 0, 0])
                boite_arrondie(8.5, 5.0, 12, r=1.0);

        // 6. Glissière / Fenêtre pour le bouton d'allumage blanc Power (⏻) + LED témoin
        translate([68, -W_tot/2, 7.5])
            rotate([90, 0, 0])
                cylinder(d = 2.8, h = 12);
        translate([76, -W_tot/2, 7.5])
            rotate([90, 0, 0])
                boite_arrondie(7.5, 5.5, 12, r=1.2);

        // --- FLANC GAUCHE : DÉCROCHÉ D'ANCRAGE DE LA SANGLE TEXTILE ---
        translate([-L_tot/2, 0, Ep_paroi + 1.0])
            boite_arrondie(14, 46, H_chassis, r=2.0);
        // Mortaises de verrouillage de l'étrier de sangle
        for (sy = [-18, 18])
            translate([-L_tot/2 + 6, sy, -1])
                boite_arrondie(6.5, 6.5, H_chassis + 2, r=1.0);

        // --- FLANC DROIT : LOGEMENT DU BUMPER DE PROTECTION BLANC ---
        translate([L_tot/2, 0, Ep_paroi + 1.0])
            boite_arrondie(10, 52, H_chassis, r=2.0);
    }

    // --- AMÉNAGEMENTS INTÉRIEURS DU CHÂSSIS (Ajoutés dans la cuve) ---
    color(Col_Bleu) {
        // 1. ZONE GAUCHE : 4 plots surélevés de 3 mm pour visser le Raspberry Pi 5 (Entraxe 58 x 49 mm)
        pos_rpi_origine = [-58, -32];
        for (dx = [0, 58]) {
            for (dy = [0, 49]) {
                translate([pos_rpi_origine[0] + dx, pos_rpi_origine[1] + dy, Ep_paroi]) {
                    difference() {
                        cylinder(d1 = 8.0, d2 = 6.5, h = 3.0);
                        translate([0, 0, -0.5])
                            cylinder(d = 2.5, h = 4.0); // Trou de vissage M2.5 RPi 5
                    }
                }
            }
        }

        // 2. ZONE CENTRALE : Berceau de maintien pour le pack batterie 2x 18650 (69 x 38.5 mm, H = 8 mm)
        translate([0, 8, Ep_paroi]) {
            difference() {
                boite_arrondie(38.5 + 4.0, 69.0 + 4.0, 8.0, r=3.0);
                translate([0, 0, -0.5])
                    boite_arrondie(38.5 + Tol, 69.0 + Tol, 9.0, r=1.5);
                // Dégagements latéraux pour passage des fils et sangle batterie
                translate([0, 0, 3.0])
                    boite_arrondie(48.0, 28.0, 6.0, r=2.0);
            }
        }

        // 3. ZONE DROITE : Berceau pour le module haut-parleur rectangulaire noir (70 x 30 mm) + Ampli I2S
        translate([L_tot/2 - 48, 12, Ep_paroi]) {
            difference() {
                boite_arrondie(34.0, 74.0, 6.0, r=2.5);
                translate([0, 0, -0.5])
                    boite_arrondie(30.2, 70.2, 7.0, r=1.5);
                // Ouverture passage câbles HP
                translate([-18, 0, 1.5])
                    boite_arrondie(12, 20, 6.0, r=1.0);
            }
        }
        // Support pour la carte PCB Ampli I2S & Carte des boutons (sous la rangée N2-N4)
        translate([L_tot/2 - 48, -W_tot/2 + 24, Ep_paroi]) {
            for (bx = [-22, 22]) {
                translate([bx, 0, 0])
                difference() {
                    cylinder(d = 6.0, h = 4.5);
                    cylinder(d = 2.2, h = 5.0);
                }
            }
        }

        // 4. QUATRE PUITS D'ANGLE POUR INSERTS FILETÉS LAITON M3 (Ø4.0 mm, profondeur 6 mm)
        for (p = pos_vis_angles()) {
            translate([p[0], p[1], Ep_paroi]) {
                difference() {
                    cylinder(d = 8.5, h = H_chassis - Ep_paroi);
                    // Logement insert laiton M3 thermofixé (Ø4.0 mm sur 6 mm de profondeur)
                    translate([0, 0, H_chassis - Ep_paroi - 6.0])
                        cylinder(d = 4.0, h = 6.5);
                    // Dégagement de vis M3 en dessous
                    translate([0, 0, -0.5])
                        cylinder(d = 3.2, h = H_chassis);
                }
            }
        }
    }
}

// ============================================================================
// 3. MODULE : TOUCHES & BOUTONS (N1..N4, Power ⏻, 2 Touches inférieures)
// ============================================================================

// Touche unitaire N1, N2, N3 ou N4 avec collerette 16x16, corps 13.5x13.5, picot Ø3 et gravure
module touche_N(label="N1") {
    color(Col_Bleu)
    difference() {
        union() {
            // Collerette de retenue anti-arrachement (16 x 16 x 1.5 mm)
            boite_arrondie(16.0, 16.0, 1.5, r=2.2);
            // Corps de touche carré (13.5 x 13.5 mm) émergeant du capot avec dôme biseauté
            translate([0, 0, 1.5])
                touche_biseautee_3d(13.5, 13.5, 4.5, biseau=0.8, r=1.6);
            // Picot actuateur inférieur (Ø3.0 mm) appuyant sur le switch tactile
            translate([0, 0, -2.5])
                cylinder(d = 3.0, h = 2.5);
        }
        // Gravure nette sur le dessus de la touche (N1, N2, N3, N4)
        translate([0, 0, 5.3])
            linear_extrude(height = 1.0)
                text(label, size = 5.2, font = "Arial:style=Bold", halign = "center", valign = "center");
    }
}

// Touche Power (⏻) en filament Blanc
module touche_power() {
    color(Col_Blanc)
    difference() {
        union() {
            // Embase de retenue interne
            boite_arrondie(12.0, 12.0, 1.5, r=2.0);
            // Corps du bouton
            translate([0, 0, 1.5])
                touche_biseautee_3d(9.5, 9.5, 4.0, biseau=0.6, r=1.5);
        }
        // Gravure du symbole universel Power (Anneau ouvert + barre verticale)
        translate([0, 0, 4.8]) {
            linear_extrude(height = 1.0) {
                difference() {
                    circle(d = 5.2);
                    circle(d = 3.6);
                    translate([0, 2.0]) square([2.2, 3.0], center=true);
                }
                translate([0, 1.4]) square([0.9, 3.2], center=true);
            }
        }
    }
}

// Les 2 touches/pads inférieurs (Bleu Roi, sans gravure texte, dôme lisse)
module touche_inferieure() {
    color(Col_Bleu)
    union() {
        boite_arrondie(16.0, 16.0, 1.5, r=2.2);
        translate([0, 0, 1.5])
            touche_biseautee_3d(13.5, 13.5, 4.2, biseau=0.8, r=1.6);
        translate([0, 0, -2.5])
            cylinder(d = 3.0, h = 2.5);
    }
}

// Ensemble complet des touches disposées pour l'export
module touches_toutes() {
    // N1 à N4
    translate([0, 0, 2.5])   touche_N("N1");
    translate([20, 0, 2.5])  touche_N("N2");
    translate([40, 0, 2.5])  touche_N("N3");
    translate([60, 0, 2.5])  touche_N("N4");
    // 2 touches inférieures
    translate([0, -22, 2.5])  touche_inferieure();
    translate([20, -22, 2.5]) touche_inferieure();
    // Touche Power blanche
    translate([45, -22, 0])   touche_power();
}

// ============================================================================
// 4. MODULE : ACCESSOIRES DE SANGLE & ANGLE DE PROTECTION (Blanc & Bleu)
// ============================================================================

// Étrier latéral gauche et boucle de guidage de la sangle (Filament Blanc)
module sangle() {
    color(Col_Blanc) {
        // 1. Étrier de sangle s'insérant dans le flanc gauche du boîtier
        difference() {
            union() {
                boite_arrondie(14.0, 45.0, 12.0, r=3.0);
                // Pattes d'ancrage rentrant dans le châssis
                for (sy = [-18, 18])
                    translate([6.0, sy, 0])
                        boite_arrondie(8.0, 6.0, 12.0, r=1.5);
            }
            // Fente oblongue pour passage de la sangle textile bleue (largeur 25 mm, ép. 3.5 mm)
            translate([-2.0, 0, 0])
                boite_arrondie(5.0, 26.0, 16.0, r=1.8);
            // 2 trous de vissage M3 de sécurité
            for (sy = [-14, 14])
                translate([0, sy, 6.0])
                    rotate([0, 90, 0])
                        cylinder(d = 3.2, h = 20, center = true);
        }
    }
}

// Bumper / Angle de protection droit (Filament Blanc)
module bumper_droit() {
    color(Col_Blanc) {
        difference() {
            union() {
                boite_arrondie(10.0, 50.0, 14.0, r=3.0);
                // Ergots d'encliquetage dans le châssis
                for (sy = [-16, 16])
                    translate([-4.0, sy, 0])
                        boite_arrondie(6.0, 6.0, 10.0, r=1.5);
            }
            // Allègement esthétique / rainures de style
            for (i = [-1, 0, 1])
                translate([2.0, i * 12.0, 0])
                    boite_arrondie(4.0, 3.0, 18.0, r=1.0);
        }
    }
}

// Patins de préhension antidérapants (Grips latéraux bleus)
module grips_lateraux() {
    color(Col_Bleu) {
        difference() {
            boite_arrondie(16.0, 36.0, 2.5, r=2.0);
            // Stries diagonales à 45°
            for (i = [-3:3]) {
                translate([0, i * 5.0, 1.5])
                    rotate([0, 0, 45])
                        cube([24.0, 1.5, 3.0], center = true);
            }
        }
    }
}

// ============================================================================
// GESTIONNAIRE D'EXPORTATION ET D'AFFICHAGE
// ============================================================================

if (PIECE_A_EXPORTER == "capot") {
    // Exporter le capot blanc seul (prêt pour plateau 1)
    capot();
} 
else if (PIECE_A_EXPORTER == "chassis") {
    // Exporter le châssis bleu seul (prêt pour plateau 2)
    chassis();
} 
else if (PIECE_A_EXPORTER == "touches_N") {
    // Exporter les 4 touches N1, N2, N3, N4
    touches_toutes();
} 
else if (PIECE_A_EXPORTER == "touche_power") {
    touche_power();
} 
else if (PIECE_A_EXPORTER == "sangle") {
    sangle();
} 
else if (PIECE_A_EXPORTER == "bumper_droit") {
    bumper_droit();
} 
else if (PIECE_A_EXPORTER == "assemblage") {
    // Vue 3D assemblée fermée
    chassis();
    translate([0, 0, H_chassis])
        capot();
    translate([-L_tot/2 + 36, W_tot/2 - 26, H_chassis + H_capot - 3.5])
        touche_N("N1");
    for (i = [-1, 0, 1]) {
        translate([L_tot/2 - 48 + i * 18.0, -W_tot/2 + 24, H_chassis + H_capot - 3.5])
            touche_N(i == -1 ? "N2" : (i == 0 ? "N3" : "N4"));
    }
    translate([-18, -W_tot/2 + 22, H_chassis + H_capot - 3.5])
        touche_inferieure();
    translate([0, -W_tot/2 + 22, H_chassis + H_capot - 3.5])
        touche_inferieure();
    translate([76, -W_tot/2 - 2, 7.5])
        rotate([90, 0, 0])
            touche_power();
    translate([-L_tot/2 - 4, 0, H_chassis/2])
        sangle();
    translate([L_tot/2 + 4, 0, H_chassis/2])
        bumper_droit();
} 
else { // "plateau_complet" (comme sur la photo de l'atelier)
    // Vue éclatée à plat de toutes les pièces séparées prêtes à l'inspection
    translate([0, 0, 0]) chassis();
    translate([0, W_tot + 25, 0]) capot();
    translate([-L_tot/2 - 35, W_tot + 25, 0]) sangle();
    translate([L_tot/2 + 35, W_tot + 25, 0]) bumper_droit();
    translate([L_tot/2 + 35, 0, 0]) touches_toutes();
    translate([-L_tot/2 - 35, 0, 0]) grips_lateraux();
}
