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
  landmarks?: any;
  visemePhotos?: Record<string, string>;
  compatibilityScore?: number;
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

export interface AvatarUploadResponse {
  photoUrl: string;
  fileName: string;
  videoUrl?: string | null;
  isVideo?: boolean;
  compatibility?: any;
  landmarks?: any;
  visemePhotos?: Record<string, string>;
}

export interface VisemeUploadResponse {
  visemeId: string;
  photoUrl: string;
  fileName: string;
  compatibility?: any;
  landmarks?: any;
}
