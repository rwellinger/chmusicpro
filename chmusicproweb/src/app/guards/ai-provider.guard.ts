import {inject} from "@angular/core";
import {CanActivateFn, Router} from "@angular/router";
import {map} from "rxjs";
import {AIConfigService} from "../services/config/ai-config.service";

export function aiProviderGuard(requiredProvider: "ollama" | "external"): CanActivateFn {
    return () => {
        const aiConfigService = inject(AIConfigService);
        const router = inject(Router);

        return aiConfigService.getConfig().pipe(
            map(config => {
                if (requiredProvider === "ollama" && config.ollama_enabled) {
                    return true;
                }
                if (requiredProvider === "external" && config.external_enabled) {
                    return true;
                }
                return router.createUrlTree(["/"]);
            })
        );
    };
}
