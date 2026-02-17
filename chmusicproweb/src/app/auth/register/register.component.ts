import {Component, inject, OnDestroy, OnInit} from "@angular/core";

import {FormBuilder, FormGroup, ReactiveFormsModule, Validators, AbstractControl, ValidationErrors} from "@angular/forms";
import {Router, RouterLink} from "@angular/router";
import {Subject} from "rxjs";
import {takeUntil} from "rxjs/operators";
import {TranslateModule, TranslateService} from "@ngx-translate/core";
import {AuthService} from "../../services/business/auth.service";
import {LanguageService} from "../../services/language.service";
import {UserCreateRequest} from "../../models/user.model";
import {environment} from "../../../environments/environment";

declare const grecaptcha: any;

@Component({
    selector: "app-register",
    standalone: true,
    imports: [ReactiveFormsModule, TranslateModule, RouterLink],
    templateUrl: "./register.component.html",
    styleUrls: ["./register.component.scss"]
})
export class RegisterComponent implements OnInit, OnDestroy {
    public registerForm: FormGroup;
    public currentStep = 1;
    public totalSteps = 5;
    public loading = false;
    public error: string | null = null;
    public hidePassword = true;
    public hideConfirmPassword = true;
    public termsAccepted = false;
    public registrationComplete = false;
    public recaptchaToken: string | null = null;
    public recaptchaWidgetId: number | null = null;
    public availableLanguages: {code: string; name: string}[] = [];

    private destroy$ = new Subject<void>();
    private formBuilder = inject(FormBuilder);
    private authService = inject(AuthService);
    private router = inject(Router);
    private languageService = inject(LanguageService);
    private translateService = inject(TranslateService);

    constructor() {
        this.registerForm = this.formBuilder.group({
            preferred_language: ["en"],
            first_name: ["", [Validators.maxLength(100)]],
            last_name: ["", [Validators.maxLength(100)]],
            artist_name: ["", [Validators.maxLength(100)]],
            invite_code: ["", [Validators.required]],
            email: ["", [Validators.required, Validators.email]],
            password: ["", [Validators.required, Validators.minLength(8)]],
            confirmPassword: ["", [Validators.required]],
            termsAccepted: [false, [Validators.requiredTrue]]
        }, {validators: this.passwordMatchValidator});
    }

    ngOnInit(): void {
        if (this.authService.isAuthenticated()) {
            this.router.navigate(["/"]);
            return;
        }

        this.availableLanguages = this.languageService.getAvailableLanguages();

        const currentLang = this.languageService.getCurrentLanguage();
        this.registerForm.patchValue({preferred_language: currentLang});
    }

    ngOnDestroy(): void {
        this.destroy$.next();
        this.destroy$.complete();
    }

    public onLanguageChange(): void {
        const lang = this.registerForm.get("preferred_language")?.value;
        if (lang) {
            this.translateService.use(lang);
        }
    }

    public get passwordStrength(): number {
        const password = this.registerForm.get("password")?.value || "";
        if (!password) return 0;
        let strength = 0;
        if (password.length >= 8) strength++;
        if (/[A-Z]/.test(password)) strength++;
        if (/[0-9]/.test(password)) strength++;
        if (/[^A-Za-z0-9]/.test(password)) strength++;
        return strength;
    }

    public get passwordStrengthLabel(): string {
        const strength = this.passwordStrength;
        if (strength <= 1) return "register.step3.strengthWeak";
        if (strength <= 2) return "register.step3.strengthMedium";
        if (strength <= 3) return "register.step3.strengthGood";
        return "register.step3.strengthStrong";
    }

    public get passwordStrengthClass(): string {
        const strength = this.passwordStrength;
        if (strength <= 1) return "weak";
        if (strength <= 2) return "medium";
        if (strength <= 3) return "good";
        return "strong";
    }

