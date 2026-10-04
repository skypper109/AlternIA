"""Moteur d'apprentissage et de construction de l'index d'embeddings des monuments."""

import json
from pathlib import Path
from typing import Dict, List, Tuple
from PIL import Image
import torch
import torch.nn.functional as F

from .config import (
    REFERENCE_DIR,
    MODEL_WEIGHTS_PATH,
    INDEX_PATH,
    LABELS_PATH,
    MODELS_DIR,
    BAMAKO_MONUMENTS,
    EMBEDDING_DIM,
)
from .augmenter import augment_monument_dataset
from .dataset_loader import load_monument_dataset, get_inference_transform
from .model import build_feature_extractor, CultureLensVisionBackbone


def train_and_index_monuments(
    num_augmentations: int = 40,
    device: str = "cpu",
    dataset_dir: Path = REFERENCE_DIR,
    run_disk_augmentation: bool = True,
) -> Dict:
    """Entraîne le modèle et génère l'index vectoriel d'embeddings pour chaque monument.

    Étapes :
    1. Génère des variations réalistes par monument (data augmentation architecturale & sahélinne)
    2. Charge toutes les images des monuments pour lesquels des données existent
    3. Extrait les embeddings 576-D via le backbone neuronal MobileNetV3
    4. Calcule le centroïde prototype normalisé et enregistre les exemplars multi-angles
    5. Sauvegarde le modèle et l'index de recherche pour inférence rapide
    """
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Étape d'augmentation réaliste basée sur les noms de dossiers
    if run_disk_augmentation:
        augment_monument_dataset(
            reference_dir=dataset_dir,
            target_count_per_monument=num_augmentations,
            save_to_disk=True,
        )

    dataset = load_monument_dataset(dataset_dir)

    if not dataset:
        raise ValueError(
            f"Aucune image trouvée dans {dataset_dir} ! "
            f"Veuillez déposer des photos dans les sous-dossiers par monument."
        )

    print(f"\n========================================================")
    print(f"  INDEXATION DU MODÈLE CULTURELENS (VISION EDGE AI)     ")
    print(f"  Basé strictement sur les monuments avec photos        ")
    print(f"========================================================")
    print(f"Monuments sélectionnés dans le dataset : {len(dataset)}")
    for m_id, imgs in dataset.items():
        nom = BAMAKO_MONUMENTS.get(m_id, {}).get("name", m_id)
        ville = BAMAKO_MONUMENTS.get(m_id, {}).get("ville", "Mali")
        print(f"  • {nom:35} ({ville}) : {len(imgs):2d} images (sources + augmentées)")

    # Initialisation du backbone
    model = build_feature_extractor(device=device)
    inf_transform = get_inference_transform()

    monument_prototypes = {}
    all_embeddings_list = []
    all_labels_list = []
    class_to_id = {}
    id_to_class = {}

    idx = 0
    for m_id in sorted(dataset.keys()):
        class_to_id[m_id] = idx
        id_to_class[idx] = m_id
        idx += 1

    total_samples = 0

    with torch.no_grad():
        for m_id, img_paths in dataset.items():
            monument_embeddings = []
            class_idx = class_to_id[m_id]

            for img_path in img_paths:
                try:
                    pil_img = Image.open(img_path).convert("RGB")
                except Exception as e:
                    print(f"⚠️ Erreur lors du chargement de {img_path}: {e}")
                    continue

                raw_tensor = inf_transform(pil_img).unsqueeze(0).to(device)
                raw_emb = model(raw_tensor)  # [1, 576]
                monument_embeddings.append(raw_emb)
                all_embeddings_list.append(raw_emb)
                all_labels_list.append(class_idx)
                total_samples += 1

            if monument_embeddings:
                # Concaténation et calcul du centroïde de classe normalisé L2
                stacked = torch.cat(monument_embeddings, dim=0)  # [N, 576]
                centroid = torch.mean(stacked, dim=0, keepdim=True)
                centroid = F.normalize(centroid, p=2, dim=1)
                monument_prototypes[m_id] = centroid

    # Création du tenseur global de centroïdes [num_classes, 576]
    num_classes = len(class_to_id)
    prototype_matrix = torch.zeros((num_classes, EMBEDDING_DIM), device=device)
    for m_id, c_idx in class_to_id.items():
        prototype_matrix[c_idx] = monument_prototypes[m_id].squeeze(0)

    # Matrice de tous les exemplars individuels pour k-NN haute précision
    if all_embeddings_list:
        exemplars_matrix = torch.cat(all_embeddings_list, dim=0).cpu()  # [total_samples, 576]
        exemplars_labels = torch.tensor(all_labels_list, dtype=torch.long)
    else:
        exemplars_matrix = prototype_matrix.cpu()
        exemplars_labels = torch.arange(num_classes)

    # Sauvegarde des fichiers de production
    torch.save(model.state_dict(), MODEL_WEIGHTS_PATH)

    index_data = {
        "prototypes": prototype_matrix.cpu(),
        "exemplar_embeddings": exemplars_matrix,
        "exemplar_labels": exemplars_labels,
        "class_to_id": class_to_id,
        "id_to_class": id_to_class,
        "num_classes": num_classes,
        "embedding_dim": EMBEDDING_DIM,
    }
    torch.save(index_data, INDEX_PATH)

    # Fichier JSON enrichi pour métadonnées lisibles
    labels_meta = {}
    for m_id, c_idx in class_to_id.items():
        meta = BAMAKO_MONUMENTS.get(m_id, {
            "name": m_id.replace("monument_", "").replace("_", " ").title(),
            "ville": "Mali",
            "coords": (12.6392, -8.0029),
            "visual_features": ["Édifice historique"],
            "category": "Patrimoine",
        })
        labels_meta[m_id] = {
            "index": c_idx,
            "name": meta["name"],
            "ville": meta["ville"],
            "coords": meta["coords"],
            "category": meta.get("category", "Patrimoine"),
            "visual_features": meta.get("visual_features", []),
        }

    with open(LABELS_PATH, "w", encoding="utf-8") as f:
        json.dump(labels_meta, f, ensure_ascii=False, indent=2)

    print(f"\n✅ ENTRAÎNEMENT & INDEXATION TERMINÉS AVEC SUCCÈS !")
    print(f"  • Monuments indexés : {num_classes} ({', '.join(sorted(dataset.keys()))})")
    print(f"  • Échantillons analysés : {total_samples}")
    print(f"  • Poids du modèle : {MODEL_WEIGHTS_PATH}")
    print(f"  • Index vectoriel : {INDEX_PATH}")
    print(f"  • Métadonnées : {LABELS_PATH}")

    return {
        "status": "success",
        "num_monuments": num_classes,
        "monuments": list(dataset.keys()),
        "total_samples": total_samples,
        "index_path": str(INDEX_PATH),
    }
