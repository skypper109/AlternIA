import { Injectable, signal, computed, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { Matiere } from '../enums';
import { SeanceRevision, StatutSeance, NotificationIntelligente } from '../../domain/entites/programme-revision.entite';
import { environment } from '../../../environments/environment';

function parseMatiereEnum(name: string): Matiere {
  const n = (name || '').toUpperCase();
  if (n.includes('MATH')) return Matiere.MATHEMATIQUES;
  if (n.includes('PHYS')) return Matiere.PHYSIQUE;
  if (n.includes('CHIM')) return Matiere.CHIMIE;
  if (n.includes('SVT') || n.includes('BIO')) return Matiere.SVT;
  if (n.includes('FRAN')) return Matiere.FRANCAIS;
  if (n.includes('HIST')) return Matiere.HISTOIRE;
  if (n.includes('GEO')) return Matiere.GEOGRAPHIE;
  if (n.includes('ANGL')) return Matiere.ANGLAIS;
  if (n.includes('PHIL')) return Matiere.PHILOSOPHIE;
  return Matiere.MATHEMATIQUES;
}

@Injectable({
  providedIn: 'root',
})
export class ProgrammeRevisionService {
  private readonly http = inject(HttpClient);

  // Liste des séances de révision synchronisée avec alta_db
  readonly seances = signal<SeanceRevision[]>([]);

  // Centre de notifications intelligentes du parent
  readonly notifications = signal<NotificationIntelligente[]>([
    {
      id: 'notif-1',
      titre: 'Rappel de séance imminent',
      message: 'Révision de Mathématiques (Équations du 2nd degré) programmée à 17:00 aujourd’hui (dans 30 min).',
      type: 'RAPPEL_AVANT',
      date: new Date(Date.now() - 1000 * 60 * 15),
      lue: false,
      seanceId: 'seance-1',
      priorite: 'haute',
    },
    {
      id: 'notif-2',
      titre: 'Séance non réalisée',
      message: 'La séance de Chimie d’hier à 17:30 n’a pas été effectuée sur le boîtier.',
      type: 'SEANCE_MANQUEE',
      date: new Date(Date.now() - 1000 * 60 * 60 * 18),
      lue: false,
      seanceId: 'seance-4',
      priorite: 'haute',
    },
  ]);

  constructor() {
    this.chargerSeancesDepuisBackend();
  }

  async chargerSeancesDepuisBackend(): Promise<void> {
    try {
      const list = await firstValueFrom(this.http.get<any[]>(`${environment.apiUrl}/programme-revision`));
      if (list && list.length > 0) {
        const mapped: SeanceRevision[] = list.map(s => ({
          id: s.id,
          titre: s.titre,
          matiere: parseMatiereEnum(s.matiere),
          jour: s.jour,
          heureDebut: s.heureDebut,
          heureFin: s.heureFin,
          dureeMinutes: s.dureeMinutes || 45,
          commentaire: s.commentaire,
          statut: s.statut as StatutSeance,
          rappelMinutesAvant: s.rappelMinutesAvant || 30,
          dateCreation: s.dateCreation ? new Date(s.dateCreation) : new Date(),
        }));
        this.seances.set(mapped);
      }
    } catch {
      // Fallback
    }
  }

  // Getters & Computed
  readonly seancesTriees = computed(() => {
    return [...this.seances()].sort((a, b) => {
      const dateA = `${a.jour}T${a.heureDebut}`;
      const dateB = `${b.jour}T${b.heureDebut}`;
      return dateA.localeCompare(dateB);
    });
  });

  readonly seancesAujourdhui = computed(() => {
    const aujourdhuiStr = new Date().toISOString().split('T')[0];
    return this.seancesTriees().filter(s => s.jour === aujourdhuiStr);
  });

  readonly prochainesSeances = computed(() => {
    return this.seancesTriees().filter(s => s.statut === 'PROGRAMMÉE' || s.statut === 'REPORTÉE');
  });

  readonly seancesTerminees = computed(() => {
    return this.seances().filter(s => s.statut === 'TERMINÉE');
  });

  readonly seancesManquees = computed(() => {
    return this.seances().filter(s => s.statut === 'MANQUÉE');
  });

  readonly tauxRespectPlanning = computed(() => {
    const terminees = this.seancesTerminees().length;
    const manquees = this.seancesManquees().length;
    const totalEvalue = terminees + manquees;
    if (totalEvalue === 0) return 100;
    return Math.round((terminees / totalEvalue) * 100);
  });

  readonly notificationsNonLuesCount = computed(() => {
    return this.notifications().filter(n => !n.lue).length;
  });

  // Actions
  async ajouterSeance(seance: Omit<SeanceRevision, 'id' | 'dateCreation'>): Promise<void> {
    const duree = this.calculerDuree(seance.heureDebut, seance.heureFin);
    try {
      const resp = await firstValueFrom(
        this.http.post<any>(`${environment.apiUrl}/programme-revision`, {
          titre: seance.titre,
          matiere: seance.matiere,
          jour: seance.jour,
          heureDebut: seance.heureDebut,
          heureFin: seance.heureFin,
          dureeMinutes: duree,
          commentaire: seance.commentaire,
          statut: seance.statut,
          rappelMinutesAvant: seance.rappelMinutesAvant || 30,
        })
      );
      const nouvelleSeance: SeanceRevision = {
        ...seance,
        id: resp?.id || `seance-${Date.now()}`,
        dureeMinutes: duree,
        dateCreation: new Date(),
      };
      this.seances.update(list => [...list, nouvelleSeance]);
    } catch {
      const nouvelleSeance: SeanceRevision = {
        ...seance,
        id: `seance-${Date.now()}`,
        dureeMinutes: duree,
        dateCreation: new Date(),
      };
      this.seances.update(list => [...list, nouvelleSeance]);
    }

    this.ajouterNotification({
      titre: 'Nouvelle séance programmée',
      message: `La séance de ${seance.titre} a été enregistrée pour le ${seance.jour} de ${seance.heureDebut} à ${seance.heureFin}.`,
      type: 'DEBUT_SEANCE',
      date: new Date(),
      lue: false,
      priorite: 'normale',
    });
  }

  async modifierSeance(id: string, modification: Partial<SeanceRevision>): Promise<void> {
    const existing = this.seances().find(s => s.id === id);
    if (existing) {
      const duree = modification.heureDebut && modification.heureFin
        ? this.calculerDuree(modification.heureDebut, modification.heureFin)
        : existing.dureeMinutes;
      const updated = { ...existing, ...modification, dureeMinutes: duree };

      try {
        await firstValueFrom(
          this.http.put(`${environment.apiUrl}/programme-revision/${id}`, {
            titre: updated.titre,
            matiere: updated.matiere,
            jour: updated.jour,
            heureDebut: updated.heureDebut,
            heureFin: updated.heureFin,
            dureeMinutes: updated.dureeMinutes,
            commentaire: updated.commentaire,
            statut: updated.statut,
            rappelMinutesAvant: updated.rappelMinutesAvant,
          })
        );
      } catch {
        // Fallback
      }

      this.seances.update(list => list.map(s => (s.id === id ? updated : s)));
    }
  }

  async supprimerSeance(id: string): Promise<void> {
    try {
      await firstValueFrom(this.http.delete(`${environment.apiUrl}/programme-revision/${id}`));
    } catch {
      // Fallback
    }
    this.seances.update(list => list.filter(s => s.id !== id));
  }

  reporterSeance(id: string, nouvelleDate: string, nouvelleHeure: string, raison?: string): void {
    this.modifierSeance(id, {
      jour: nouvelleDate,
      heureDebut: nouvelleHeure,
      statut: 'REPORTÉE',
      commentaire: raison || 'Reporté par le parent',
    });
  }

  changerStatutSeance(id: string, statut: StatutSeance): void {
    this.modifierSeance(id, { statut });
  }

  ajouterNotification(notif: Omit<NotificationIntelligente, 'id'>): void {
    const nouvelleNotif: NotificationIntelligente = {
      ...notif,
      id: `notif-${Date.now()}`,
    };
    this.notifications.update(list => [nouvelleNotif, ...list]);
  }

  marquerNotificationLue(id: string): void {
    this.notifications.update(list =>
      list.map(n => (n.id === id ? { ...n, lue: true } : n))
    );
  }

  marquerToutesNotificationsLues(): void {
    this.notifications.update(list => list.map(n => ({ ...n, lue: true })));
  }

  toutMarquerNotificationLue(): void {
    this.marquerToutesNotificationsLues();
  }

  supprimerNotification(id: string): void {
    this.notifications.update(list => list.filter(n => n.id !== id));
  }

  private calculerDuree(debut: string, fin: string): number {
    const [hD, mD] = debut.split(':').map(Number);
    const [hF, mF] = fin.split(':').map(Number);
    return (hF * 60 + mF) - (hD * 60 + mD);
  }
}
