import {inject} from "@angular/core";
import {CanActivateFn, Router} from "@angular/router";
import {AuthService} from "../services/business/auth.service";

export const domainRoleGuard: CanActivateFn = (route) => {
    const authService = inject(AuthService);
    const router = inject(Router);
    const requiredRoles: string[] = route.data["requiredDomainRoles"] || ["owner", "admin"];
    const currentRole = authService.getDomainRole();

    if (currentRole && requiredRoles.includes(currentRole)) {
        return true;
    }

    router.navigate(["/dashboard"]);
    return false;
};
