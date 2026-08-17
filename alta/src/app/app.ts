import { Component, OnInit, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { CommonModule } from '@angular/common';
import { ThemeService } from './core/services/theme.service';
import { NotificationService, Notification } from './core/services/notification.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, CommonModule],
  template: `
    <router-outlet/>

    <!-- Global Toast Notifications -->
    <div class="toast-container" aria-live="polite" aria-atomic="false">
      @for (notif of notifications(); track notif.id) {
        <div class="toast" [class]="'toast--' + notif.type" role="alert">
          <div class="toast__icon">
            @switch (notif.type) {
              @case ('success') {
                <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                  <path d="M3.5 9.5L7 13L14.5 5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              }
              @case ('error') {
                <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                  <path d="M4.5 4.5L13.5 13.5M13.5 4.5L4.5 13.5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                </svg>
              }
              @case ('warning') {
                <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                  <path d="M9 2L16.5 15.5H1.5L9 2Z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/>
                  <path d="M9 7V10.5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                  <circle cx="9" cy="13" r="0.8" fill="currentColor"/>
                </svg>
              }
              @case ('info') {
                <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                  <circle cx="9" cy="9" r="7" stroke="currentColor" stroke-width="1.8"/>
                  <path d="M9 8.5V13" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                  <circle cx="9" cy="5.5" r="0.8" fill="currentColor"/>
                </svg>
              }
            }
          </div>
          <div class="toast__content">
            <div class="toast__titre">{{ notif.titre }}</div>
            @if (notif.message) {
              <div class="toast__message">{{ notif.message }}</div>
            }
          </div>
          <button class="toast__close" (click)="fermerToast(notif.id)" [attr.aria-label]="'Fermer la notification'">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path d="M3 3L11 11M11 3L3 11" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
          </button>
        </div>
      }
    </div>
  `,
  styles: [`
    :host { display: block; }

    .toast-container {
      position: fixed;
      bottom: 24px;
      right: 24px;
      z-index: var(--z-toast, 700);
      display: flex;
      flex-direction: column;
      gap: 10px;
      max-width: 380px;
      width: 100%;
      pointer-events: none;
    }

    .toast {
      display: flex;
      align-items: flex-start;
      gap: 12px;
      padding: 14px 16px;
      border-radius: 12px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.12), 0 2px 8px rgba(0,0,0,0.08);
      animation: slideInRight 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
      pointer-events: all;
      backdrop-filter: blur(16px);
      border: 1px solid;

      &--success {
        background: rgba(240, 253, 244, 0.95);
        border-color: rgba(16, 185, 129, 0.3);
        color: #065f46;
        html.dark & { background: rgba(6, 78, 59, 0.9); border-color: rgba(16,185,129,0.4); color: #a7f3d0; }
      }
      &--error {
        background: rgba(254, 242, 242, 0.95);
        border-color: rgba(239, 68, 68, 0.3);
        color: #991b1b;
        html.dark & { background: rgba(127, 29, 29, 0.9); border-color: rgba(239,68,68,0.4); color: #fca5a5; }
      }
      &--warning {
        background: rgba(255, 251, 235, 0.95);
        border-color: rgba(245, 158, 11, 0.3);
        color: #92400e;
        html.dark & { background: rgba(78, 52, 11, 0.9); border-color: rgba(245,158,11,0.4); color: #fcd34d; }
      }
      &--info {
        background: rgba(239, 246, 255, 0.95);
        border-color: rgba(59, 130, 246, 0.3);
        color: #1e40af;
        html.dark & { background: rgba(30, 58, 138, 0.9); border-color: rgba(59,130,246,0.4); color: #93c5fd; }
      }
    }

    .toast__icon { font-size: 18px; flex-shrink: 0; line-height: 1; margin-top: 1px; }
    .toast__content { flex: 1; min-width: 0; }
    .toast__titre { font-size: 13px; font-weight: 600; font-family: var(--font-sans, 'Inter', sans-serif); line-height: 1.3; }
    .toast__message { font-size: 12px; margin-top: 2px; opacity: 0.8; line-height: 1.4; }
    .toast__close {
      flex-shrink: 0;
      background: none;
      border: none;
      cursor: pointer;
      opacity: 0.5;
      padding: 2px;
      border-radius: 4px;
      color: inherit;
      display: flex;
      align-items: center;
      transition: opacity 0.15s;
      &:hover { opacity: 1; }
    }

    @keyframes slideInRight {
      from { opacity: 0; transform: translateX(20px); }
      to { opacity: 1; transform: translateX(0); }
    }
  `],
})
export class App implements OnInit {
  private readonly themeService = inject(ThemeService);
  private readonly notificationService = inject(NotificationService);

  readonly notifications = this.notificationService.notifications;

  ngOnInit(): void {
    // ThemeService initializes on construction – no extra call needed
  }

  fermerToast(id: string): void {
    this.notificationService.supprimer(id);
  }
}
