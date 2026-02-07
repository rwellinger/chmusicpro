import {Component, inject, Input} from "@angular/core";
import {CommonModule} from "@angular/common";
import {MatTooltipModule} from "@angular/material/tooltip";
import {TranslateModule, TranslateService} from "@ngx-translate/core";
import {DeviceService} from "../../services/ui/device.service";

@Component({
    selector: "app-info-tooltip",
    standalone: true,
    imports: [CommonModule, MatTooltipModule, TranslateModule],
    template: `
    <i class="fas fa-info-circle info-tooltip-icon"
       [matTooltip]="tooltipText"
       [matTooltipPosition]="'above'"
       [matTooltipShowDelay]="300"
       [matTooltipHideDelay]="0"
       [matTooltipClass]="'info-tooltip-content'"
       (click)="onTouch($event)">
    </i>
  `,
    styleUrls: ["./info-tooltip.component.scss"]
})
export class InfoTooltipComponent {
    @Input() text!: string;
    @Input() translateKey: boolean = true;

    private translate = inject(TranslateService);
    private deviceService = inject(DeviceService);

    get tooltipText(): string {
        return this.translateKey
            ? this.translate.instant(this.text)
            : this.text;
    }

    onTouch(event: Event): void {
        if (this.deviceService.isTouchDevice) {
            event.stopPropagation();
        }
    }
}
