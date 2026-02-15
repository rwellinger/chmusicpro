import {ComponentFixture, TestBed} from "@angular/core/testing";
import {provideHttpClient} from "@angular/common/http";
import {provideHttpClientTesting} from "@angular/common/http/testing";
import {provideRouter} from "@angular/router";
import {TranslateModule} from "@ngx-translate/core";

import {TextWorkshopComponent} from "./text-workshop.component";

describe("TextWorkshopComponent", () => {
    let component: TextWorkshopComponent;
    let fixture: ComponentFixture<TextWorkshopComponent>;

    beforeEach(async () => {
        await TestBed.configureTestingModule({
            imports: [
                TextWorkshopComponent,
                TranslateModule.forRoot()
            ],
            providers: [
                provideHttpClient(),
                provideHttpClientTesting(),
                provideRouter([])
            ]
        })
            .compileComponents();

        fixture = TestBed.createComponent(TextWorkshopComponent);
        component = fixture.componentInstance;
        fixture.detectChanges();
    });

    it("should create", () => {
        expect(component).toBeTruthy();
    });

    it("should initialize in library mode", () => {
        expect(component.isEditorMode).toBe(false);
        expect(component.currentWorkshopId).toBeNull();
    });

    it("should have default phase as connect", () => {
        expect(component.currentPhase).toBe("connect");
    });

    it("should have default draft language as EN", () => {
        expect(component.draftLanguage).toBe("EN");
    });

    describe("getLanguageName", () => {
        it("should return correct language names", () => {
            expect(component.getLanguageName("EN")).toBe("English");
            expect(component.getLanguageName("DE")).toBe("German");
            expect(component.getLanguageName("FR")).toBe("French");
            expect(component.getLanguageName("IT")).toBe("Italian");
            expect(component.getLanguageName("ES")).toBe("Spanish");
        });

        it("should return English for unknown code", () => {
            expect(component.getLanguageName("JP")).toBe("English");
        });
    });

    describe("parseMarkdownItems", () => {
        it("should parse numbered bold items", () => {
            const text = "1. **Heading One**\nContent one\n\n2. **Heading Two**\nContent two";
            const items = component.parseMarkdownItems(text);
            expect(items.length).toBe(2);
            expect(items[0].heading).toBe("Heading One");
            expect(items[1].heading).toBe("Heading Two");
            expect(items[0].selected).toBe(true);
        });

        it("should return empty array for single item", () => {
            const text = "1. **Only One**\nSome content";
            const items = component.parseMarkdownItems(text);
            expect(items.length).toBe(0);
        });

        it("should return empty array for plain text", () => {
            const items = component.parseMarkdownItems("Just plain text without bold headings");
            expect(items.length).toBe(0);
        });
    });

    describe("compileSelectedItems", () => {
        it("should compile only selected items", () => {
            const items = [
                {id: 0, heading: "First", content: "Content 1", selected: true},
                {id: 1, heading: "Second", content: "Content 2", selected: false},
                {id: 2, heading: "Third", content: "Content 3", selected: true}
            ];
            const result = component.compileSelectedItems(items);
            expect(result).toContain("1. **First**");
            expect(result).toContain("2. **Third**");
            expect(result).not.toContain("Second");
        });

        it("should return empty string when nothing selected", () => {
            const items = [
                {id: 0, heading: "First", content: "Content 1", selected: false}
            ];
            const result = component.compileSelectedItems(items);
            expect(result).toBe("");
        });
    });

    describe("pagination", () => {
        it("should not have previous page on first page", () => {
            component.currentPage = 0;
            expect(component.hasPreviousPage).toBe(false);
        });

        it("should have previous page when not on first page", () => {
            component.currentPage = 1;
            expect(component.hasPreviousPage).toBe(true);
        });

        it("should not have next page when all items shown", () => {
            component.currentPage = 0;
            component.pageSize = 20;
            component.totalWorkshops = 15;
            expect(component.hasNextPage).toBe(false);
        });

        it("should have next page when more items exist", () => {
            component.currentPage = 0;
            component.pageSize = 20;
            component.totalWorkshops = 25;
            expect(component.hasNextPage).toBe(true);
        });
    });

    describe("selection helpers", () => {
        it("should detect selected inspirations", () => {
            component.inspirationItems = [
                {id: 0, heading: "A", content: "B", selected: true}
            ];
            expect(component.hasSelectedInspirations).toBe(true);
        });

        it("should detect no selected inspirations", () => {
            component.inspirationItems = [
                {id: 0, heading: "A", content: "B", selected: false}
            ];
            expect(component.hasSelectedInspirations).toBe(false);
        });

        it("should toggle inspiration item selection", () => {
            const item = {id: 0, heading: "A", content: "B", selected: true};
            component.toggleInspirationItem(item);
            expect(item.selected).toBe(false);
            component.toggleInspirationItem(item);
            expect(item.selected).toBe(true);
        });

        it("should toggle story item selection", () => {
            const item = {id: 0, heading: "A", content: "B", selected: false};
            component.toggleStoryItem(item);
            expect(item.selected).toBe(true);
        });
    });
});
