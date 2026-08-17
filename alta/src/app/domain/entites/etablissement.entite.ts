import { Matiere, CategorieMatiere } from '../../core/enums';

export interface Etablissement {
  id: string;
  nom: string;
  ville: string;
  pays: string;
  email: string;
  telephone?: string;
  adresse?: string;
  logo?: string;
  nombreApprenants: number;
  nombreBoitiers: number;
  dateCreation: Date;
  abonnementActif: boolean;
  administrateurs: string[];
}

export interface Apprenant {
  id: string;
  nom: string;
  prenom: string;
  nomComplet: string;
  etablissementId: string;
  classe: string;
  dateNaissance: Date;
  avatar?: string;
  boitierId?: string;
  matieresFavorites: Matiere[];
  dateInscription: Date;
  derniereActivite: Date;
  actif: boolean;
  progression: number; // 0-100
}

export interface ProgressionApprenant {
  apprenantId: string;
  matiere: Matiere;
  categorie: CategorieMatiere;
  scoreGlobal: number;
  progressionHebdo: number[];
  competencesMaitrisees: string[];
  competencesArenforcer: string[];
  derniereSession: Date;
  nombreSessions: number;
  tempsTotal: number; // en minutes
}
