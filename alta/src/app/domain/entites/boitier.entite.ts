import { StatutBoitier } from '../../core/enums';

export interface Boitier {
  id: string;
  codeUnique: string;
  nom: string;
  modele: string;
  statut: StatutBoitier;
  niveauBatterie: number; // 0-100
  versionFirmware: string;
  derniereSync: Date;
  espaceUtilise: number; // Mo
  espaceTotal: number; // Mo
  wifiConnecte: boolean;
  ssid?: string;
  proprietaireId?: string; // parent ou etablissement
  enfantId?: string;
  etablissementId?: string;
  dateActivation: Date;
  localisation?: string;
}

export interface ConfigurationBoitier {
  boitierId: string;
  modeHorsLigne: boolean;
  syncAutomatique: boolean;
  heureDebut: string;
  heureFin: string;
  matieresPrioritaires: string[];
  volumeSon: number;
  luminosite: number;
  langue: string;
  controleParental: boolean;
  dureeSessionMax: number; // minutes
}
