import { Matiere } from '../../core/enums';

export interface QuestionFrequente {
  id: string;
  question: string;
  matiere: Matiere;
  chapitre: string;
  nombreOccurrences: number;
  evolutionPct: number;
  niveauPriorite: 'haute' | 'moyenne' | 'basse';
}

export interface TendanceMatiere {
  matiere: Matiere;
  nombreConsultations: number;
  variationHebdoPct: number;
  variationMensuellePct: number;
  statut: 'hausse' | 'baisse' | 'stable';
  historique7jours: number[];
}

export interface NotionRenforcer {
  id: string;
  notion: string;
  matiere: Matiere;
  chapitre: string;
  nombreRequetes: number;
  tauxAssistanceIA: number; // 0-100
  priorite: 'haute' | 'moyenne' | 'basse';
  actionRecommandee: string;
}

export interface IndiceEngagement {
  scoreGlobal: number; // ex: 87
  niveau: 'Excellent' | 'Bon' | 'Moyen' | 'Faible';
  variationHebdo: number;
  composantes: {
    tempsUtilisation: number; // score sur 100
    frequenceConnexion: number;
    diversiteMatieres: number;
    volumeQuestions: number;
  };
}

export interface TelemetrieSysteme {
  statutServeur: 'OPERATIONNEL' | 'OPTIMAL' | 'DEGRADE';
  latenceReseauMs: number;
  disponibilitePct: number;
  boitiersConnectes: number;
  boitiersTotal: number;
  requetesParSeconde: number;
  chargeCpuCloudPct: number;
  bandePassanteMbps: number;
  dernierePulsation: Date;
}
