import {ComponentFixture, TestBed} from "@angular/core/testing";
import {provideHttpClient} from "@angular/common/http";
import {provideHttpClientTesting} from "@angular/common/http/testing";
import {TranslateModule} from "@ngx-translate/core";

import {SongDetailPanelComponent} from "./song-detail-panel.component";

describe("SongDetailPanelComponent", () => {
    let component: SongDetailPanelComponent;
    let fixture: ComponentFixture<SongDetailPanelComponent>;

    beforeEach(async () => {
        await TestBed.configureTestingModule({
            imports: [SongDetailPanelComponent,
                TranslateModule.forRoot()
            ],
            providers: [
                provideHttpClient(),
                provideHttpClientTesting()
            ]
        })
            .compileComponents();

        fixture = TestBed.createComponent(SongDetailPanelComponent);
        component = fixture.componentInstance;
        fixture.detectChanges();
    });

    it("should create", () => {
        expect(component).toBeTruthy();
    });
});
