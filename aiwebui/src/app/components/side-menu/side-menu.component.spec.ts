import {ComponentFixture, TestBed} from "@angular/core/testing";
import {provideHttpClient} from "@angular/common/http";
import {provideHttpClientTesting} from "@angular/common/http/testing";
import {provideRouter} from "@angular/router";
import {TranslateModule} from "@ngx-translate/core";

import {SideMenuComponent} from "./side-menu.component";

describe("SideMenuComponent", () => {
    let component: SideMenuComponent;
    let fixture: ComponentFixture<SideMenuComponent>;

    beforeEach(async () => {
        await TestBed.configureTestingModule({
            imports: [SideMenuComponent,
                TranslateModule.forRoot()
            ],
            providers: [
                provideHttpClient(),
                provideHttpClientTesting(),
                provideRouter([])
            ]
        })
            .compileComponents();

        fixture = TestBed.createComponent(SideMenuComponent);
        component = fixture.componentInstance;
        fixture.detectChanges();
    });

    it("should create", () => {
        expect(component).toBeTruthy();
    });
});
