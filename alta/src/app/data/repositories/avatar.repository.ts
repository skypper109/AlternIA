import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of, map } from 'rxjs';
import { AvatarPedagogique, VoixPedagogique } from '../../domain/entites/avatar-pedagogique.entite';
import { CategorieMatiere, Matiere } from '../../core/enums';
import { environment } from '../../../environments/environment';

export const VOIX_DISPONIBLES: VoixPedagogique[] = [
  { id: 'vivienne', nom: 'Vivienne (Neurale)', langue: 'Français', description: 'Voix chaleureuse, bienveillante et pédagogique', genre: 'feminin', audioPreviewUrl: '/api/studio-vocal/test-audio', actif: true, dateCreation: new Date() },
  { id: 'remy', nom: 'Rémy', langue: 'Français', description: 'Voix posée, méthodique et scientifique', genre: 'masculin', audioPreviewUrl: '/api/studio-vocal/test-audio', actif: true, dateCreation: new Date() },
  { id: 'denise', nom: 'Denise', langue: 'Français', description: 'Voix dynamique, littéraire et interactive', genre: 'feminin', audioPreviewUrl: '/api/studio-vocal/test-audio', actif: true, dateCreation: new Date() },
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

  obtenirTousAvatars(): Observable<AvatarPedagogique[]> {
    return this.http.get<any[]>(`${environment.apiUrl}/avatars`).pipe(
      map(list => {
        return (list || []).map((item, index) => ({
          id: item.id,
          nom: item.nom,
          description: item.stylePedagogique || 'Tuteur pédagogique AlternIA',
          matiere: parseMatiere(item.matiere),
          categorie: CategorieMatiere.SCIENTIFIQUE,
          imageUrl: item.photoUrl || `assets/avatars/${item.voixTts || 'vivienne'}.svg`,
          voixId: item.voixTts || 'vivienne',
          personnalite: item.stylePedagogique || 'Bienveillante et explicative',
          actif: item.actif ?? true,
          dateCreation: new Date(),
          utilisations: 120 + index * 45,
        }));
      })
    );
  }

  obtenirAvatarParId(id: string): Observable<AvatarPedagogique | undefined> {
    return this.obtenirTousAvatars().pipe(
      map(list => list.find(a => a.id === id))
    );
  }

  obtenirToutesVoix(): Observable<VoixPedagogique[]> {
    return of(VOIX_DISPONIBLES);
  }
}
