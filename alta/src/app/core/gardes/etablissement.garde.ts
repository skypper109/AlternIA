import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { RoleUtilisateur } from '../enums';
import { ROUTES_APP } from '../constantes/routes.constantes';

export const etablissementGarde: CanActivateFn = () => {
  const authService = inject(AuthService);
  const router = inject(Router);
  const utilisateur = authService.utilisateurCourant();

  if (utilisateur && utilisateur.role === RoleUtilisateur.ADMIN_ECOLE) {
    return true;
  }
  return router.createUrlTree([ROUTES_APP.AUTH.CONNEXION]);
};
