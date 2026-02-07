import {bootstrapApplication} from "@angular/platform-browser";
import {registerLocaleData} from "@angular/common";
import localeDe from "@angular/common/locales/de";
import {appConfig} from "./app/app.config";
import {AppComponent} from "./app/app.component";

// Register German locale data for date formatting
registerLocaleData(localeDe, "de-DE");

bootstrapApplication(AppComponent, appConfig)
    .catch((err) => console.error(err));
