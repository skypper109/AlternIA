import { Matiere, CategorieMatiere } from '../../core/enums';

export interface AvatarPedagogique {
  id: string;
  nom: string;
  description: string;
  matiere: Matiere;
  categorie: CategorieMatiere;
  imageUrl?: string;
  voixId?: string;
  personnalite: string;
  actif: boolean;
  dateCreation: Date;
  utilisations: number;
}

export interface VoixPedagogique {
  id: string;
  nom: string;
  description: string;
  langue: string;
  genre: 'masculin' | 'feminin' | 'neutre';
  accent?: string;
  audioPreviewUrl?: string;
  matiereAssociee?: Matiere;
  actif: boolean;
  cloneeDepuis?: string;
  dateCreation: Date;
}
