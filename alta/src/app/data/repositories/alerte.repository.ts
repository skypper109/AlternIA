import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { Alerte, TypeAlerte } from '../../domain/entites/alerte.entite';
import { environment } from '../../../environments/environment';

function parseTypeAlerte(typeStr: string): TypeAlerte {
  const t = (typeStr || '').toLowerCase();
  if (t.includes('difficulte') || t.includes('recurrente')) return TypeAlerte.REVISION_RECOMMANDEE;
  if (t.includes('inactivite') || t.includes('faible')) return TypeAlerte.FAIBLE_ACTIVITE;
  if (t.includes('reussite') || t.includes('progression')) return TypeAlerte.PROGRESSION_REMARQUABLE;
  return TypeAlerte.REVISION_RECOMMANDEE;
}

@Injectable({ providedIn: 'root' })
export class AlerteRepository {
  private readonly http = inject(HttpClient);

  obtenirAlertesParent(parentId: string): Observable<Alerte[]> {
    return this.http.get<any[]>(`${environment.apiUrl}/alertes`).pipe(
      map(list => {
        return (list || []).map(a => {
          const priorite: 'basse' | 'normale' | 'haute' =
            a.gravite === 'elevee' ? 'haute' :
            a.gravite === 'faible' ? 'basse' : 'normale';

          return {
            id: a.id,
            parentId: parentId || 'parent-1',
            enfantId: a.apprenantId || 'enfant-1',
            titre: a.titre,
            message: a.description,
            type: parseTypeAlerte(a.type),
            priorite,
            lue: a.resolu ?? false,
            dateCreation: a.dateCreation ? new Date(a.dateCreation) : new Date(),
          };
        });
      })
    );
  }

  marquerCommeLue(alerteId: string): Observable<boolean> {
    return this.http.put<any>(`${environment.apiUrl}/alertes/${alerteId}/resoudre`, {}).pipe(
      map(() => true)
    );
  }
}
