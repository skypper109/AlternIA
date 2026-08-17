import { Injectable, signal } from '@angular/core';

export interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  titre: string;
  message?: string;
  duree?: number;
}

@Injectable({ providedIn: 'root' })
export class NotificationService {
  private _notifications = signal<Notification[]>([]);
  readonly notifications = this._notifications.asReadonly();

  afficher(notif: Omit<Notification, 'id'>): void {
    const id = crypto.randomUUID();
    const notification: Notification = { id, duree: 4000, ...notif };
    this._notifications.update(list => [...list, notification]);

    setTimeout(() => this.supprimer(id), notification.duree);
  }

  succes(titre: string, message?: string): void {
    this.afficher({ type: 'success', titre, message });
  }

  erreur(titre: string, message?: string): void {
    this.afficher({ type: 'error', titre, message, duree: 6000 });
  }

  avertissement(titre: string, message?: string): void {
    this.afficher({ type: 'warning', titre, message });
  }

  info(titre: string, message?: string): void {
    this.afficher({ type: 'info', titre, message });
  }

  supprimer(id: string): void {
    this._notifications.update(list => list.filter(n => n.id !== id));
  }
}
