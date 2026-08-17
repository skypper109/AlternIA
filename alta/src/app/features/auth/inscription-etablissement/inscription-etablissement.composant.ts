import { Component, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { ROUTES_APP } from '../../../core/constantes/routes.constantes';
import { NotificationService } from '../../../core/services/notification.service';

@Component({
  selector: 'app-inscription-etablissement',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './inscription-etablissement.composant.html',
  styleUrl: './inscription-etablissement.composant.scss',
})
export class InscriptionEtablissementComposant {
  private readonly fb = inject(FormBuilder);
  private readonly notifService = inject(NotificationService);
  readonly routes = ROUTES_APP;

  chargement = signal(false);
  succes = signal(false);
  messageErreur = signal<string | null>(null);
  afficherMdp = signal(false);
  afficherConfMdp = signal(false);

  formulaire = this.fb.group({
    nomEtablissement: ['', [Validators.required, Validators.minLength(3)]],
    ville: ['', [Validators.required]],
    email: ['', [Validators.required, Validators.email]],
    telephone: [''],
    motDePasse: ['', [Validators.required, Validators.minLength(8)]],
    confirmationMotDePasse: ['', [Validators.required]],
  }, { validators: this.passwordsMatch });

  private passwordsMatch(group: any) {
    const mdp = group.get('motDePasse')?.value;
    const conf = group.get('confirmationMotDePasse')?.value;
    return mdp === conf ? null : { passwordMismatch: true };
  }

  toggleAfficherMdp(): void {
    this.afficherMdp.update(v => !v);
  }

  toggleAfficherConfMdp(): void {
    this.afficherConfMdp.update(v => !v);
  }

  async sInscrire(): Promise<void> {
    this.messageErreur.set(null);

    if (this.formulaire.invalid) {
      this.formulaire.markAllAsTouched();
      if (this.formulaire.hasError('passwordMismatch')) {
        this.messageErreur.set('Les mots de passe ne correspondent pas.');
      } else {
        this.messageErreur.set('Veuillez remplir correctement tous les champs obligatoires.');
      }
      return;
    }

    this.chargement.set(true);
    await new Promise(r => setTimeout(r, 1200));
    this.chargement.set(false);
    this.succes.set(true);
    this.notifService.succes('Compte créé', 'Votre établissement a été enregistré avec succès.');
  }
}
