import {ComponentFixture, TestBed} from "@angular/core/testing";
import {provideHttpClient} from "@angular/common/http";
import {provideHttpClientTesting} from "@angular/common/http/testing";
import {TranslateModule} from "@ngx-translate/core";

import {SongSketchLibraryComponent} from "./song-sketch-library.component";

describe("SongSketchLibraryComponent", () => {
    let component: SongSketchLibraryComponent;
    let fixture: ComponentFixture<SongSketchLibraryComponent>;

    beforeEach(async () => {
        await TestBed.configureTestingModule({
            imports: [SongSketchLibraryComponent,
                TranslateModule.forRoot()
            ],
            providers: [
                provideHttpClient(),
                provideHttpClientTesting()
            ]
        })
            .compileComponents();

        fixture = TestBed.createComponent(SongSketchLibraryComponent);
        component = fixture.componentInstance;
        fixture.detectChanges();
    });

    it("should create", () => {
        expect(component).toBeTruthy();
    });
});
