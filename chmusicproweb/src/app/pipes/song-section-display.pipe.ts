import {Pipe, PipeTransform} from "@angular/core";
import {SongSection} from "../models/lyric-architecture.model";

@Pipe({
    name: "songSectionDisplay",
    standalone: true
})
export class SongSectionDisplayPipe implements PipeTransform {

    transform(section: SongSection): string {
        switch (section) {
            case SongSection.INTRO:
                return "Intro";
            case SongSection.VERSE:
                return "Verse";
            case SongSection.PRE_CHORUS:
                return "Pre-Chorus";
            case SongSection.CHORUS:
                return "Chorus";
            case SongSection.BRIDGE:
                return "Bridge";
            case SongSection.OUTRO:
                return "Outro";
            default:
                return section;
        }
    }
}