    public canProceed(): boolean {
        switch (this.currentStep) {
            case 1:
                return true;
            case 2:
                return true; // Personal info is optional
            case 3: {
                const inviteCode = this.registerForm.get("invite_code");
                const email = this.registerForm.get("email");
                const password = this.registerForm.get("password");
                const confirmPassword = this.registerForm.get("confirmPassword");
                return !!(inviteCode?.valid && email?.valid && password?.valid && confirmPassword?.valid &&
                    password?.value === confirmPassword?.value);
            }
            case 4:
                return this.registerForm.get("termsAccepted")?.value === true;
            default:
                return false;
        }
    }

    public nextStep(): void {
        if (this.currentStep < this.totalSteps && this.canProceed()) {
            this.currentStep++;
            if (this.currentStep === 4) {
                setTimeout(() => this.renderRecaptcha(), 300);
            }
        }
    }

    public prevStep(): void {
        if (this.currentStep > 1) {
            this.currentStep--;
        }
    }

    public goToStep(step: number): void {
        if (step < this.currentStep) {
            this.currentStep = step;
        }
    }

    public onSubmit(): void {
        if (!this.canProceed() || this.loading) return;

        this.loading = true;
        this.error = null;

        const formValue = this.registerForm.value;
        const userData: UserCreateRequest = {
            email: formValue.email,
            password: formValue.password,
            first_name: formValue.first_name || undefined,
            last_name: formValue.last_name || undefined,
            artist_name: formValue.artist_name || undefined,
            preferred_language: formValue.preferred_language,
            recaptcha_token: this.recaptchaToken || undefined,
            invite_code: formValue.invite_code || undefined
        };

        this.authService.register(userData)
            .pipe(takeUntil(this.destroy$))
            .subscribe({
                next: () => {
                    this.loading = false;
                    this.registrationComplete = true;
                    this.currentStep = 5;
                },
                error: (err) => {
                    this.loading = false;
                    this.error = err.error?.error || "Registration failed";
                    if (this.recaptchaWidgetId !== null) {
                        try { grecaptcha.reset(this.recaptchaWidgetId); } catch (_e) { /* ignore */ }
                    }
                    this.recaptchaToken = null;
                }
            });
    }

    public enterApp(): void {
        this.router.navigate(["/"]);
    }

    public togglePasswordVisibility(): void {
        this.hidePassword = !this.hidePassword;
    }

    public toggleConfirmPasswordVisibility(): void {
        this.hideConfirmPassword = !this.hideConfirmPassword;
    }

    public isFieldInvalid(fieldName: string): boolean {
        const field = this.registerForm.get(fieldName);
        return !!(field && field.invalid && (field.dirty || field.touched));
    }

    public hasPasswordMismatch(): boolean {
        const password = this.registerForm.get("password")?.value;
        const confirm = this.registerForm.get("confirmPassword");
        return !!(confirm && confirm.touched && password !== confirm.value && confirm.value);
    }

    private passwordMatchValidator(control: AbstractControl): ValidationErrors | null {
        const password = control.get("password");
        const confirmPassword = control.get("confirmPassword");
        if (password && confirmPassword && password.value !== confirmPassword.value) {
            confirmPassword.setErrors({...confirmPassword.errors, passwordMismatch: true});
            return {passwordMismatch: true};
        }
        if (confirmPassword?.hasError("passwordMismatch")) {
            const errors = {...confirmPassword.errors};
            delete errors["passwordMismatch"];
            confirmPassword.setErrors(Object.keys(errors).length ? errors : null);
        }
        return null;
    }

    private renderRecaptcha(): void {
        const siteKey = environment.recaptchaSiteKey;
        if (!siteKey) return;

        const container = document.getElementById("recaptcha-container");
        if (!container) return;

        try {
            if (typeof grecaptcha !== "undefined" && grecaptcha.render) {
                this.recaptchaWidgetId = grecaptcha.render("recaptcha-container", {
                    sitekey: siteKey,
                    callback: (token: string) => {
                        this.recaptchaToken = token;
                    },
                    "expired-callback": () => {
                        this.recaptchaToken = null;
                    }
                });
            }
        } catch (_e) {
            // reCAPTCHA may already be rendered
        }
    }
}
