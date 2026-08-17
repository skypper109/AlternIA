import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { Boitier } from '../../domain/entites/boitier.entite';
import { StatutBoitier } from '../../core/enums';
import { environment } from '../../../environments/environment';

@Injectable({ providedIn: 'root' })
export class BoitierRepository {
  private readonly http = inject(HttpClient);

  private mapDtoToBoitier(dto: any): Boitier {
    return {
      id: dto.id,
      codeUnique: dto.numeroSerie || dto.codeUnique || 'ALT-BOX-2026-001',
      nom: dto.modele || dto.nom || 'AlternIA Box',
      modele: dto.modele || 'AlternIA Box v2.0',
      statut: (dto.statut === 'en_ligne' ? StatutBoitier.EN_LIGNE_CLOUD :
               dto.statut === 'hors_ligne' ? StatutBoitier.HORS_LIGNE_LOCAL :
               StatutBoitier.DECONNECTE),
      niveauBatterie: dto.batterie ?? 95,
      versionFirmware: dto.firmware || 'v2.0-LocalEdge',
      derniereSync: dto.derniereSynchro ? new Date(dto.derniereSynchro) : new Date(),
      espaceUtilise: Math.round((dto.stockageUtiliseGo ?? 8.4) * 1024),
      espaceTotal: Math.round((dto.stockageGo ?? 32) * 1024),
      wifiConnecte: dto.statut === 'en_ligne',
      ssid: dto.wifiSsid || 'AlternIA-Box-WiFi',
      etablissementId: dto.etablissementId,
      enfantId: dto.enfantId,
      dateActivation: dto.dateActivation ? new Date(dto.dateActivation) : new Date(),
    };
  }

  obtenirTous(): Observable<Boitier[]> {
    return this.http.get<any[]>(`${environment.apiUrl}/boitiers`).pipe(
      map(list => (list || []).map(b => this.mapDtoToBoitier(b)))
    );
  }

  obtenirBoitierParEnfant(enfantId: string): Observable<Boitier | undefined> {
    return this.http.get<any[]>(`${environment.apiUrl}/boitiers`).pipe(
      map(list => {
        if (!list || list.length === 0) return undefined;
        const found = list.find(b => b.enfantId === enfantId) || list[0];
        return found ? this.mapDtoToBoitier(found) : undefined;
      })
    );
  }

  obtenirBoitiersEtablissement(etablissementId: string): Observable<Boitier[]> {
    return this.http.get<any[]>(`${environment.apiUrl}/boitiers`).pipe(
      map(list => (list || []).map(b => this.mapDtoToBoitier(b)))
    );
  }

  obtenirBoitierParId(id: string): Observable<Boitier | undefined> {
    return this.http.get<any>(`${environment.apiUrl}/boitiers/${id}`).pipe(
      map(b => b ? this.mapDtoToBoitier(b) : undefined)
    );
  }

  synchroniser(boitierId: string): Observable<any> {
    return this.http.post<any>(`${environment.apiUrl}/boitiers/${boitierId}/sync`, { force: true });
  }

  configurerWifi(boitierId: string, ssid: string, motDePasse?: string): Observable<any> {
    return this.http.post<any>(`${environment.apiUrl}/boitiers/${boitierId}/wifi`, {
      ssid,
      mot_de_passe: motDePasse || null,
    });
  }
}
