import { Matiere } from '../../core/enums';

export interface HistoriqueSession {
  id: string;
  enfantId: string;
  date: Date;
  duree: number; // minutes
  matiere: Matiere;
  nombreQuestionsIA: number;
  nombreQuiz: number;
  nombreExercices: number;
  scoreObtenu: number;
  notionsTravaillees: string[];
}

export interface ProgressionParMatiere {
  matiere: Matiere;
  score: number; // 0-100
  variation: number; // variation en %
  courbeEvolution: number[];
  competencesMaitrisees: string[];
  competencesArenforcer: string[];
  derniereTravail: Date;
  tempsTotal: number;
}
