"""
Schémas Pydantic pour l'authentification et la gestion des utilisateurs.
"""

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ConnexionRequest(BaseModel):
    email: str
    mot_de_passe: Optional[str] = Field(default="", alias="motDePasse")

    model_config = ConfigDict(populate_by_name=True, extra="ignore")


class InscriptionParentRequest(BaseModel):
    nom_complet: Optional[str] = Field(default=None, alias="nomComplet")
    nom: Optional[str] = None
    prenom: Optional[str] = None
    email: str
    mot_de_passe: Optional[str] = Field(default="", alias="motDePasse")
    telephone: Optional[str] = None
    nom_enfant: Optional[str] = Field(default=None, alias="nomEnfant")
    classe_enfant: Optional[str] = Field(default="11eme", alias="classeEnfant")
    numero_serie_boitier: Optional[str] = Field(default=None, alias="numeroSerieBoitier")
    code_boitier: Optional[str] = Field(default=None, alias="codeBoitier")

    model_config = ConfigDict(populate_by_name=True, extra="ignore")


class InscriptionEtablissementRequest(BaseModel):
    nom_etablissement: str = Field(default="Établissement", alias="nomEtablissement")
    code_etablissement: Optional[str] = Field(default=None, alias="codeEtablissement")
    nom_responsable: Optional[str] = Field(default="Administrateur", alias="nomResponsable")
    email: str
    mot_de_passe: Optional[str] = Field(default="", alias="motDePasse")
    ville: Optional[str] = "Bamako"
    telephone: Optional[str] = None
    type_etablissement: Optional[str] = Field(default="Lycée", alias="typeEtablissement")

    model_config = ConfigDict(populate_by_name=True, extra="ignore")


class CreerUtilisateurRequest(BaseModel):
    nom_complet: str = Field(..., alias="nomComplet")
    email: str
    role: str = "enseignant"  # 'admin_ecole', 'enseignant', 'parent'
    mot_de_passe: Optional[str] = Field(default="alternia2026", alias="motDePasse")
    actif: bool = True

    model_config = ConfigDict(populate_by_name=True, extra="ignore")


class ModifierProfilRequest(BaseModel):
    nom_complet: Optional[str] = Field(default=None, alias="nomComplet")
    email: Optional[str] = None
    mot_de_passe_actuel: Optional[str] = Field(default=None, alias="motDePasseActuel")
    nouveau_mot_de_passe: Optional[str] = Field(default=None, alias="nouveauMotDePasse")

    model_config = ConfigDict(populate_by_name=True, extra="ignore")


class ModifierUtilisateurRequest(BaseModel):
    nom_complet: Optional[str] = Field(default=None, alias="nomComplet")
    email: Optional[str] = None
    role: Optional[str] = None
    actif: Optional[bool] = None
    nouveau_mot_de_passe: Optional[str] = Field(default=None, alias="nouveauMotDePasse")

    model_config = ConfigDict(populate_by_name=True, extra="ignore")
