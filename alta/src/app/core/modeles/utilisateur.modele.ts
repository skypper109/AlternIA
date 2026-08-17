import { RoleUtilisateur } from '../enums';

export interface Utilisateur {
  id: string;
  email: string;
  role: RoleUtilisateur;
  nomComplet: string;
  avatar?: string;
  dateCreation: Date;
  dernierAcces?: Date;
  actif: boolean;
}

export interface SessionUtilisateur {
  utilisateur: Utilisateur;
  token: string;
  expiresAt: Date;
}
