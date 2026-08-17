import { Injectable, signal, computed } from '@angular/core';
import { Matiere } from '../enums';
import { SeanceRevision, StatutSeance, NotificationIntelligente } from '../../domain/entites/programme-revision.entite';

@Injectable({
  providedIn: 'root',
})
export class ProgrammeRevisionService {
  // Liste des séances de révision
  readonly seances = signal<SeanceRevision[]>([
    {
      id: 'seance-1',
      titre: 'Révision Équations du 2nd degré',
      matiere: Matiere.MATHEMATIQUES,
      jour: '2026-08-11',
      heureDebut: '17:00',
      heureFin: '17:45',
      dureeMinutes: 45,
      commentaire: 'Axer sur la méthode du discriminant et les exercices pratiques.',
      statut: 'PROGRAMMÉE',
      rappelMinutesAvant: 30,
      dateCreation: new Date('2026-08-08'),
    },
    {
      id: 'seance-2',
      titre: 'Quiz interactif Optique & Ondes',
      matiere: Matiere.PHYSIQUE,
      jour: '2026-08-11',
      heureDebut: '18:15',
      heureFin: '19:00',
      dureeMinutes: 45,
      commentaire: 'Session de questions courtes avec l’Enseignant IA.',
      statut: 'PROGRAMMÉE',
      rappelMinutesAvant: 15,
      dateCreation: new Date('2026-08-08'),
    },
    {
      id: 'seance-3',
      titre: 'Lecture analytique & Vocabulaire',
      matiere: Matiere.FRANCAIS,
      jour: '2026-08-10',
      heureDebut: '16:30',
      heureFin: '17:15',
      dureeMinutes: 45,
      commentaire: 'Commentaire de texte sur le théâtre du XVIIe siècle.',
      statut: 'TERMINÉE',
      dateCreation: new Date('2026-08-07'),
    },
    {
      id: 'seance-4',
      titre: 'Réaction d’oxydoréduction',
      matiere: Matiere.CHIMIE,
      jour: '2026-08-10',
      heureDebut: '17:30',
      heureFin: '18:15',
      dureeMinutes: 45,
      commentaire: 'Exercices manqués faute de disponibilité.',
      statut: 'MANQUÉE',
      dateCreation: new Date('2026-08-07'),
    },
    {
      id: 'seance-5',
      titre: 'Génétique & ADN',
      matiere: Matiere.SVT,
      jour: '2026-08-09',
      heureDebut: '15:00',
      heureFin: '15:45',
      dureeMinutes: 45,
      statut: 'MANQUÉE',
      dateCreation: new Date('2026-08-06'),
    },
    {
      id: 'seance-6',
      titre: 'Histoire : La Guerre Froide',
      matiere: Matiere.HISTOIRE,
      jour: '2026-08-12',
      heureDebut: '16:00',
      heureFin: '17:00',
      dureeMinutes: 60,
      commentaire: 'Reporté depuis lundi.',
      statut: 'REPORTÉE',
      dateCreation: new Date('2026-08-08'),
    },
    {
      id: 'seance-7',
      titre: 'Grammaire & Expressions Anglaises',
      matiere: Matiere.ANGLAIS,
      jour: '2026-08-13',
      heureDebut: '17:00',
      heureFin: '17:45',
      dureeMinutes: 45,
      statut: 'PROGRAMMÉE',
      dateCreation: new Date('2026-08-09'),
    },
    {
      id: 'seance-8',
      titre: 'Geometrie dans l’espace',
      matiere: Matiere.MATHEMATIQUES,
      jour: '2026-08-14',
      heureDebut: '10:00',
      heureFin: '11:00',
      dureeMinutes: 60,
      statut: 'PROGRAMMÉE',
      dateCreation: new Date('2026-08-09'),
    },
  ]);

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
    {
      id: 'notif-3',
      titre: 'Alerte assiduité : séances manquées',
      message: 'Attention : Deux séances consécutives ont été manquées (SVT & Chimie).',
      type: 'ALERTE_SUIVI',
      date: new Date(Date.now() - 1000 * 60 * 60 * 24),
      lue: false,
      priorite: 'urgente',
    },
    {
      id: 'notif-4',
      titre: 'Séance terminée avec succès',
      message: 'La séance de Français a été complétée le 10 août avec 92% d’exercices réussis avec l’Enseignant IA.',
      type: 'FIN_SEANCE',
      date: new Date(Date.now() - 1000 * 60 * 60 * 30),
      lue: true,
      seanceId: 'seance-3',
      priorite: 'normale',
    },
    {
      id: 'notif-5',
      titre: 'Alerte inactivité',
      message: 'Aucune activité de révision libre n’a été enregistrée le week-end dernier.',
      type: 'ALERTE_SUIVI',
      date: new Date(Date.now() - 1000 * 60 * 60 * 72),
      lue: true,
      priorite: 'normale',
    },
  ]);

  // Computed signals
  readonly seancesTriees = computed(() => {
    return [...this.seances()].sort((a, b) => {
      const dateA = new Date(`${a.jour}T${a.heureDebut}`);
      const dateB = new Date(`${b.jour}T${b.heureDebut}`);
      return dateA.getTime() - dateB.getTime();
    });
  });

  readonly prochainesSeances = computed(() => {
    const aujourdhuiStr = new Date().toISOString().split('T')[0];
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
  ajouterSeance(seance: Omit<SeanceRevision, 'id' | 'dateCreation'>): void {
    const duree = this.calculerDuree(seance.heureDebut, seance.heureFin);
    const nouvelleSeance: SeanceRevision = {
      ...seance,
      id: `seance-${Date.now()}`,
      dureeMinutes: duree,
      dateCreation: new Date(),
    };
    this.seances.update(list => [...list, nouvelleSeance]);

    // Ajouter une notification automatique
    this.ajouterNotification({
      titre: 'Nouvelle séance programmée',
      message: `La séance de ${seance.titre} a été ajoutée pour le ${seance.jour} de ${seance.heureDebut} à ${seance.heureFin}.`,
      type: 'DEBUT_SEANCE',
      date: new Date(),
      lue: false,
      seanceId: nouvelleSeance.id,
      priorite: 'normale',
    });
  }

  modifierSeance(id: string, modification: Partial<SeanceRevision>): void {
    this.seances.update(list =>
      list.map(s => {
        if (s.id === id) {
          const duree = modification.heureDebut && modification.heureFin
            ? this.calculerDuree(modification.heureDebut, modification.heureFin)
            : s.dureeMinutes;
          return { ...s, ...modification, dureeMinutes: duree };
        }
        return s;
      })
    );
  }

  supprimerSeance(id: string): void {
    this.seances.update(list => list.filter(s => s.id !== id));
  }

  changerStatutSeance(id: string, statut: StatutSeance): void {
    this.seances.update(list =>
      list.map(s => (s.id === id ? { ...s, statut } : s))
    );

    if (statut === 'MANQUÉE') {
      const s = this.seances().find(item => item.id === id);
      if (s) {
        this.ajouterNotification({
          titre: 'Alerte : Séance manquée',
          message: `La séance "${s.titre}" n'a pas été réalisée.`,
          type: 'SEANCE_MANQUEE',
          date: new Date(),
          lue: false,
          seanceId: id,
          priorite: 'haute',
        });
      }
    }
  }

  reporterSeance(id: string, nouvelleDate: string, heureDebut: string, heureFin: string): void {
    this.seances.update(list =>
      list.map(s =>
        s.id === id
          ? {
              ...s,
              jour: nouvelleDate,
              heureDebut,
              heureFin,
              dureeMinutes: this.calculerDuree(heureDebut, heureFin),
              statut: 'REPORTÉE',
              dateReportee: new Date().toISOString(),
            }
          : s
      )
    );
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

  toutMarquerNotificationLue(): void {
    this.notifications.update(list => list.map(n => ({ ...n, lue: true })));
  }

  private calculerDuree(heureDebut: string, heureFin: string): number {
    const [hDeb, mDeb] = heureDebut.split(':').map(Number);
    const [hFin, mFin] = heureFin.split(':').map(Number);
    const debMin = hDeb * 60 + mDeb;
    const finMin = hFin * 60 + mFin;
    return Math.max(15, finMin - debMin);
  }
}
