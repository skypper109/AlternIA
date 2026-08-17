export type MatiereEnseignee =
  | 'Mathématiques'
  | 'Physique-Chimie'
  | 'Français'
  | 'SVT'
  | 'Histoire-Géographie'
  | 'Anglais'
  | 'Philosophie'
  | 'Économie'
  | 'Autre';

/**
 * ProfilPedagogique – profil simple représentant un enseignant.
 * Contient uniquement : photo, nom, matière et fichier audio.
 */
export interface ProfilPedagogique {
  id: string;
  nom: string;
  matiere: string;
  photoUrl?: string;
  audioUrl?: string;
  audioFileName?: string;
  actif?: boolean;
}

export interface ConfigurationEnseignantParent {
  profilActifId: string;
  dateDerniereModification: Date;
}

// Aliases rétro-compatibles
export type AvatarParent = ProfilPedagogique;
