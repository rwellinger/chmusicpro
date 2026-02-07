import {ComponentFixture, TestBed} from "@angular/core/testing";
import {provideHttpClient} from "@angular/common/http";
import {provideHttpClientTesting} from "@angular/common/http/testing";
import {TranslateModule} from "@ngx-translate/core";

import {GridPositionSelectorComponent} from "./grid-position-selector.component";

describe("GridPositionSelectorComponent", () => {
    let component: GridPositionSelectorComponent;
    let fixture: ComponentFixture<GridPositionSelectorComponent>;

    beforeEach(async () => {
        await TestBed.configureTestingModule({
            imports: [GridPositionSelectorComponent,
                TranslateModule.forRoot()
            ],
            providers: [
                provideHttpClient(),
                provideHttpClientTesting()
            ]
        })
            .compileComponents();

        fixture = TestBed.createComponent(GridPositionSelectorComponent);
        component = fixture.componentInstance;
        fixture.detectChanges();
    });

    it("should create", () => {
        expect(component).toBeTruthy();
    });
});
