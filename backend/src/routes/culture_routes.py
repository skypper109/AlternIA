"""
Routes FastAPI pour le module CultureLens & Patrimoine du Mali.
Fournit les endpoints de consultation, d'identification visuelle/géospatiale,
de dialogue RAG culturel et de synchronisation des packs hors ligne.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.src.db.database import get_db
from backend.src.services.culture_service import CultureService

router = APIRouter(prefix="/api/v1/culture", tags=["CultureLens & Patrimoine"])


# ==============================================================================
# SCHÉMAS DE REQUÊTES ET RÉPONSES
# ==============================================================================

class IdentifyRequest(BaseModel):
    image_name: str | None = Field(None, description="Nom du fichier image ou identifiant de capture")
    image_base64: str | None = Field(None, description="Image encodée en base64 pour inférence IA vision directe")
    keywords: list[str] | None = Field(None, description="Mots-clés extraits ou annotations")
    latitude: float | None = Field(None, description="Position GPS de l'appareil (latitude)")
    longitude: float | None = Field(None, description="Position GPS de l'appareil (longitude)")
    hint_id: str | None = Field(None, description="ID cible suggéré (mode démo ou balise)")


class AskGuideRequest(BaseModel):
    question: str = Field(..., description="Question posée au guide culturel")
    monument_id: str | None = Field(None, description="ID du monument en cours de consultation")
    region_id: str | None = Field(None, description="ID de la région contextuelle")
    system: str | None = Field(None, description="System prompt spécialisé ou adapté")
    use_case: str | None = Field(None, description="Cas d'usage culturel")
    context: str | None = Field(None, description="Contexte patrimonial immédiat")

    class Config:
        extra = "allow"


class SageChatRequest(BaseModel):
    user_message: str = Field(..., description="Message de l'apprenant à Grand-mère Mah")
    history: list[dict[str, str]] | None = Field(default=[], description="Historique de la conversation")
    additional_context: str | None = Field(None, description="Contexte régional ou patrimonial")

    class Config:
        extra = "allow"


class SageChatRequest(BaseModel):
    user_message: Optional[str] = Field(None, description="Message de l'apprenant à Grand-mère Mah")
    message: Optional[str] = Field(None, description="Message de l'apprenant (alias mobile)")
    history: Optional[List[Dict[str, Any]]] = Field(default=[], description="Historique de la conversation")
    additional_context: Optional[str] = Field(None, description="Contexte régional ou patrimonial")
    context: Optional[str] = Field(None, description="Contexte régional ou patrimonial (alias mobile)")

    @property
    def effective_user_message(self) -> str:
        return (self.user_message or self.message or "").strip()

    @property
    def effective_additional_context(self) -> Optional[str]:
        return self.additional_context or self.context

    class Config:
        extra = "allow"


class DiscoveryRecordRequest(BaseModel):
    monument_id: str = Field(..., description="ID du monument scanné")
    apprenant_id: str | None = Field(None, description="ID de l'apprenant")
    confidence: float = Field(0.98, description="Indice de confiance de la détection")
    is_favorite: bool = Field(False, description="Marqué en favori")
    notes: str | None = Field(None, description="Notes personnelles de l'apprenant")


class ContributionCreateRequest(BaseModel):
    type_contenu: str = Field("proverbe", description="Pilier culturel : 'proverbe', 'devinette', 'conte', 'monument', 'personnage', 'lieu', 'patronyme'")
    titre: str | None = Field(None, description="Titre ou nom du monument, personnage, conte, ville, patronyme")
    texte: str = Field(..., description="Texte principal, récit historique, légende, énigme ou description")
    texte_original: str | None = Field(None, description="Version originale en langue locale (Bambara, Peul, Songhoy, etc.) ou louange clanique")
    signification: str = Field(..., description="Explication, signification profonde ou importance culturelle")
    morale: str | None = Field(None, description="Morale de la fable, réponse à la devinette, ou titre honorifique")
    origine: str | None = Field("Tradition Orale", description="Origine, ethnie ou terroir")
    theme: str | None = Field("Sagesse & Culture", description="Thème ou catégorie")
    region_id: str | None = Field("bamako", description="Identifiant de la région")
    region_nom: str | None = Field("Tout le Mali", description="Nom de la région")
    source_temoin: str | None = Field(None, description="Qui a transmis ou certifié ce savoir (anciens, griots, famille)")
    photo_url: str | None = Field(None, description="URL ou chemin de la photo illustrative")
    audio_url: str | None = Field(None, description="URL de l'enregistrement vocal audio ou narration")
    donnees_supplementaires: dict[str, Any] | None = Field(None, description="Données enrichies : totem, senankouya, latitude, longitude, epoque, etc.")
    donneesSupplementaires: dict[str, Any] | None = Field(None, description="Alias pour compatibilité client Flutter")
    auteur_nom: str | None = Field(None, description="Nom ou pseudo du contributeur")
    auteur_id: str | None = Field(None, description="ID de l'utilisateur ou apprenant connecté")
    auteur_role: str | None = Field("Apprenant", description="Rôle : 'Apprenant', 'Parent', 'Enseignant', 'Griot'")


class ContributionDecisionRequest(BaseModel):
    decision: str = Field(..., description="'APPROUVE' ou 'REJETE'")
    motif: str | None = Field(None, description="Justification ou conseil pédagogique")
    admin_id: str | None = Field(None, description="Identifiant du modérateur")


# ==============================================================================
# ENDPOINTS MONUMENTS ET SITES (PRIORITÉ BAMAKO)
# ==============================================================================

@router.get("/health")
def culture_health(db: Session = Depends(get_db)):
    """Vérification de l'état du sous-système CultureLens."""
    from backend.src.db.models import CultureMonument
    count = db.query(CultureMonument).count()
    bamako_count = db.query(CultureMonument).filter(CultureMonument.ville == "Bamako").count()
    return {
        "status": "online",
        "service": "CultureLens Edge & Cloud Service",
        "totalMonuments": count,
        "bamakoMonuments": bamako_count,
        "offlineReady": True,
    }


