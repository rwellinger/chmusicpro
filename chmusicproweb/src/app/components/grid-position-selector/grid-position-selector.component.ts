import {Component, input, output} from "@angular/core";
import {CommonModule} from "@angular/common";

export type GridPosition =
    | "top-left"
    | "top-center"
    | "top-right"
    | "middle-left"
    | "center"
    | "middle-right"
    | "bottom-left"
    | "bottom-center"
    | "bottom-right";

@Component({
    selector: "app-grid-position-selector",
    standalone: true,
    imports: [CommonModule],
    templateUrl: "./grid-position-selector.component.html",
    styleUrl: "./grid-position-selector.component.scss"
})
export class GridPositionSelectorComponent {
    selectedPosition = input<GridPosition | null>(null);
    positionChange = output<GridPosition>();

    readonly positions: GridPosition[] = [
        "top-left", "top-center", "top-right",
        "middle-left", "center", "middle-right",
        "bottom-left", "bottom-center", "bottom-right"
    ];

    selectPosition(position: GridPosition): void {
        this.positionChange.emit(position);
    }
}
