import {Injectable} from "@angular/core";
import {BehaviorSubject, Observable} from "rxjs";

export interface ProgressState {
    isVisible: boolean;
    message: string;
    detail?: string;
}

@Injectable({
    providedIn: "root"
})
export class ProgressService {
    private progressState = new BehaviorSubject<ProgressState>({
        isVisible: false,
        message: "",
        detail: ""
    });

    get progress$(): Observable<ProgressState> {
        return this.progressState.asObservable();
    }

    show(message: string, detail?: string): void {
        this.progressState.next({
            isVisible: true,
            message,
            detail
        });
    }

    hide(): void {
        this.progressState.next({
            isVisible: false,
            message: "",
            detail: ""
        });
    }

    updateMessage(message: string, detail?: string): void {
        const current = this.progressState.value;
        if (current.isVisible) {
            this.progressState.next({
                ...current,
                message,
                detail: detail || current.detail
            });
        }
    }

    async executeWithProgress<T>(
        operation: () => Promise<T>,
        message: string,
        detail?: string
    ): Promise<T> {
        this.show(message, detail);
        try {
            const result = await operation();
            return result;
        } finally {
            this.hide();
        }
    }
}