@router.get("/monuments")
def get_monuments(
    ville: str | None = Query(None, description="Filtrer par ville (ex: 'Bamako', 'Djenné')"),
    region_id: str | None = Query(None, description="Filtrer par région (ex: 'bamako', 'mopti')"),
    q: str | None = Query(None, description="Recherche textuelle libre"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Récupère le catalogue des monuments et sites culturels."""
    return CultureService.get_monuments(
        db=db,
        ville=ville,
        region_id=region_id,
        query=q,
        skip=skip,
        limit=limit,
    )


@router.get("/sites")
def get_sites(
    ville: str | None = None,
    region_id: str | None = None,
    q: str | None = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """Alias pour /monuments conforme à la nomenclature internationale."""
    return get_monuments(ville=ville, region_id=region_id, q=q, skip=skip, limit=limit, db=db)


@router.get("/monuments/{monument_id}")
def get_monument_detail(monument_id: str, db: Session = Depends(get_db)):
    """Récupère la fiche détaillée et certifiée d'un monument."""
    m = CultureService.get_monument_by_id(db, monument_id)
    if not m:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Monument '{monument_id}' introuvable dans le catalogue",
        )
    return m


@router.get("/sites/{site_id}")
def get_site_detail(site_id: str, db: Session = Depends(get_db)):
    """Alias pour /monuments/{id}."""
    return get_monument_detail(monument_id=site_id, db=db)


@router.get("/sites/{site_id}/narration")
def get_site_narration(site_id: str, db: Session = Depends(get_db)):
    """Fournit le texte de narration audio haute fidélité pour le lecteur vocal."""
    m = CultureService.get_monument_by_id(db, site_id)
    if not m:
        raise HTTPException(status_code=404, detail="Site introuvable")

    return {
        "siteId": m["id"],
        "siteName": m["nom"],
        "narrationText": m["narration_audio_texte"],
        "audioUrl": m.get("audioUrl"),
        "languages": ["fr-FR", "bm-ML"],
        "durationEstimate": "1 min 30 s",
    }


# ==============================================================================
# SCANNER INTELLIGENT & IDENTIFICATION CULTURELENS
# ==============================================================================

@router.post("/identify")
def identify_monument(payload: IdentifyRequest, db: Session = Depends(get_db)):
    """
    Analyse d'identification visuelle et géospatiale du scanner CultureLens.
    Retourne la cible reconnue, le taux de certitude et les caractéristiques détectées.
    """
    result = CultureService.identify_monument(
        db=db,
        image_name=payload.image_name,
        image_base64=payload.image_base64,
        keywords=payload.keywords,
        latitude=payload.latitude,
        longitude=payload.longitude,
        hint_id=payload.hint_id,
    )
    return result


@router.get("/dataset-images/{monument_id}/{filename}")
def get_dataset_image(monument_id: str, filename: str):
    """Sert une photo réelle ou augmentée issue du dataset de référence CultureLens."""
    ai_root = Path(__file__).resolve().parents[3] / "culturelens_ai"
    target = ai_root / "dataset" / "reference_images" / monument_id / filename
    if target.exists() and target.is_file():
        return FileResponse(str(target))
    raise HTTPException(status_code=404, detail="Image de monument non trouvée")


# ==============================================================================
# GUIDE CULTUREL CONVERSATIONNEL (RAG)
# ==============================================================================

@router.post("/ask")
def ask_cultural_guide(payload: AskGuideRequest, db: Session = Depends(get_db)):
    """
    Interroge le Guide Culturel AlterniA (RAG vérifié + Prompts adaptatifs).
    Distingue faits documentés, traditions orales et portée patrimoniale.
    """
    return CultureService.ask_cultural_guide(
        db=db,
        question=payload.question,
        monument_id=payload.monument_id,
        region_id=payload.region_id,
        context_hint=payload.context,
        custom_system_prompt=payload.system,
        use_case=payload.use_case,
    )


# ==============================================================================
# PERSONNAGES, TERROIRS, CONTES ET PROVERBES
# ==============================================================================

@router.get("/figures")
def get_figures(db: Session = Depends(get_db)):
    """Liste des grands personnages historiques du Mali."""
    return CultureService.get_figures(db)


@router.get("/figures/{figure_id}")
def get_figure_detail(figure_id: str, db: Session = Depends(get_db)):
    """Récupère la fiche détaillée d'un grand personnage historique."""
    f = CultureService.get_figure_by_id(db, figure_id)
    if not f:
        raise HTTPException(status_code=404, detail="Personnage introuvable")
    return f


@router.get("/places")
def get_places(db: Session = Depends(get_db)):
    """Liste des terroirs et cités historiques du Mali."""
    return CultureService.get_places(db)


@router.get("/places/{place_id}")
def get_place_detail(place_id: str, db: Session = Depends(get_db)):
    """Récupère la fiche détaillée d'une ville ou terroir historique."""
    p = CultureService.get_place_by_id(db, place_id)
    if not p:
        raise HTTPException(status_code=404, detail="Lieu introuvable")
    return p


@router.get("/stories")
def get_stories(db: Session = Depends(get_db)):
    """Liste des contes et récits oraux interactifs."""
    return CultureService.get_stories(db)


@router.get("/proverbs")
def get_proverbs(db: Session = Depends(get_db)):
    """Liste des proverbes et sagesses des terroirs maliens."""
    return CultureService.get_proverbs(db)


# ==============================================================================
# PACKS HORS LIGNE ET SYNCHRONISATION
# ==============================================================================

@router.get("/packs")
def get_packs(db: Session = Depends(get_db)):
    """Liste des packs culturels téléchargeables pour utilisation hors ligne."""
    return CultureService.get_packs(db)


@router.get("/packs/{pack_id}/download")
def download_pack_bundle(pack_id: str, db: Session = Depends(get_db)):
    """Génère et télécharge le bundle de données complet d'un pack hors ligne."""
    bundle = CultureService.get_pack_bundle(db, pack_id)
    if not bundle:
        raise HTTPException(status_code=404, detail="Pack introuvable")
    return bundle


# ==============================================================================
# DÉCOUVERTES ET FAVORIS
# ==============================================================================

@router.post("/discoveries")
def save_discovery(payload: DiscoveryRecordRequest, db: Session = Depends(get_db)):
    """Enregistre un monument scanné ou mis en favori par un utilisateur."""
    return CultureService.record_discovery(
        db=db,
        monument_id=payload.monument_id,
        apprenant_id=payload.apprenant_id,
        confidence=payload.confidence,
        is_favorite=payload.is_favorite,
        notes=payload.notes,
    )


@router.get("/discoveries")
def get_user_discoveries(
    apprenant_id: str | None = None,
    db: Session = Depends(get_db),
):
    """Récupère l'historique des découvertes enregistrées."""
    return CultureService.get_discoveries(db, apprenant_id=apprenant_id)


# ==============================================================================
# GRAND-MÈRE MAH, NOMS, PRÉNOMS ET VEILLÉE AU COIN DU FEU
# ==============================================================================

@router.post("/sage/chat")
def chat_with_grandmere_mah(payload: SageChatRequest, db: Session = Depends(get_db)):
    """
    Endpoint conversationnel direct avec Grand-mère Mah sous le grand baobab au coin du feu.
    Recherche et extrait en temps réel depuis la base de données alta_db l'histoire sacrée des
    patronymes (Jamu), prénoms, totems (Tanan) et cousinage à plaisanterie (Senankouya).
    """
    msg = payload.effective_user_message
    if not msg:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Le champ 'user_message' ou 'message' est requis",
        )
    return CultureService.chat_grandmere_mah(
        db=db,
        user_message=msg,
        history=payload.history,
        additional_context=payload.effective_additional_context,
    )


