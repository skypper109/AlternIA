import { Component, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { ROUTES_APP } from '../../../core/constantes/routes.constantes';
import { NotificationService } from '../../../core/services/notification.service';

@Component({
  selector: 'app-connexion',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './connexion.composant.html',
  styleUrl: './connexion.composant.scss',
})
export class ConnexionComposant {
  private readonly fb = inject(FormBuilder);
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);
  private readonly notifService = inject(NotificationService);

  readonly routes = ROUTES_APP;

  profilChoisi = signal<'etablissement' | 'parent' | null>(null);
  chargement = signal(false);
  erreur = signal<string | null>(null);
  motDePasseVisible = signal(false);

  formulaire = this.fb.group({
    email: ['', [Validators.required, Validators.email]],
    motDePasse: ['', [Validators.required, Validators.minLength(6)]],
  });

  choisirProfil(profil: 'etablissement' | 'parent'): void {
    this.profilChoisi.set(profil);
    this.erreur.set(null);
    if (profil === 'etablissement') {
      this.formulaire.patchValue({ email: 'directeur@altern.ia', motDePasse: 'alternia2026' });
    } else {
      this.formulaire.patchValue({ email: 'parent@altern.ia', motDePasse: 'alternia2026' });
    }
  }

  retourChoixProfil(): void {
    this.profilChoisi.set(null);
    this.formulaire.reset();
    this.erreur.set(null);
  }

  basculerMotDePasse(): void {
    this.motDePasseVisible.update(v => !v);
  }

  motDePasseOublie(event: Event): void {
    event.preventDefault();
    const emailSaisi = this.formulaire.value.email;
    if (emailSaisi) {
      this.notifService.succes('Réinitialisation envoyée', `Un lien de réinitialisation de mot de passe a été envoyé à ${emailSaisi}.`);
    } else {
      this.notifService.info('Réinitialisation', 'Saisissez votre adresse email puis cliquez sur "Mot de passe oublié ?" pour recevoir les instructions.');
    }
  }

  async seConnecter(): Promise<void> {
    if (this.formulaire.invalid) {
      this.formulaire.markAllAsTouched();
      return;
    }
    this.chargement.set(true);
    this.erreur.set(null);

    try {
      const { email, motDePasse } = this.formulaire.value;
      await this.authService.connexion(email!, motDePasse!);
      this.authService.redirectionSelonRole();
    } catch {
      this.erreur.set('Email ou mot de passe incorrect. Veuillez réessayer.');
    } finally {
      this.chargement.set(false);
    }
  }

  get emailControl() { return this.formulaire.get('email'); }
  get motDePasseControl() { return this.formulaire.get('motDePasse'); }
}
