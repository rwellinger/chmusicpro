import {ComponentFixture, TestBed} from "@angular/core/testing";
import {provideHttpClient} from "@angular/common/http";
import {provideHttpClientTesting} from "@angular/common/http/testing";
import {provideRouter} from "@angular/router";
import {provideAnimations} from "@angular/platform-browser/animations";
import {TranslateModule} from "@ngx-translate/core";

import {ImageGeneratorComponent} from "./image-generator.component";

describe("ImageGeneratorComponent", () => {
    let component: ImageGeneratorComponent;
    let fixture: ComponentFixture<ImageGeneratorComponent>;

    beforeEach(async () => {
        await TestBed.configureTestingModule({
            imports: [ImageGeneratorComponent,
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

        fixture = TestBed.createComponent(ImageGeneratorComponent);
        component = fixture.componentInstance;
        fixture.detectChanges();
    });

    it("should create", () => {
        expect(component).toBeTruthy();
    });
});
