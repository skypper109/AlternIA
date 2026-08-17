import { Injectable, signal, computed } from '@angular/core';
import { ProfilPedagogique, ConfigurationEnseignantParent } from '../../domain/entites/enseignant-ia.entite';

@Injectable({
  providedIn: 'root',
})
export class EnseignantIaParentService {
  // Liste des profils pédagogiques avec Vivienne par défaut
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
    {
      id: 'prof-coulibaly',
      nom: 'Professeure Samaké Fatou',
      matiere: 'Français & Philosophie',
      photoUrl: '',
      audioUrl: '',
      audioFileName: 'extrait-francais-coulibaly.mp3',
      actif: false,
    },
  ]);

  readonly configuration = signal<ConfigurationEnseignantParent>({
    profilActifId: 'avatar-vivienne',
    dateDerniereModification: new Date(),
  });

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

  ajouterProfil(profil: Omit<ProfilPedagogique, 'id'>): void {
    const newId = 'prof-' + Date.now();
    const nouveauProfil: ProfilPedagogique = {
      ...profil,
      id: newId,
      actif: this.profils().length === 0,
    };
    this.profils.update(list => [...list, nouveauProfil]);
    if (nouveauProfil.actif) {
      this.choisirProfil(newId);
    }
  }

  modifierProfil(id: string, modifications: Partial<ProfilPedagogique>): void {
    this.profils.update(list =>
      list.map(p => (p.id === id ? { ...p, ...modifications } : p))
    );
  }

  supprimerProfil(id: string): void {
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
