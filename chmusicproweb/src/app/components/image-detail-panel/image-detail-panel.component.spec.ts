import {ComponentFixture, TestBed} from "@angular/core/testing";
import {provideHttpClient} from "@angular/common/http";
import {provideHttpClientTesting} from "@angular/common/http/testing";
import {TranslateModule} from "@ngx-translate/core";

import {ImageDetailPanelComponent} from "./image-detail-panel.component";

describe("ImageDetailPanelComponent", () => {
    let component: ImageDetailPanelComponent;
    let fixture: ComponentFixture<ImageDetailPanelComponent>;

    beforeEach(async () => {
        await TestBed.configureTestingModule({
            imports: [
                ImageDetailPanelComponent,
                TranslateModule.forRoot()
            ],
            providers: [
                provideHttpClient(),
                provideHttpClientTesting()
            ]
        })
            .compileComponents();

        fixture = TestBed.createComponent(ImageDetailPanelComponent);
        component = fixture.componentInstance;
        fixture.detectChanges();
    });

    it("should create", () => {
        expect(component).toBeTruthy();
    });
});
