import {Component, inject} from "@angular/core";
import {CommonModule} from "@angular/common";
import {Router, RouterModule} from "@angular/router";
import {TranslateModule} from "@ngx-translate/core";
import {MatTooltipModule} from "@angular/material/tooltip";
import {PipelineService} from "../../services/config/pipeline.service";
import {PipelineStep} from "../../services/config/pipeline.config";

@Component({
    selector: "app-pipeline-step-bar",
    standalone: true,
    imports: [CommonModule, RouterModule, TranslateModule, MatTooltipModule],
    templateUrl: "./pipeline-step-bar.component.html",
    styleUrl: "./pipeline-step-bar.component.scss"
})
export class PipelineStepBarComponent {
    private router = inject(Router);
    private pipelineService = inject(PipelineService);

    readonly steps = this.pipelineService.steps;
    readonly currentStep$ = this.pipelineService.currentStep$;

    goHome(): void {
        this.router.navigate(["/dashboard"]);
    }

    goToStep(step: PipelineStep): void {
        if (step.enabled && step.primaryRoute) {
            this.router.navigate([step.primaryRoute]);
        }
    }
}
