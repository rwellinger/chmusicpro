import {inject, Injectable} from "@angular/core";
import {NavigationEnd, Router} from "@angular/router";
import {filter, map, startWith} from "rxjs";
import {PIPELINE_STEPS, PipelineStep} from "./pipeline.config";

@Injectable({providedIn: "root"})
export class PipelineService {
    private router = inject(Router);

    readonly steps: PipelineStep[] = PIPELINE_STEPS;

    readonly currentStep$ = this.router.events.pipe(
        filter((event): event is NavigationEnd => event instanceof NavigationEnd),
        startWith({urlAfterRedirects: this.router.url} as NavigationEnd),
        map(event => this.findStep(event.urlAfterRedirects))
    );

    readonly isOnPipelinePage$ = this.currentStep$.pipe(
        map(step => step !== null)
    );

    private findStep(url: string): PipelineStep | null {
        return this.steps.find(step =>
            step.routes.some(route => url.startsWith(route))
        ) ?? null;
    }
}
