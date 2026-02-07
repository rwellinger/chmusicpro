import {ComponentFixture, TestBed} from "@angular/core/testing";
import {provideHttpClient} from "@angular/common/http";
import {provideHttpClientTesting} from "@angular/common/http/testing";
import {TranslateModule} from "@ngx-translate/core";

import {SongSketchCreatorComponent} from "./song-sketch-creator.component";

describe("SongSketchCreatorComponent", () => {
    let component: SongSketchCreatorComponent;
    let fixture: ComponentFixture<SongSketchCreatorComponent>;

    beforeEach(async () => {
        await TestBed.configureTestingModule({
            imports: [SongSketchCreatorComponent,
                TranslateModule.forRoot()
            ],
            providers: [
                provideHttpClient(),
                provideHttpClientTesting()
            ]
        })
            .compileComponents();

        fixture = TestBed.createComponent(SongSketchCreatorComponent);
        component = fixture.componentInstance;
        fixture.detectChanges();
    });

    it("should create", () => {
        expect(component).toBeTruthy();
    });
});
