import { Matiere } from '../../core/enums';

export type StatutSeance = 'PROGRAMMÉE' | 'EN_COURS' | 'TERMINÉE' | 'MANQUÉE' | 'REPORTÉE';

export interface SeanceRevision {
  id: string;
  titre: string;
  matiere: Matiere;
  jour: string; // Format YYYY-MM-DD
  heureDebut: string; // Format HH:mm
  heureFin: string; // Format HH:mm
  dureeMinutes: number;
  commentaire?: string;
  statut: StatutSeance;
  rappelMinutesAvant?: number;
  dateCreation: Date;
  dateReportee?: string;
}

export type TypeNotificationParent =
  | 'RAPPEL_AVANT'
  | 'DEBUT_SEANCE'
  | 'FIN_SEANCE'
  | 'SEANCE_MANQUEE'
  | 'ALERTE_SUIVI';

export interface NotificationIntelligente {
  id: string;
  titre: string;
  message: string;
  type: TypeNotificationParent;
  date: Date;
  lue: boolean;
  seanceId?: string;
  priorite: 'normale' | 'haute' | 'urgente';
}

export interface StatutSeanceBadgeConfig {
  label: string;
  cssClass: string;
  couleurBg: string;
  couleurTexte: string;
  couleurBorder: string;
}

export const STATUT_SEANCE_CONFIG: Record<StatutSeance, StatutSeanceBadgeConfig> = {
  PROGRAMMÉE: {
    label: 'PROGRAMMÉE',
    cssClass: 'statut-programmee',
    couleurBg: 'rgba(49, 73, 153, 0.12)',
    couleurTexte: '#314999',
    couleurBorder: 'rgba(49, 73, 153, 0.25)',
  },
  EN_COURS: {
    label: 'EN COURS',
    cssClass: 'statut-en-cours',
    couleurBg: 'rgba(64, 187, 204, 0.15)',
    couleurTexte: '#0284C7',
    couleurBorder: '#40BBCC',
  },
  TERMINÉE: {
    label: 'TERMINÉE',
    cssClass: 'statut-terminee',
    couleurBg: 'rgba(16, 185, 129, 0.12)',
    couleurTexte: '#059669',
    couleurBorder: 'rgba(16, 185, 129, 0.25)',
  },
  MANQUÉE: {
    label: 'MANQUÉE',
    cssClass: 'statut-manquee',
    couleurBg: 'rgba(239, 68, 68, 0.12)',
    couleurTexte: '#DC2626',
    couleurBorder: 'rgba(239, 68, 68, 0.25)',
  },
  REPORTÉE: {
    label: 'REPORTÉE',
    cssClass: 'statut-reportee',
    couleurBg: 'rgba(241, 133, 31, 0.12)',
    couleurTexte: '#F1851F',
    couleurBorder: 'rgba(241, 133, 31, 0.25)',
  },
};
