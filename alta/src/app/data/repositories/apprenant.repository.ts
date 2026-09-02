import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { Apprenant } from '../../domain/entites/etablissement.entite';
import { Matiere } from '../../core/enums';
import { environment } from '../../../environments/environment';

@Injectable({ providedIn: 'root' })
export class ApprenantRepository {
  private readonly http = inject(HttpClient);

  private mapDtoToApprenant(dto: any, index: number): Apprenant {
    return {
      id: dto.id,
      nom: dto.nom,
      prenom: dto.prenom,
      nomComplet: dto.nomComplet || `${dto.prenom} ${dto.nom}`,
      etablissementId: dto.etablissementId || 'etab-lbad-bamako',
      classe: dto.classe || '11eme',
      dateNaissance: new Date(2008, 5, 12),
      avatar: dto.photoUrl || `assets/avatars/eleve-${(index % 3) + 1}.png`,
      boitierId: dto.boitierId || 'box-alta-01',
      matieresFavorites: [Matiere.SVT, Matiere.MATHEMATIQUES, Matiere.PHYSIQUE],
      dateInscription: new Date(),
      derniereActivite: dto.dernierAcces ? new Date(dto.dernierAcces) : new Date(),
      actif: true,
      progression: Math.round(dto.niveauMaitrise ?? 75),
    };
  }

  obtenirTous(etablissementId: string): Observable<Apprenant[]> {
    return this.http.get<any[]>(`${environment.apiUrl}/apprenants`).pipe(
      map(list => (list || []).map((dto, idx) => this.mapDtoToApprenant(dto, idx)))
    );
  }

  obtenirParId(id: string): Observable<Apprenant | undefined> {
    return this.http.get<any>(`${environment.apiUrl}/apprenants/${id}`).pipe(
      map(dto => dto ? this.mapDtoToApprenant(dto, 0) : undefined)
    );
  }

  rechercher(terme: string): Observable<Apprenant[]> {
    const termeNorm = terme.toLowerCase();
    return this.obtenirTous('').pipe(
      map(list => list.filter(a =>
        a.nomComplet.toLowerCase().includes(termeNorm) ||
        a.classe.toLowerCase().includes(termeNorm)
      ))
    );
  }

  obtenirActifs(): Observable<Apprenant[]> {
    return this.obtenirTous('').pipe(
      map(list => list.filter(a => a.actif))
    );
  }

  creerApprenant(data: { nom: string; prenom: string; classe: string; serie?: string; boitierId?: string }): Observable<Apprenant> {
    return this.http.post<any>(`${environment.apiUrl}/apprenants`, {
      nom: data.nom,
      prenom: data.prenom,
      classe: data.classe,
      serie: data.serie || 'generale',
      boitier_id: data.boitierId || null,
    }).pipe(map((dto) => this.mapDtoToApprenant(dto, 0)));
  }

  supprimerApprenant(apprenantId: string): Observable<any> {
    return this.http.delete<any>(`${environment.apiUrl}/apprenants/${apprenantId}`);
  }
}
