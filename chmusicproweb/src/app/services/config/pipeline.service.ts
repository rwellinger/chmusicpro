import {inject, Injectable} from "@angular/core";
import {NavigationEnd, Router} from "@angular/router";
import {combineLatest, filter, map, shareReplay, startWith} from "rxjs";
import {PIPELINE_STEPS, PipelineStep} from "./pipeline.config";
import {AIConfigService} from "./ai-config.service";

@Injectable({providedIn: "root"})
export class PipelineService {
    private router = inject(Router);
    private aiConfigService = inject(AIConfigService);

    readonly steps: PipelineStep[] = PIPELINE_STEPS;

    readonly currentStep$ = this.router.events.pipe(
        filter((event): event is NavigationEnd => event instanceof NavigationEnd),
        startWith({urlAfterRedirects: this.router.url} as NavigationEnd),
        map(event => this.findStep(event.urlAfterRedirects)),
        shareReplay(1)
    );

    private applicationMode$ = this.aiConfigService.getApplicationMode();

    readonly isOnPipelinePage$ = combineLatest([this.currentStep$, this.applicationMode$]).pipe(
        map(([step, mode]) => step !== null && mode !== "PRJCT")
    );

    readonly filteredSteps$ = this.applicationMode$.pipe(
        map(mode => mode === "PRJCT" ? this.steps.filter(s => s.step === 6) : this.steps)
    );

    private findStep(url: string): PipelineStep | null {
        return this.steps.find(step =>
            step.routes.some(route => url.startsWith(route))
        ) ?? null;
    }
}
