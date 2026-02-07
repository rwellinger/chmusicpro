import {Component, inject, OnDestroy, OnInit} from "@angular/core";
import {CommonModule} from "@angular/common";
import {FormBuilder, FormGroup, ReactiveFormsModule, Validators} from "@angular/forms";
import {Router} from "@angular/router";
import {Subject} from "rxjs";
import {takeUntil} from "rxjs/operators";
import {AuthService} from "../../services/business/auth.service";
import {LoginRequest} from "../../models/user.model";

@Component({
    selector: "app-login",
    standalone: true,
    imports: [CommonModule, ReactiveFormsModule],
    templateUrl: "./login.component.html",
    styleUrls: ["./login.component.scss"]
})
export class LoginComponent implements OnInit, OnDestroy {
    public loginForm: FormGroup;
    public loading = false;
    public error: string | null = null;
    public hidePassword = true;

    private destroy$ = new Subject<void>();
    private formBuilder = inject(FormBuilder);
    private authService = inject(AuthService);
    private router = inject(Router);

    constructor() {
        this.loginForm = this.formBuilder.group({
            email: ["", [Validators.required, Validators.email]],
            password: ["", [Validators.required, Validators.minLength(4)]]
        });
    }

    ngOnInit(): void {
        // Check if already authenticated
        if (this.authService.isAuthenticated()) {
            this.router.navigate(["/"]);
            return;
        }

        // Subscribe to auth state changes
        this.authService.authState$
            .pipe(takeUntil(this.destroy$))
            .subscribe(authState => {
                this.loading = authState.loading;
                this.error = authState.error;

                if (authState.isAuthenticated) {
                    this.router.navigate(["/"]);
                }
            });
    }

    ngOnDestroy(): void {
        this.destroy$.next();
        this.destroy$.complete();
    }

    public onSubmit(): void {
        if (this.loginForm.valid) {
            const credentials: LoginRequest = {
                email: this.loginForm.value.email,
                password: this.loginForm.value.password
            };

            this.authService.login(credentials)
                .pipe(takeUntil(this.destroy$))
                .subscribe({
                    next: () => {
                    },
                    error: (error) => {
                        console.error("Login error:", error);
                    }
                });
        } else {
            this.markFormGroupTouched();
        }
    }

    public togglePasswordVisibility(): void {
        this.hidePassword = !this.hidePassword;
    }

    public getErrorMessage(fieldName: string): string {
        const field = this.loginForm.get(fieldName);

        if (field?.hasError("required")) {
            return `${fieldName.charAt(0).toUpperCase() + fieldName.slice(1)} is required`;
        }

        if (field?.hasError("email")) {
            return "Please enter a valid email address";
        }

        if (field?.hasError("minlength")) {
            return `${fieldName.charAt(0).toUpperCase() + fieldName.slice(1)} must be at least 4 characters long`;
        }

        return "";
    }

    public isFieldInvalid(fieldName: string): boolean {
        const field = this.loginForm.get(fieldName);
        return !!(field && field.invalid && (field.dirty || field.touched));
    }

    private markFormGroupTouched(): void {
        Object.keys(this.loginForm.controls).forEach(key => {
            const control = this.loginForm.get(key);
            if (control) {
                control.markAsTouched();
            }
        });
    }

    public clearError(): void {
        this.error = null;
    }
}