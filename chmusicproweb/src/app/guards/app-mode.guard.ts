import {inject} from "@angular/core";
import {CanActivateFn, Router} from "@angular/router";
import {map} from "rxjs";
import {AIConfigService} from "../services/config/ai-config.service";
import {ApplicationMode} from "../models/ai-config.model";

export function appModeGuard(blockedModes: ApplicationMode[]): CanActivateFn {
    return () => {
        const aiConfigService = inject(AIConfigService);
        const router = inject(Router);

        return aiConfigService.getApplicationMode().pipe(
            map(mode => {
                if (blockedModes.includes(mode)) {
                    return router.createUrlTree(["/song-projects"]);
                }
                return true;
            })
        );
    };
}
