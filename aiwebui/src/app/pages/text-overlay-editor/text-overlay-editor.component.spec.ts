import {ComponentFixture, TestBed} from "@angular/core/testing";
import {provideHttpClient} from "@angular/common/http";
import {provideHttpClientTesting} from "@angular/common/http/testing";
import {provideRouter} from "@angular/router";
import {provideAnimations} from "@angular/platform-browser/animations";
import {TranslateModule} from "@ngx-translate/core";

import {TextOverlayEditorComponent} from "./text-overlay-editor.component";

describe("TextOverlayEditorComponent", () => {
    let component: TextOverlayEditorComponent;
    let fixture: ComponentFixture<TextOverlayEditorComponent>;

    beforeEach(async () => {
        await TestBed.configureTestingModule({
            imports: [
                TextOverlayEditorComponent,
                TranslateModule.forRoot()
            ],
            providers: [
                provideHttpClient(),
                provideHttpClientTesting(),
                provideRouter([]),
                provideAnimations()
            ]
        })
            .compileComponents();

        fixture = TestBed.createComponent(TextOverlayEditorComponent);
        component = fixture.componentInstance;
        fixture.detectChanges();
    });

    it("should create", () => {
        expect(component).toBeTruthy();
    });
});
