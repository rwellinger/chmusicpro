import {ApplicationConfig, APP_INITIALIZER, LOCALE_ID} from "@angular/core";
import {provideRouter} from "@angular/router";
import {provideHttpClient, withInterceptors} from "@angular/common/http";
import {provideAnimationsAsync} from "@angular/platform-browser/animations/async";
import {CookieService} from "ngx-cookie-service";
import {provideTranslateService, TranslateLoader} from "@ngx-translate/core";
import {HttpClient} from "@angular/common/http";
import {Observable} from "rxjs";
import {MAT_DATE_LOCALE, MAT_DATE_FORMATS, provideNativeDateAdapter} from "@angular/material/core";

import {routes} from "./app.routes";
import {authInterceptor} from "./interceptors/auth.interceptor";
import {LanguageService} from "./services/language.service";

// Custom TranslateLoader implementation
export class CustomTranslateLoader implements TranslateLoader {
    constructor(private http: HttpClient, private prefix: string = "./assets/i18n/", private suffix: string = ".json") {
    }

    getTranslation(lang: string): Observable<any> {
        return this.http.get(`${this.prefix}${lang}${this.suffix}`);
    }
}

// Factory function for APP_INITIALIZER to load translations before app starts
export function initializeApp(languageService: LanguageService): () => Promise<void> {
    return () => languageService.initialize();
}

// Custom date format for European format (DD.MM.YYYY)
export const EUROPEAN_DATE_FORMATS = {
    parse: {
        dateInput: "DD.MM.YYYY",
    },
    display: {
        dateInput: "DD.MM.YYYY",
        monthYearLabel: "MMM YYYY",
        dateA11yLabel: "DD.MM.YYYY",
        monthYearA11yLabel: "MMMM YYYY",
    },
};

export const appConfig: ApplicationConfig = {
    providers: [
        provideRouter(routes),
        provideHttpClient(withInterceptors([authInterceptor])),
        provideAnimationsAsync(),
        CookieService,
        provideTranslateService({
            defaultLanguage: "en",
            loader: {
                provide: TranslateLoader,
                useFactory: (http: HttpClient) => new CustomTranslateLoader(http),
                deps: [HttpClient]
            }
        }),
        {
            provide: APP_INITIALIZER,
            useFactory: initializeApp,
            deps: [LanguageService],
            multi: true
        },
        // Date Configuration for European Format (DD.MM.YYYY)
        {provide: LOCALE_ID, useValue: "de-DE"},
        {provide: MAT_DATE_LOCALE, useValue: "de-DE"},
        {provide: MAT_DATE_FORMATS, useValue: EUROPEAN_DATE_FORMATS},
        provideNativeDateAdapter()
    ]
};
