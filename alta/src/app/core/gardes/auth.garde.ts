import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { ROUTES_APP } from '../constantes/routes.constantes';

export const authGarde: CanActivateFn = () => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (authService.estConnecte()) {
    return true;
  }
  return router.createUrlTree([ROUTES_APP.AUTH.CONNEXION]);
};
