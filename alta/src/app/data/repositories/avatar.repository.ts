import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of, map } from 'rxjs';
import { AvatarPedagogique, VoixPedagogique } from '../../domain/entites/avatar-pedagogique.entite';
import { CategorieMatiere, Matiere } from '../../core/enums';
import { environment } from '../../../environments/environment';

export const VOIX_DISPONIBLES: VoixPedagogique[] = [
  { id: 'vivienne', nom: 'Vivienne (Neurale Féminine)', langue: 'Français', description: 'Voix chaleureuse, posée et très explicite', genre: 'feminin', audioPreviewUrl: '/api/studio-vocal/test-audio', actif: true, dateCreation: new Date() },
  { id: 'remy', nom: 'Dr. Rémy (Masculin)', langue: 'Français', description: 'Voix méthodique, scientifique et bienveillante', genre: 'masculin', audioPreviewUrl: '/api/studio-vocal/test-audio', actif: true, dateCreation: new Date() },
  { id: 'denise', nom: 'Denise (Littéraire)', langue: 'Français', description: 'Voix dynamique, interactive et éloquente', genre: 'feminin', audioPreviewUrl: '/api/studio-vocal/test-audio', actif: true, dateCreation: new Date() },
  { id: 'henri', nom: 'Henri (Académique)', langue: 'Français', description: 'Voix posée et solennelle pour les sciences humaines', genre: 'masculin', audioPreviewUrl: '/api/studio-vocal/test-audio', actif: true, dateCreation: new Date() },
];

function parseMatiere(name: string): Matiere {
  const n = (name || '').toLowerCase();
  if (n.includes('math')) return Matiere.MATHEMATIQUES;
  if (n.includes('phys')) return Matiere.PHYSIQUE;
  if (n.includes('chim')) return Matiere.CHIMIE;
  if (n.includes('bio') || n.includes('svt') || n.includes('nature')) return Matiere.SVT;
  if (n.includes('eco')) return Matiere.ECONOMIE;
  if (n.includes('franc')) return Matiere.FRANCAIS;
  if (n.includes('hist')) return Matiere.HISTOIRE;
  if (n.includes('geo')) return Matiere.GEOGRAPHIE;
  if (n.includes('ang')) return Matiere.ANGLAIS;
  if (n.includes('philo')) return Matiere.PHILOSOPHIE;
  return Matiere.SVT;
}

@Injectable({ providedIn: 'root' })
export class AvatarRepository {
  private readonly http = inject(HttpClient);

  private mapDtoToAvatar(item: any, index: number = 0): AvatarPedagogique {
    return {
      id: item.id,
      nom: item.nom,
      description: item.stylePedagogique || 'Tuteur pédagogique AlternIA',
      matiere: parseMatiere(item.matiere),
      categorie: CategorieMatiere.SCIENTIFIQUE,
      imageUrl: item.photoUrl || `assets/avatars/${item.voixTts || 'vivienne'}.svg`,
      voixId: item.voixTts || 'vivienne',
      personnalite: item.stylePedagogique || 'Bienveillante et explicative',
      actif: item.parDefaut ?? item.actif ?? true,
      dateCreation: item.dateCreation ? new Date(item.dateCreation) : new Date(),
      utilisations: 120 + index * 45,
    };
  }

  obtenirTousAvatars(): Observable<AvatarPedagogique[]> {
    return this.http.get<any[]>(`${environment.apiUrl}/avatars`).pipe(
      map(list => (list || []).map((item, index) => this.mapDtoToAvatar(item, index)))
    );
  }

  obtenirAvatarActif(): Observable<AvatarPedagogique> {
    return this.http.get<any>(`${environment.apiUrl}/avatars/actif`).pipe(
      map(item => this.mapDtoToAvatar(item, 0))
    );
  }

  obtenirAvatarParId(id: string): Observable<AvatarPedagogique | undefined> {
    return this.obtenirTousAvatars().pipe(
      map(list => list.find(a => a.id === id))
    );
  }

  uploaderPhotoAvatar(file: File): Observable<{ photoUrl: string; fileName: string }> {
    const formData = new FormData();
    formData.append('file', file, file.name);
    return this.http.post<{ photoUrl: string; fileName: string }>(`${environment.apiUrl}/avatars/upload`, formData);
  }

  creerAvatar(data: {
    nom: string;
    matiere: string;
    stylePedagogique?: string;
    voixTts?: string;
    photoUrl?: string;
    parDefaut?: boolean;
  }): Observable<AvatarPedagogique> {
    return this.http.post<any>(`${environment.apiUrl}/avatars`, {
      nom: data.nom,
      matiere: data.matiere,
      style_pedagogique: data.stylePedagogique || 'Bienveillant et interactif',
      voix_tts: data.voixTts || 'vivienne',
      photo_url: data.photoUrl || null,
      par_defaut: data.parDefaut || false,
    }).pipe(map(item => this.mapDtoToAvatar(item, 0)));
  }

  activerAvatar(avatarId: string): Observable<AvatarPedagogique> {
    return this.http.put<any>(`${environment.apiUrl}/avatars/${avatarId}/activer`, {}).pipe(
      map(item => this.mapDtoToAvatar(item, 0))
    );
  }

  supprimerAvatar(avatarId: string): Observable<any> {
    return this.http.delete<any>(`${environment.apiUrl}/avatars/${avatarId}`);
  }

  obtenirToutesVoix(): Observable<VoixPedagogique[]> {
    return of(VOIX_DISPONIBLES);
  }

  testerAudio(phrase: string, voix: string): Observable<Blob> {
    return this.http.post(`${environment.apiUrl}/studio-vocal/test-audio`, {
      phrase,
      voix,
    }, { responseType: 'blob' });
  }
}
