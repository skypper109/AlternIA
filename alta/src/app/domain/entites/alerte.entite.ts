export interface Alerte {
  id: string;
  parentId: string;
  enfantId: string;
  type: TypeAlerte;
  titre: string;
  message: string;
  dateCreation: Date;
  lue: boolean;
  priorite: 'basse' | 'normale' | 'haute';
}

export enum TypeAlerte {
  FAIBLE_ACTIVITE = 'FAIBLE_ACTIVITE',
  PROGRESSION_REMARQUABLE = 'PROGRESSION_REMARQUABLE',
  REVISION_RECOMMANDEE = 'REVISION_RECOMMANDEE',
  OBJECTIF_ATTEINT = 'OBJECTIF_ATTEINT',
  BOITIER_DECONNECTE = 'BOITIER_DECONNECTE',
  SYNCHRONISATION = 'SYNCHRONISATION',
}
