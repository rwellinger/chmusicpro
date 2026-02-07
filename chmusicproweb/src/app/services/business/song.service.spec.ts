import {TestBed} from "@angular/core/testing";
import {provideHttpClient} from "@angular/common/http";
import {provideHttpClientTesting} from "@angular/common/http/testing";

import {SongService} from "./song.service";

describe("SongService", () => {
    let service: SongService;

    beforeEach(() => {
        TestBed.configureTestingModule({
            providers: [
                provideHttpClient(),
                provideHttpClientTesting()
            ]
        });
        service = TestBed.inject(SongService);
    });

    it("should be created", () => {
        expect(service).toBeTruthy();
    });
});
