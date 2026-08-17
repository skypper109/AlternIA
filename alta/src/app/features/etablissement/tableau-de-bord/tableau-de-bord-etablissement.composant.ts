import { Component, OnInit, signal, inject, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { StatistiquesRepository } from '../../../data/repositories/statistiques.repository';
import { ApprenantRepository } from '../../../data/repositories/apprenant.repository';
import { BoitierRepository } from '../../../data/repositories/boitier.repository';
import { StatistiquesUtilisation, NotionDifficile } from '../../../domain/entites/statistiques-utilisation.entite';
import { Apprenant } from '../../../domain/entites/etablissement.entite';
import { Boitier } from '../../../domain/entites/boitier.entite';
import { StatutBoitier, Matiere, MatiereLabels, MatiereCouleurs } from '../../../core/enums';

import { Router, RouterLink } from '@angular/router';
import { NotificationService } from '../../../core/services/notification.service';

@Component({
  selector: 'app-tableau-de-bord-etablissement',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './tableau-de-bord-etablissement.composant.html',
  styleUrl: './tableau-de-bord-etablissement.composant.scss',
})
export class TableauDeBordEtablissementComposant implements OnInit {
  private readonly statsRepo = inject(StatistiquesRepository);
  private readonly apprenantRepo = inject(ApprenantRepository);
  private readonly boitierRepo = inject(BoitierRepository);
  private readonly router = inject(Router);
  private readonly notifService = inject(NotificationService);

  readonly Math = Math;
  readonly MatiereLabels = MatiereLabels;
  readonly MatiereCouleurs = MatiereCouleurs;
  readonly StatutBoitier = StatutBoitier;

  chargement = signal(true);
  stats = signal<StatistiquesUtilisation | null>(null);
  apprenants = signal<Apprenant[]>([]);
  boitiers = signal<Boitier[]>([]);
  periodeActive = signal<'7j' | '30j'>('7j');
  typeGraphique = signal<'barres' | 'courbe'>('barres');
  jourSurvole = signal<{ index: number; jour: string; valeur: number; diffMoyenne: number } | null>(null);

  readonly apprenantActifs = computed(() => this.apprenants().filter(a => a.actif).length);
  readonly boitiersEnLigne = computed(() => this.boitiers().filter(b => b.statut === StatutBoitier.EN_LIGNE_CLOUD).length);
  readonly boitiersHorsLigne = computed(() => this.boitiers().filter(b => b.statut === StatutBoitier.HORS_LIGNE_LOCAL).length);
  readonly boitiersDeconnectes = computed(() => this.boitiers().filter(b => b.statut === StatutBoitier.DECONNECTE).length);

  readonly tempsFormatte = computed(() => {
    const minutes = this.stats()?.tempsTotal ?? 0;
    const heures = Math.floor(minutes / 60);
    return `${heures.toLocaleString('fr-FR')}h`;
  });

  readonly donneesActives = computed(() => {
    return this.periodeActive() === '7j' 
      ? (this.stats()?.activiteJournaliere ?? [320, 410, 395, 465, 488, 342, 290])
      : (this.stats()?.activiteHebdomadaire ?? [1820, 2240, 2150, 2610, 2380, 1940, 2100, 2450]);
  });

  readonly labelsActifs = computed(() => {
    return this.periodeActive() === '7j' ? this.joursSemaine : this.semainesHebdo;
  });

  readonly totalActivitePeriode = computed(() => {
    return this.donneesActives().reduce((acc, v) => acc + v, 0);
  });

  readonly moyenneActivitePeriode = computed(() => {
    const data = this.donneesActives();
    return data.length ? Math.round(this.totalActivitePeriode() / data.length) : 0;
  });

  readonly indexPic = computed(() => {
    const data = this.donneesActives();
    if (!data.length) return -1;
    const max = Math.max(...data);
    return data.indexOf(max);
  });

  readonly jourPicNom = computed(() => {
    const idx = this.indexPic();
    return idx >= 0 ? this.labelsActifs()[idx] : '';
  });

  readonly valeurPic = computed(() => {
    const idx = this.indexPic();
    const data = this.donneesActives();
    return idx >= 0 ? data[idx] : 0;
  });

  readonly chartPointsSvg = computed(() => {
    const data = this.donneesActives();
    const labels = this.labelsActifs();
    if (!data.length) return [];
    const max = Math.max(...data) * 1.15;
    const min = Math.min(...data) * 0.85;
    const range = (max - min) || 1;
    const width = 460;
    const height = 170;
    const paddingX = 20;

    return data.map((v, i) => {
      const x = paddingX + (i / (data.length - 1)) * (width - 2 * paddingX);
      const y = height - ((v - min) / range) * (height - 30);
      return { x, y, val: v, label: labels[i] };
    });
  });

  semaineSurvolee = signal<{
    index: number;
    label: string;
    valeur: number;
    diffMoy: number;
    x: number;
    y: number;
  } | null>(null);

  readonly labelsHebdo4Sem = ['Sem 1', 'Sem 2', 'Sem 3', 'Sem 4'];

  readonly donneesHebdo4Sem = computed(() => {
    const raw = this.stats()?.activiteHebdomadaire ?? [1940, 2150, 2380, 2610];
    return raw.slice(-4);
  });

  readonly totalActiviteHebdo = computed(() => {
    return this.donneesHebdo4Sem().reduce((acc, val) => acc + val, 0);
  });

  readonly moyenneHebdo = computed(() => {
    const data = this.donneesHebdo4Sem();
    return data.length ? Math.round(this.totalActiviteHebdo() / data.length) : 0;
  });

  readonly indexPicHebdo = computed(() => {
    const data = this.donneesHebdo4Sem();
    if (!data.length) return -1;
    const max = Math.max(...data);
    return data.indexOf(max);
  });

  readonly croissanceHebdo = computed(() => {
    const data = this.donneesHebdo4Sem();
    if (data.length < 2) return 0;
    const first = data[0];
    const last = data[data.length - 1];
    return first > 0 ? Math.round(((last - first) / first) * 100) : 0;
  });

  readonly hebdoMaxScale = computed(() => {
    const data = this.donneesHebdo4Sem();
    const max = Math.max(...data, 1000);
    return Math.ceil((max * 1.12) / 500) * 500;
  });

  readonly hebdoGridLines = computed(() => {
    const max = this.hebdoMaxScale();
    const count = 3;
    const lines = [];
    for (let i = 0; i <= count; i++) {
      const val = Math.round(max * (1 - i / count));
      const y = 15 + i * (110 / count);
      lines.push({ val, y, label: val >= 1000 ? `${(val / 1000).toFixed(1)}k` : `${val}` });
    }
    return lines;
  });

  readonly hebdoAvgY = computed(() => {
    const max = this.hebdoMaxScale();
    const moy = this.moyenneHebdo();
    return 125 - (moy / max) * 110;
  });

  readonly pointsHebdoSvg = computed(() => {
    const data = this.donneesHebdo4Sem();
    const labels = this.labelsHebdo4Sem;
    if (!data.length) return [];
    const max = this.hebdoMaxScale();
    const width = 360;
    const paddingX = 35;
    const plotWidth = width - paddingX - 10;
    const plotHeight = 110;
    const topY = 15;

    return data.map((v, i) => {
      const x = paddingX + (i / (data.length - 1)) * plotWidth;
      const y = (topY + plotHeight) - (v / max) * plotHeight;
      const diffMoy = this.moyenneHebdo() > 0 ? Math.round(((v - this.moyenneHebdo()) / this.moyenneHebdo()) * 100) : 0;
      return {
        x,
        y,
        val: v,
        label: labels[i],
        diffMoy,
        isPeak: i === this.indexPicHebdo()
      };
    });
  });

  readonly hebdoCurvePath = computed(() => {
    const pts = this.pointsHebdoSvg();
    if (!pts.length) return '';
    if (pts.length === 1) return `M ${pts[0].x} ${pts[0].y}`;

    let path = `M ${pts[0].x.toFixed(1)} ${pts[0].y.toFixed(1)}`;
    for (let i = 0; i < pts.length - 1; i++) {
      const p0 = pts[i === 0 ? i : i - 1];
      const p1 = pts[i];
      const p2 = pts[i + 1];
      const p3 = pts[i + 2 < pts.length ? i + 2 : i + 1];

      const cp1x = p1.x + (p2.x - p0.x) / 5;
      const cp1y = p1.y + (p2.y - p0.y) / 5;

      const cp2x = p2.x - (p3.x - p1.x) / 5;
      const cp2y = p2.y - (p3.y - p1.y) / 5;

      path += ` C ${cp1x.toFixed(1)} ${cp1y.toFixed(1)}, ${cp2x.toFixed(1)} ${cp2y.toFixed(1)}, ${p2.x.toFixed(1)} ${p2.y.toFixed(1)}`;
    }
    return path;
  });

  readonly hebdoAreaPath = computed(() => {
    const pts = this.pointsHebdoSvg();
    if (!pts.length) return '';
    const curve = this.hebdoCurvePath();
    const first = pts[0];
    const last = pts[pts.length - 1];
    const bottomY = 125;
    return `${curve} L ${last.x.toFixed(1)} ${bottomY} L ${first.x.toFixed(1)} ${bottomY} Z`;
  });

  survolerSemaine(index: number): void {
    const pts = this.pointsHebdoSvg();
    if (pts[index]) {
      const p = pts[index];
      this.semaineSurvolee.set({
        index,
        label: p.label,
        valeur: p.val,
        diffMoy: p.diffMoy,
        x: p.x,
        y: p.y
      });
    }
  }

  quitterSurvolSemaine(): void {
    this.semaineSurvolee.set(null);
  }

  readonly svgCurvePath = computed(() => {
    const pts = this.chartPointsSvg();
    if (!pts.length) return '';
    return 'M ' + pts.map(p => `${p.x} ${p.y}`).join(' L ');
  });

  readonly svgCurveAreaPath = computed(() => {
    const pts = this.chartPointsSvg();
    if (!pts.length) return '';
    const first = pts[0];
    const last = pts[pts.length - 1];
    return `M ${first.x} 180 L ${first.x} ${first.y} ` + pts.map(p => `L ${p.x} ${p.y}`).join(' ') + ` L ${last.x} 180 Z`;
  });

  ngOnInit(): void {
    Promise.all([
      new Promise<void>(resolve => {
        this.statsRepo.obtenirStatistiques('etab-1').subscribe(s => {
          this.stats.set(s);
          resolve();
        });
      }),
      new Promise<void>(resolve => {
        this.apprenantRepo.obtenirTous('etab-1').subscribe(a => {
          this.apprenants.set(a);
          resolve();
        });
      }),
      new Promise<void>(resolve => {
        this.boitierRepo.obtenirBoitiersEtablissement('etab-1').subscribe(b => {
          this.boitiers.set(b);
          resolve();
        });
      }),
    ]).then(() => this.chargement.set(false));
  }

  formatterMinutes(minutes: number): string {
    const h = Math.floor(minutes / 60);
    const m = minutes % 60;
    return h > 0 ? `${h}h${m > 0 ? m + 'min' : ''}` : `${m}min`;
  }

  getStatutLabel(statut: StatutBoitier): string {
    const labels = {
      [StatutBoitier.EN_LIGNE_CLOUD]: 'En ligne',
      [StatutBoitier.HORS_LIGNE_LOCAL]: 'Hors ligne',
      [StatutBoitier.DECONNECTE]: 'Déconnecté',
    };
    return labels[statut];
  }

  getStatutClass(statut: StatutBoitier): string {
    const classes = {
      [StatutBoitier.EN_LIGNE_CLOUD]: 'online',
      [StatutBoitier.HORS_LIGNE_LOCAL]: 'warning',
      [StatutBoitier.DECONNECTE]: 'danger',
    };
    return classes[statut];
  }

  getBarHeight(value: number, max: number): number {
    return Math.max(8, (value / max) * 100);
  }

  getMaxActivite(): number {
    const data = this.donneesActives();
    return Math.max(...data, 1);
  }

  getMaxHebdo(): number {
    const data = this.stats()?.activiteHebdomadaire ?? [];
    return data.length ? Math.max(...data, 1) : 1;
  }

  generateLinePath(data?: number[]): string {
    if (!data || data.length === 0) return '';
    const max = this.getMaxHebdo();
    return data.reduce((acc, val, i) => {
      const x = (i / (data.length - 1)) * 400;
      const y = 180 - (val / max) * 160;
      return i === 0 ? `M ${x} ${y}` : `${acc} L ${x} ${y}`;
    }, '');
  }

  generateAreaPath(data?: number[]): string {
    if (!data || data.length === 0) return '';
    const linePath = this.generateLinePath(data);
    return `${linePath} L 400 180 L 0 180 Z`;
  }

  readonly joursSemaine = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'];
  readonly joursSemaineCourt = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'];
  readonly semainesHebdo = ['Sem 1', 'Sem 2', 'Sem 3', 'Sem 4', 'Sem 5', 'Sem 6', 'Sem 7', 'Sem 8'];

  survolerBarre(valeur: number, index: number): void {
    const jour = this.labelsActifs()[index];
    const moy = this.moyenneActivitePeriode();
    const diff = moy > 0 ? Math.round(((valeur - moy) / moy) * 100) : 0;
    this.jourSurvole.set({ index, jour, valeur, diffMoyenne: diff });
  }

  quitterSurvol(): void {
    this.jourSurvole.set(null);
  }

  exporterStats(): void {
    const csvContent = "Matière,TotalQuestions,TempsTotalMinutes\n" +
      (this.stats()?.matieresPlusUtilisees.map(m => `"${MatiereLabels[m.matiere]}",${m.totalQuestions},${m.tempsTotal}`).join('\n') || '');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `statistiques_etablissement_mali_${Date.now()}.csv`;
    link.click();

    this.notifService.succes('Exportation réussie', 'Les statistiques de l\'établissement ont été exportées en CSV.');
  }

  genererRapport(): void {
    this.router.navigate(['/etablissement/rapports']);
    this.notifService.info('Redirection', 'Accès à la page de génération de rapports.');
  }

  setPeriode(p: '7j' | '30j'): void {
    this.periodeActive.set(p);
  }

  setTypeGraphique(t: 'barres' | 'courbe'): void {
    this.typeGraphique.set(t);
  }
}
