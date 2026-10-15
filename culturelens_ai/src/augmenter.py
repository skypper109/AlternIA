"""Module de Data Augmentation avancée et réaliste pour les monuments du Mali (CultureLens AI).

Optimisé pour les conditions réelles de prise de vue smartphone au Mali :
- Contre-plongée et perspectives architecturales (monuments verticaux vus du sol)
- Ensoleillement sahélien extrême (plein midi, contre-jour, ombres fortes)
- Heure dorée / crépuscule (teintes chaudes ocres et dorées)
- Poussière de l'harmattan / brume sèche sahélienne
- Légère inclinaison et flou de bougé smartphone
- Équilibrage intelligent des classes minoritaires (ex: 1 photo -> 40 variations réalistes)
"""

import os
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

from .config import REFERENCE_DIR


class MonumentDataAugmenter:
    """Générateur d'augmentations d'images haute fidélité pour monuments historiques."""

    def __init__(self, seed: Optional[int] = 42):
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

    # ──────────────────────────────────────────────────────────────────────────
    # 1. TRANSFORMATIONS GÉOMÉTRIQUES & PERSPECTIVES ARCHITECTURALES
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def perspective_warp(img: np.ndarray, intensity: float = 0.15) -> np.ndarray:
        """Simule une prise de vue en contre-plongée (au pied du monument) ou sous un angle oblique."""
        h, w = img.shape[:2]
        dx = int(w * intensity * (random.uniform(0.5, 1.0)))
        dy = int(h * intensity * (random.uniform(0.5, 1.0)))

        mode = random.choice(["bottom_up", "left_tilt", "right_tilt", "top_down"])
        src = np.array([[0, 0], [w, 0], [w, h], [0, h]], dtype=np.float32)

        if mode == "bottom_up":
            # Sommet rétréci, base élargie (vue depuis le sol en regardant vers le haut)
            dst = np.array([[dx, dy], [w - dx, dy], [w, h], [0, h]], dtype=np.float32)
        elif mode == "top_down":
            dst = np.array([[0, 0], [w, 0], [w - dx, h - dy], [dx, h - dy]], dtype=np.float32)
        elif mode == "left_tilt":
            dst = np.array([[0, dy], [w, 0], [w, h], [0, h - dy]], dtype=np.float32)
        else:
            dst = np.array([[0, 0], [w, dy], [w, h - dy], [0, h]], dtype=np.float32)

        matrix = cv2.getPerspectiveTransform(src, dst)
        warped = cv2.warpPerspective(img, matrix, (w, h), borderMode=cv2.BORDER_REFLECT_101)
        return warped

    @staticmethod
    def random_rotation(img: np.ndarray, max_angle: float = 14.0) -> np.ndarray:
        """Légère rotation du smartphone tenu à main levée."""
        angle = random.uniform(-max_angle, max_angle)
        h, w = img.shape[:2]
        center = (w // 2, h // 2)
        rot_mat = cv2.getRotationMatrix2D(center, angle, 1.0)
        return cv2.warpAffine(img, rot_mat, (w, h), borderMode=cv2.BORDER_REFLECT_101)

    @staticmethod
    def random_zoom_crop(img: np.ndarray, zoom_range: Tuple[float, float] = (0.78, 1.18)) -> np.ndarray:
        """Recadrage avec zoom aléatoire sur les détails architecturaux ou plan plus large."""
        h, w = img.shape[:2]
        zoom = random.uniform(*zoom_range)

        if zoom < 1.0:
            # Zoom avant (recadrage)
            crop_h = int(h * zoom)
            crop_w = int(w * zoom)
            start_y = random.randint(0, h - crop_h)
            start_x = random.randint(0, w - crop_w)
            cropped = img[start_y:start_y + crop_h, start_x:start_x + crop_w]
            return cv2.resize(cropped, (w, h), interpolation=cv2.INTER_LINEAR)
        else:
            # Zoom arrière avec remplissage miroir
            pad_h = int((h * zoom - h) / 2)
            pad_w = int((w * zoom - w) / 2)
            padded = cv2.copyMakeBorder(img, pad_h, pad_h, pad_w, pad_w, cv2.BORDER_REFLECT_101)
            return cv2.resize(padded, (w, h), interpolation=cv2.INTER_LINEAR)

    # ──────────────────────────────────────────────────────────────────────────
    # 2. RADIOMÉTRIE & LUMIÈRE SAHÉLIENNE
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def sahel_sunlight(img: np.ndarray) -> np.ndarray:
        """Simule la forte lumière du soleil de Bamako à midi (contraste élevé et éclats)."""
        table = np.array([((i / 255.0) ** 0.82) * 255 for i in np.arange(0, 256)]).astype("uint8")
        bright = cv2.LUT(img, table)
        alpha = random.uniform(1.12, 1.30)
        beta = random.uniform(10, 25)
        adjusted = cv2.convertScaleAbs(bright, alpha=alpha, beta=beta)
        return adjusted

    @staticmethod
    def golden_hour_dusk(img: np.ndarray) -> np.ndarray:
        """Simule la lumière chaude dorée du coucher de soleil sahélien sur les ocres et bancos."""
        b, g, r = cv2.split(img.astype(np.float32))
        r = np.clip(r * random.uniform(1.15, 1.30), 0, 255)
        g = np.clip(g * random.uniform(1.02, 1.12), 0, 255)
        b = np.clip(b * random.uniform(0.72, 0.88), 0, 255)
        merged = cv2.merge([b, g, r]).astype(np.uint8)
        return merged

    @staticmethod
    def harmattan_haze(img: np.ndarray) -> np.ndarray:
        """Simule le voile de poussière de l'harmattan (brume sèche et contraste adouci)."""
        h, w = img.shape[:2]
        dust_overlay = np.full((h, w, 3), (165, 205, 225), dtype=np.uint8)  # Teinte sable BGR
        alpha = random.uniform(0.12, 0.22)
        hazed = cv2.addWeighted(img, 1.0 - alpha, dust_overlay, alpha, 0)
        return hazed

    @staticmethod
    def shadow_overcast(img: np.ndarray) -> np.ndarray:
        """Simule une prise de vue à l'ombre ou temps couvert."""
        table = np.array([((i / 255.0) ** 1.25) * 255 for i in np.arange(0, 256)]).astype("uint8")
        dark = cv2.LUT(img, table)
        return dark

    # ──────────────────────────────────────────────────────────────────────────
    # 3. CAPTEUR SMARTPHONE & ARTEFACTS OPTIQUES
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def motion_blur(img: np.ndarray, size: int = 5) -> np.ndarray:
        """Simule un léger flou de bougé lors du déclenchement caméra."""
        kernel = np.zeros((size, size))
        angle = random.choice([0, 45, 90, 135])
        if angle == 0:
            kernel[int((size - 1) / 2), :] = np.ones(size)
        elif angle == 90:
            kernel[:, int((size - 1) / 2)] = np.ones(size)
        else:
            np.fill_diagonal(kernel, 1)
        kernel = kernel / size
        return cv2.filter2D(img, -1, kernel)

    @staticmethod
    def sensor_noise(img: np.ndarray, std: float = 12.0) -> np.ndarray:
        """Simule le bruit numérique ISO d'un capteur smartphone en basse lumière."""
        noise = np.random.normal(0, std, img.shape).astype(np.float32)
        noisy = np.clip(img.astype(np.float32) + noise, 0, 255).astype(np.uint8)
        return noisy

    # ──────────────────────────────────────────────────────────────────────────
    # 4. COMPOSITION DE TRANSFORMATIONS ALÉATOIRES
    # ──────────────────────────────────────────────────────────────────────────

    def apply_random_pipeline(self, img_bgr: np.ndarray) -> np.ndarray:
        """Applique une combinaison aléatoire mais réaliste de transformations sur l'image."""
        result = img_bgr.copy()

        # 1. Flip horizontal éventuel
        if random.random() < 0.5:
            result = cv2.flip(result, 1)

        # 2. Déformation de perspective (fondamental pour les monuments)
        if random.random() < 0.75:
            result = self.perspective_warp(result, intensity=random.uniform(0.08, 0.18))

        # 3. Rotation légère
        if random.random() < 0.80:
            result = self.random_rotation(result, max_angle=random.uniform(6.0, 14.0))

        # 4. Zoom / Recadrage
        if random.random() < 0.85:
            result = self.random_zoom_crop(result, zoom_range=(0.80, 1.15))

        # 5. Effet d'ambiance lumineuse (1 parmi 4)
        light_choice = random.choice(["sun", "dusk", "haze", "shadow", "none"])
        if light_choice == "sun":
            result = self.sahel_sunlight(result)
        elif light_choice == "dusk":
            result = self.golden_hour_dusk(result)
        elif light_choice == "haze":
            result = self.harmattan_haze(result)
        elif light_choice == "shadow":
            result = self.shadow_overcast(result)

        # 6. Artefacts optiques légers
        if random.random() < 0.25:
            result = self.motion_blur(result, size=random.choice([3, 5]))
        elif random.random() < 0.25:
            result = self.sensor_noise(result, std=random.uniform(6.0, 14.0))

        return result


def augment_monument_dataset(
    reference_dir: Path = REFERENCE_DIR,
    target_count_per_monument: int = 40,
    save_to_disk: bool = True,
    clean_existing: bool = True,
    augmented_dir_name: str = "augmented",
) -> Dict[str, int]:
    """Exécute la data augmentation sur tous les sous-dossiers ayant des photos.

    Pour chaque monument :
    - Nettoie les anciens fichiers générés si clean_existing=True
    - Détecte les images sources déposées par l'utilisateur
    - Génère des variations réalistes jusqu'à atteindre 'target_count_per_monument'
    - Sauvegarde les images augmentées avec des noms explicites
    """
    augmenter = MonumentDataAugmenter()
    valid_exts = {".jpg", ".jpeg", ".png", ".webp", ".avif"}

    stats: Dict[str, int] = {}
    total_generated = 0

    print(f"\n========================================================")
    print(f"  DATA AUGMENTATION HAUTE FIDÉLITÉ (CULTURELENS AI)     ")
    print(f"  Objectif : minimum {target_count_per_monument} photos par monument")
    print(f"========================================================")

    for monument_dir in sorted(reference_dir.iterdir()):
        if not monument_dir.is_dir() or monument_dir.name.startswith("."):
            continue

        if clean_existing:
            for old_aug in monument_dir.glob("aug_*"):
                try:
                    old_aug.unlink()
                except Exception:
                    pass

        # Récupération des images sources brutes (non générées)
        source_images = [
            p for p in monument_dir.iterdir()
            if p.is_file() and p.suffix.lower() in valid_exts and not p.name.startswith("aug_")
        ]

        if not source_images:
            continue

        m_name = monument_dir.name
        num_sources = len(source_images)

        # Nombre de variations nécessaires pour atteindre target_count_per_monument
        needed = max(0, target_count_per_monument - num_sources)
        # Chaque source produira au moins ceil(needed / num_sources) variations
        per_source = max(2, (needed + num_sources - 1) // num_sources) if needed > 0 else 2

        generated_for_m = 0

        # Si save_to_disk, création des fichiers dans le dossier du monument
        for src_path in source_images:
            try:
                # Lecture via OpenCV (gère webp, jpg, png)
                img = cv2.imread(str(src_path))
                if img is None:
                    # Fallback PIL
                    pil = Image.open(src_path).convert("RGB")
                    img = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
            except Exception as e:
                print(f"⚠️ Erreur de lecture pour {src_path.name}: {e}")
                continue

            base_stem = src_path.stem

            for i in range(per_source):
                if generated_for_m >= needed and needed > 0 and generated_for_m >= 15:
                    break

                aug_img = augmenter.apply_random_pipeline(img)
                aug_filename = f"aug_{base_stem}_v{i+1}.jpg"
                out_path = monument_dir / aug_filename

                if save_to_disk:
                    cv2.imwrite(str(out_path), aug_img, [int(cv2.IMWRITE_JPEG_QUALITY), 90])

                generated_for_m += 1
                total_generated += 1

        total_m = num_sources + generated_for_m
        stats[m_name] = total_m
        print(f"  🏛️ {m_name:35} : {num_sources:2d} sources ➔ +{generated_for_m:2d} augmentées = {total_m:2d} images totales")

    print(f"\n✅ Total variations générées avec succès : {total_generated} images augmentées")
    print(f"  • Monuments enrichis : {len(stats)}")
    return stats


if __name__ == "__main__":
    augment_monument_dataset()
