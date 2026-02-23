import {ComponentFixture, TestBed} from "@angular/core/testing";
import {provideHttpClient} from "@angular/common/http";
import {provideRouter} from "@angular/router";
import {TranslateModule} from "@ngx-translate/core";
import {provideAnimationsAsync} from "@angular/platform-browser/animations/async";
import {SunoEnhancerComponent} from "./suno-enhancer.component";

describe("SunoEnhancerComponent", () => {
    let component: SunoEnhancerComponent;
    let fixture: ComponentFixture<SunoEnhancerComponent>;

    beforeEach(async () => {
        await TestBed.configureTestingModule({
            imports: [
                SunoEnhancerComponent,
                TranslateModule.forRoot(),
            ],
            providers: [
                provideHttpClient(),
                provideRouter([]),
                provideAnimationsAsync(),
            ],
        }).compileComponents();

        fixture = TestBed.createComponent(SunoEnhancerComponent);
        component = fixture.componentInstance;
        fixture.detectChanges();
    });

    it("should create", () => {
        expect(component).toBeTruthy();
    });

    it("should initialize in library mode", () => {
        expect(component.isEditorMode).toBeFalsy();
    });

    it("should have correct char limits", () => {
        expect(component.LYRICS_LIMIT).toBe(3000);
        expect(component.STYLE_LIMIT).toBe(1000);
    });
});
