import { Injectable, signal, computed, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { ProfilPedagogique, ConfigurationEnseignantParent } from '../../domain/entites/enseignant-ia.entite';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root',
})
export class EnseignantIaParentService {
  private readonly http = inject(HttpClient);

  // Liste des profils pédagogiques connectée au backend alta_db
  readonly profils = signal<ProfilPedagogique[]>([
    {
      id: 'avatar-vivienne',
      nom: 'Professeure Vivienne',
      matiere: 'SVT & Sciences Naturelles',
      photoUrl: '',
      audioUrl: '',
      audioFileName: 'extrait-vivienne-svt.mp3',
      actif: true,
    },
    {
      id: 'prof-diarra',
      nom: 'Dr. Koné Amadou',
      matiere: 'Mathématiques & Physique',
      photoUrl: '',
      audioUrl: '',
      audioFileName: 'extrait-maths-diarra.mp3',
      actif: false,
    },
  ]);

  readonly configuration = signal<ConfigurationEnseignantParent>({
    profilActifId: 'avatar-vivienne',
    dateDerniereModification: new Date(),
  });

  constructor() {
    this.chargerAvatarsDepuisBackend();
  }

  async chargerAvatarsDepuisBackend(): Promise<void> {
    try {
      const data = await firstValueFrom(this.http.get<any[]>(`${environment.apiUrl}/avatars`));
      if (data && data.length > 0) {
        const mapped: ProfilPedagogique[] = data.map((a, idx) => ({
          id: a.id,
          nom: a.nom,
          matiere: a.matiere || 'Enseignement Général',
          photoUrl: a.photoUrl || '',
          audioUrl: a.audioUrl || '',
          audioFileName: a.audioFileName || `extrait-${a.nom.toLowerCase().replace(/\s+/g, '-')}.mp3`,
          actif: a.actif ?? (idx === 0),
        }));
        this.profils.set(mapped);
        const actif = mapped.find(p => p.actif) || mapped[0];
        if (actif) {
          this.configuration.set({ profilActifId: actif.id, dateDerniereModification: new Date() });
        }
      }
    } catch {
      // Conserver les profils de base si hors ligne
    }
  }

  // Profil actif sélectionné
  readonly profilActif = computed(() => {
    const config = this.configuration();
    return this.profils().find(p => p.id === config.profilActifId) ?? this.profils()[0];
  });

  // Alias rétro-compatible pour l'accueil parent
  readonly avatarActif = this.profilActif;
  readonly avatars = this.profils;

  // Actions CRUD
  choisirProfil(profilId: string): void {
    this.profils.update(list =>
      list.map(p => ({
        ...p,
        actif: p.id === profilId,
      }))
    );
    this.configuration.update(cfg => ({
      ...cfg,
      profilActifId: profilId,
      dateDerniereModification: new Date(),
    }));
  }

  async ajouterProfil(profil: Omit<ProfilPedagogique, 'id'>): Promise<void> {
    try {
      const resp = await firstValueFrom(
        this.http.post<any>(`${environment.apiUrl}/avatars`, {
          nom: profil.nom,
          matiere: profil.matiere,
          style_pedagogique: 'Bienveillant et interactif',
          voix_tts: 'vivienne',
          actif: true,
        })
      );
      const newId = resp?.id || 'prof-' + Date.now();
      const nouveauProfil: ProfilPedagogique = {
        ...profil,
        id: newId,
        actif: true,
      };
      this.profils.update(list => [...list.map(p => ({ ...p, actif: false })), nouveauProfil]);
      this.choisirProfil(newId);
    } catch {
      const newId = 'prof-' + Date.now();
      const nouveauProfil: ProfilPedagogique = {
        ...profil,
        id: newId,
        actif: true,
      };
      this.profils.update(list => [...list, nouveauProfil]);
      this.choisirProfil(newId);
    }
  }

  modifierProfil(id: string, modifications: Partial<ProfilPedagogique>): void {
    this.profils.update(list =>
      list.map(p => (p.id === id ? { ...p, ...modifications } : p))
    );
  }

  async supprimerProfil(id: string): Promise<void> {
    try {
      await firstValueFrom(this.http.delete(`${environment.apiUrl}/avatars/${id}`));
    } catch {
      // Continuer en local
    }
    this.profils.update(list => list.filter(p => p.id !== id));
    if (this.configuration().profilActifId === id) {
      const premierRestant = this.profils()[0];
      if (premierRestant) {
        this.choisirProfil(premierRestant.id);
      }
    }
  }

  changerPhoto(id: string, photoUrl: string): void {
    this.modifierProfil(id, { photoUrl });
  }

  supprimerPhoto(id: string): void {
    this.modifierProfil(id, { photoUrl: '' });
  }

  changerAudio(id: string, audioUrl: string, audioFileName: string): void {
    this.modifierProfil(id, { audioUrl, audioFileName });
  }

  supprimerAudio(id: string): void {
    this.modifierProfil(id, { audioUrl: '', audioFileName: '' });
  }
}
