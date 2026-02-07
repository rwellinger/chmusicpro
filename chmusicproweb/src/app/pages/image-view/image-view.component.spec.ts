import {ComponentFixture, TestBed} from "@angular/core/testing";
import {provideHttpClient} from "@angular/common/http";
import {provideHttpClientTesting} from "@angular/common/http/testing";
import {TranslateModule} from "@ngx-translate/core";

import {ImageViewComponent} from "./image-view.component";

describe("ImageViewComponent", () => {
    let component: ImageViewComponent;
    let fixture: ComponentFixture<ImageViewComponent>;

    beforeEach(async () => {
        await TestBed.configureTestingModule({
            imports: [ImageViewComponent,
                TranslateModule.forRoot()
            ],
            providers: [
                provideHttpClient(),
                provideHttpClientTesting()
            ]
        })
            .compileComponents();

        fixture = TestBed.createComponent(ImageViewComponent);
        component = fixture.componentInstance;
        fixture.detectChanges();
    });

    it("should create", () => {
        expect(component).toBeTruthy();
    });
});