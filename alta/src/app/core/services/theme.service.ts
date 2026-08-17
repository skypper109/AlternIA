import { Injectable, signal } from '@angular/core';

type Theme = 'light' | 'dark';
const THEME_KEY = 'alternia_theme';

@Injectable({ providedIn: 'root' })
export class ThemeService {
  private _theme = signal<Theme>(this.chargerTheme());
  readonly theme = this._theme.asReadonly();

  basculerTheme(): void {
    const nouveau = this._theme() === 'light' ? 'dark' : 'light';
    this.appliquerTheme(nouveau);
  }

  definirTheme(theme: Theme): void {
    this.appliquerTheme(theme);
  }

  get estModeNuit(): boolean {
    return this._theme() === 'dark';
  }

  private appliquerTheme(theme: Theme): void {
    this._theme.set(theme);
    localStorage.setItem(THEME_KEY, theme);
    document.documentElement.classList.toggle('dark', theme === 'dark');
    document.documentElement.classList.toggle('light', theme === 'light');
  }

  private chargerTheme(): Theme {
    const saved = localStorage.getItem(THEME_KEY) as Theme | null;
    if (saved) {
      document.documentElement.classList.add(saved);
      return saved;
    }
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const theme: Theme = prefersDark ? 'dark' : 'light';
    document.documentElement.classList.add(theme);
    return theme;
  }
}
