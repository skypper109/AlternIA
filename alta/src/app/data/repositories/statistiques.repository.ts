import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import {
  StatistiquesUtilisation,
  NotionDifficile,
  RapportActivite,
  MatiereStats,
} from '../../domain/entites/statistiques-utilisation.entite';
import { Matiere } from '../../core/enums';
import { environment } from '../../../environments/environment';

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
export class StatistiquesRepository {
  private readonly http = inject(HttpClient);

  obtenirStatistiques(etablissementId: string): Observable<StatistiquesUtilisation> {
    return this.http.get<any>(`${environment.apiUrl}/statistiques`).pipe(
      map(data => {
        const matieres: MatiereStats[] = (data?.repartitionMatieres || []).map((m: any) => ({
          matiere: parseMatiere(m.matiere),
          pourcentage: m.pourcentage,
          totalQuestions: Math.round((data.totalInteractions || 100) * (m.pourcentage / 100)),
          tempsTotal: Math.round((data.totalHeuresApprentissage || 10) * (m.pourcentage / 100) * 60),
        }));

        const hebdo: number[] = (data?.progressionHebdomadaire || []).map((p: any) => p.interactions || 15);

        return {
          etablissementId: etablissementId || 'etab-lbad-bamako',
          periode: 'semaine',
          totalQuestionsIA: data?.totalInteractions || 120,
          tempsTotal: Math.round((data?.totalHeuresApprentissage || 15) * 60),
          apprenantActifs: 3,
          tauxEngagement: Math.round(data?.tauxSatisfaction || 92),
          matieresPlusUtilisees: matieres,
          pictUtilisation: [
            { heure: 8, nombreSessions: 12 },
            { heure: 10, nombreSessions: 28 },
            { heure: 14, nombreSessions: 35 },
            { heure: 16, nombreSessions: 42 },
            { heure: 18, nombreSessions: 19 },
          ],
          activiteJournaliere: hebdo,
          activiteHebdomadaire: hebdo,
          evolutionMensuelle: [110, 140, 180, 220, 280, 310],
          dateGeneration: new Date(),
        };
      })
    );
  }

  obtenirNotionsDifficiles(etablissementId: string): Observable<NotionDifficile[]> {
    return this.http.get<any>(`${environment.apiUrl}/insights`).pipe(
      map(data => {
        const notions: any[] = data?.notionsCritiques || [];
        return notions.map((nc: any) => ({
          matiere: parseMatiere(nc.matiere),
          notion: nc.notion,
          tauxEchec: Math.round(100 - (nc.tauxReussite || 60)),
          nombreTentatives: nc.nombreQuestions || 24,
          apprenantsConcernes: 3,
        }));
      })
    );
  }

  obtenirRapports(etablissementId: string): Observable<RapportActivite[]> {
    return this.http.get<any>(`${environment.apiUrl}/statistiques`).pipe(
      map(data => [
        {
          id: 'rap-001',
          etablissementId: etablissementId || 'etab-lbad-bamako',
          titre: 'Bilan Hebdomadaire d\'Apprentissage ALTA',
          periode: 'Semaine en cours',
          dateDebut: new Date(Date.now() - 7 * 24 * 3600 * 1000),
          dateFin: new Date(),
          dateGeneration: new Date(),
          type: 'pdf',
          statut: 'genere',
          tailleFichier: 1024 * 450,
        },
        {
          id: 'rap-002',
          etablissementId: etablissementId || 'etab-lbad-bamako',
          titre: 'Rapport Mensuel des Notions Critiques (SVT & Maths)',
          periode: 'Mois en cours',
          dateDebut: new Date(Date.now() - 30 * 24 * 3600 * 1000),
          dateFin: new Date(),
          dateGeneration: new Date(),
          type: 'pdf',
          statut: 'genere',
          tailleFichier: 1024 * 820,
        },
      ])
    );
  }
}
