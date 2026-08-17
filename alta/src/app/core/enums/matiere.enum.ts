export enum Matiere {
  MATHEMATIQUES = 'MATHEMATIQUES',
  MATH_FINANCIERE = 'MATH_FINANCIERE',
  PHYSIQUE = 'PHYSIQUE',
  CHIMIE = 'CHIMIE',
  SVT = 'SVT',
  ECONOMIE = 'ECONOMIE',
  FRANCAIS = 'FRANCAIS',
  HISTOIRE = 'HISTOIRE',
  GEOGRAPHIE = 'GEOGRAPHIE',
  ANGLAIS = 'ANGLAIS',
  PHILOSOPHIE = 'PHILOSOPHIE',
  INFORMATIQUE = 'INFORMATIQUE',
}

export const MatiereLabels: Record<Matiere, string> = {
  [Matiere.MATHEMATIQUES]: 'Mathématiques',
  [Matiere.MATH_FINANCIERE]: 'Math Financière',
  [Matiere.PHYSIQUE]: 'Physique',
  [Matiere.CHIMIE]: 'Chimie',
  [Matiere.SVT]: 'SVT',
  [Matiere.ECONOMIE]: 'Économie',
  [Matiere.FRANCAIS]: 'Français',
  [Matiere.HISTOIRE]: 'Histoire',
  [Matiere.GEOGRAPHIE]: 'Géographie',
  [Matiere.ANGLAIS]: 'Anglais',
  [Matiere.PHILOSOPHIE]: 'Philosophie',
  [Matiere.INFORMATIQUE]: 'Informatique',
};

export const MatiereCouleurs: Record<Matiere, string> = {
  [Matiere.MATHEMATIQUES]: '#314999',
  [Matiere.MATH_FINANCIERE]: '#1d6fa4',
  [Matiere.PHYSIQUE]: '#40BBCC',
  [Matiere.CHIMIE]: '#7c3aed',
  [Matiere.SVT]: '#10B981',
  [Matiere.ECONOMIE]: '#F59E0B',
  [Matiere.FRANCAIS]: '#F1851F',
  [Matiere.HISTOIRE]: '#dc2626',
  [Matiere.GEOGRAPHIE]: '#059669',
  [Matiere.ANGLAIS]: '#2563eb',
  [Matiere.PHILOSOPHIE]: '#9333ea',
  [Matiere.INFORMATIQUE]: '#0891b2',
};
