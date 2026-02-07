import {inject, Injectable} from "@angular/core";
import {MatSnackBar, MatSnackBarRef, TextOnlySnackBar} from "@angular/material/snack-bar";

export enum NotificationType {
    SUCCESS = "success",
    ERROR = "error",
    INFO = "info",
    LOADING = "loading"
}

@Injectable({
    providedIn: "root"
})
export class NotificationService {
    private loadingRef: MatSnackBarRef<TextOnlySnackBar> | null = null;

    private snackBar = inject(MatSnackBar);

    success(message: string, duration: number = 2000): void {
        this.dismissLoading();
        this.snackBar.open(message, "Close", {
            duration: duration,
            panelClass: ["success-snackbar"],
            verticalPosition: "top",
            horizontalPosition: "right"
        });
    }

    error(message: string, duration: number = 0): void {
        this.dismissLoading();
        this.snackBar.open(message, "Close", {
            duration: duration,  // 0 = indefinite (user must click Close button)
            panelClass: ["error-snackbar"],
            verticalPosition: "top",
            horizontalPosition: "right"
        });
    }

    info(message: string, duration: number = 3000): void {
        this.snackBar.open(message, "Close", {
            duration: duration,
            panelClass: ["info-snackbar"],
            verticalPosition: "top",
            horizontalPosition: "right"
        });
    }

    loading(message: string): void {
        this.dismissLoading();
        this.loadingRef = this.snackBar.open(message, undefined, {
            panelClass: ["loading-snackbar"],
            verticalPosition: "top",
            horizontalPosition: "right"
        });
    }

    dismissLoading(): void {
        if (this.loadingRef) {
            this.loadingRef.dismiss();
            this.loadingRef = null;
        }
    }

    dismiss(): void {
        this.snackBar.dismiss();
    }
}
