import { Matiere } from '../../core/enums';

export interface StatistiquesUtilisation {
  etablissementId: string;
  periode: 'jour' | 'semaine' | 'mois';
  totalQuestionsIA: number;
  tempsTotal: number; // minutes
  apprenantActifs: number;
  tauxEngagement: number; // 0-100
  matieresPlusUtilisees: MatiereStats[];
  pictUtilisation: PicUtilisation[];
  activiteJournaliere: number[];
  activiteHebdomadaire: number[];
  evolutionMensuelle: number[];
  dateGeneration: Date;
}

export interface MatiereStats {
  matiere: Matiere;
  pourcentage: number;
  totalQuestions: number;
  tempsTotal: number;
}

export interface PicUtilisation {
  heure: number;
  nombreSessions: number;
}

export interface NotionDifficile {
  matiere: Matiere;
  notion: string;
  tauxEchec: number;
  nombreTentatives: number;
  apprenantsConcernes: number;
  remediationProposee?: boolean;
}

export interface RapportActivite {
  id: string;
  etablissementId: string;
  titre: string;
  periode: string;
  dateDebut: Date;
  dateFin: Date;
  dateGeneration: Date;
  type: 'pdf' | 'excel';
  statut: 'genere' | 'en_cours' | 'erreur';
  urlTelechargement?: string;
  tailleFichier?: number;
}
