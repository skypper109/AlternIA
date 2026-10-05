"""Chargement et augmentation de données pour l'apprentissage des monuments."""

from pathlib import Path
from typing import List, Tuple, Dict
from PIL import Image
import torch
from torchvision import transforms

from .config import IMAGE_SIZE, REFERENCE_DIR


def get_inference_transform():
    """Transformation standard pour l'évaluation et l'inférence en direct."""
    return transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.CenterCrop(IMAGE_SIZE),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
    ])


def get_training_augmentation_transform():
    """Augmentation de données réaliste simulant les conditions de cadrage smartphone à Bamako:
    - Plein soleil / ombres portées
    - Cadrage sous angle contre-plongée (monuments élevés)
    - Légère variation de focale / zoom
    """
    return transforms.Compose([
        transforms.RandomResizedCrop(IMAGE_SIZE, scale=(0.75, 1.0), ratio=(0.85, 1.15)),
        transforms.RandomHorizontalFlip(p=0.4),
        transforms.RandomRotation(degrees=(-12, 12)),
        transforms.ColorJitter(
            brightness=0.25,
            contrast=0.25,
            saturation=0.20,
            hue=0.05
        ),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
    ])


def load_monument_dataset(dataset_dir: Path = REFERENCE_DIR) -> Dict[str, List[Path]]:
    """Scanne le répertoire des images de référence et retourne la liste des photos par monument."""
    dataset = {}
    valid_exts = {".jpg", ".jpeg", ".png", ".webp"}

    for monument_dir in dataset_dir.iterdir():
        if monument_dir.is_dir() and not monument_dir.name.startswith("."):
            images = [
                p for p in monument_dir.iterdir()
                if p.is_file() and p.suffix.lower() in valid_exts
            ]
            if images:
                dataset[monument_dir.name] = images

    return dataset


def preprocess_image_file(image_path: Path, device: str = "cpu") -> torch.Tensor:
    """Charge et prépare une image quelconque pour l'inférence par le modèle."""
    image = Image.open(image_path).convert("RGB")
    transform = get_inference_transform()
    tensor_img = transform(image)
    assert isinstance(tensor_img, torch.Tensor)
    return tensor_img.unsqueeze(0).to(device)