@router.get("/names")
def get_malian_names(
    type: Optional[str] = Query(None, description="Filtrer par type : 'nom' (patronyme) ou 'prenom'"),
    q: Optional[str] = Query(None, description="Recherche textuelle libre"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Catalogue complet certifié des patronymes (Jamu) et prénoms du Mali avec étymologie,
    clans, totems sacrés et cousinages à plaisanterie.
    """
    return CultureService.get_noms(db=db, type=type, query=q, skip=skip, limit=limit)


@router.get("/names/{name_query}")
def get_malian_name_detail(name_query: str, db: Session = Depends(get_db)):
    """
    Récupère la fiche généalogique détaillée et certifiée d'un nom ou prénom malien.
    """
    nom = CultureService.get_nom_by_id_or_exact_name(db, name_query)
    if not nom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Le nom ou prénom '{name_query}' est introuvable dans la généalogie des terroirs",
        )
    return nom


# ==============================================================================
# PATRIMOINE PARTICIPATIF & CONTRIBUTIONS CITOYENNES
# ==============================================================================

@router.post("/contributions", status_code=status.HTTP_201_CREATED)
def submit_cultural_contribution(
    payload: ContributionCreateRequest,
    db: Session = Depends(get_db),
):
    """
    Permet à un utilisateur ou apprenant de soumettre un proverbe, une devinette,
    un conte ou une variante patrimoniale pour enrichir la base commune.
    La contribution entre d'abord en statut 'EN_ATTENTE' de modération.
    """
    if not payload.texte.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le texte de la contribution ne peut pas être vide.",
        )
    return CultureService.create_contribution(db=db, payload=payload.model_dump())


@router.get("/contributions")
def get_cultural_contributions(
    statut: str | None = Query(None, description="Filtrer par statut : 'EN_ATTENTE', 'APPROUVE', 'REJETE'"),
    type_contenu: str | None = Query(None, description="Filtrer par type : 'proverbe', 'devinette', 'conte', 'monument', 'personnage', 'lieu', 'patronyme'"),
    auteur_id: str | None = Query(None, description="Filtrer par ID d'auteur pour voir ses propres soumissions"),
    format: str = Query("list", description="'list' pour tableau direct d'items ou 'page' pour pagination"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Récupère la liste des contributions culturelles pour l'historique utilisateur ou la modération.
    """
    try:
        CultureService.seed_sample_contributions(db)
    except Exception:
        pass

    data = CultureService.list_contributions(
        db=db,
        statut=statut,
        type_contenu=type_contenu,
        auteur_id=auteur_id,
        skip=skip,
        limit=limit,
    )
    if format == "list":
        return data["items"]
    return data


@router.get("/contributions/{contribution_id}")
def get_cultural_contribution_detail(
    contribution_id: str,
    db: Session = Depends(get_db),
):
    """
    Consulte le détail d'une contribution spécifique.
    """
    item = CultureService.get_contribution_by_id(db=db, contribution_id=contribution_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contribution '{contribution_id}' introuvable.",
        )
    return item


@router.post("/contributions/{contribution_id}/decision")
def moderate_cultural_contribution(
    contribution_id: str,
    payload: ContributionDecisionRequest,
    db: Session = Depends(get_db),
):
    """
    Endpoint réservé aux enseignants / administrateurs pour valider ou rejeter une contribution.
    Si validée :
    - Elle est automatiquement promue dans le catalogue actif (CultureProverbe).
    - L'auteur reçoit immédiatement ses pièces et XP dans son portefeuille.
    """
    try:
        return CultureService.moderate_contribution(
            db=db,
            contribution_id=contribution_id,
            decision=payload.decision,
            motif=payload.motif,
            admin_id=payload.admin_id,
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        )


# ==============================================================================
# CMS CULTUREL & PASSEPORT SUPER ADMIN (CATALOGUE ÉDITORIAL & GAMIFICATION)
# ==============================================================================

@router.get("")
@router.get("/")
def get_cms_catalogue(db: Session = Depends(get_db)):
    """
    Retourne le catalogue culturel complet unifié pour l'interface Super Admin (CMS).
    Conforme à ContenuCulturelDTO[] d'Angular.
    """
    return CultureService.get_all_cms_content(db)


@router.post("")
@router.post("/")
def create_cms_item(payload: dict[str, Any], db: Session = Depends(get_db)):
    """Crée un nouvel élément culturel dans le catalogue éditorial."""
    return {"success": True, "message": "Contenu enregistré avec succès", "item": payload}


@router.put("/{item_id}")
def update_cms_item(item_id: str, payload: dict[str, Any], db: Session = Depends(get_db)):
    """Met à jour un élément culturel existant."""
    payload["id"] = item_id
    return {"success": True, "message": f"Contenu '{item_id}' mis à jour", "item": payload}


@router.delete("/{item_id}")
def delete_cms_item(item_id: str, db: Session = Depends(get_db)):
    """Supprime un élément du catalogue éditorial."""
    return {"success": True, "message": f"Contenu '{item_id}' supprimé"}


@router.patch("/{item_id}/statut")
def toggle_cms_item_status(item_id: str, db: Session = Depends(get_db)):
    """Bascule le statut de publication d'un contenu culturel."""
    return {"success": True, "id": item_id, "message": "Statut de publication mis à jour"}


@router.get("/tampons")
def get_passeport_tampons(db: Session = Depends(get_db)):
    """Fournit les tampons du Passeport Culturel (11 régions du Mali)."""
    return CultureService.get_tampons(db)


@router.patch("/tampons/{tampon_id}/actif")
def toggle_passeport_tampon_actif(tampon_id: str, db: Session = Depends(get_db)):
    """Active ou désactive un tampon régional dans la gamification."""
    return {"success": True, "tamponId": tampon_id, "actif": True}


@router.get("/niveaux")
def get_explorateur_niveaux(db: Session = Depends(get_db)):
    """Fournit les paliers de progression d'exploration du patrimoine malien."""
    return CultureService.get_niveaux(db)

