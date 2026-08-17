import { Matiere } from '../../core/enums';

export interface Parent {
  id: string;
  nom: string;
  prenom: string;
  nomComplet: string;
  email: string;
  telephone?: string;
  avatar?: string;
  enfantsIds: string[];
  dateInscription: Date;
  actif: boolean;
}

export interface Enfant {
  id: string;
  nom: string;
  prenom: string;
  nomComplet: string;
  parentId: string;
  boitierId?: string;
  classe: string;
  dateNaissance: Date;
  avatar?: string;
  matieresFavorites: Matiere[];
  progression: number;
  tempsEtude: number; // minutes aujourd'hui
  dernierAcces: Date;
  objectifsAtteints: number;
  totalObjectifs: number;
}
