export interface PipelineStep {
    step: number;
    titleKey: string;
    descriptionKey: string;
    icon: string;
    iconColor: string;
    enabled: boolean;
    routes: string[];
    primaryRoute: string;
}

export const PIPELINE_STEPS: PipelineStep[] = [
    {
        step: 1,
        titleKey: "dashboard.tiles.workshop.title",
        descriptionKey: "dashboard.tiles.workshop.description",
        icon: "fa-pen-fancy",
        iconColor: "#AD1457",
        enabled: true,
        routes: ["/text-workshop", "/lyriccreation"],
        primaryRoute: "/text-workshop"
    },
    {
        step: 2,
        titleKey: "dashboard.tiles.composition.title",
        descriptionKey: "dashboard.tiles.composition.description",
        icon: "fa-sliders-h",
        iconColor: "#7B1FA2",
        enabled: true,
        routes: ["/song-sketch-library", "/song-sketch-creator", "/music-style-prompt"],
        primaryRoute: "/song-sketch-library"
    },
    {
        step: 3,
        titleKey: "dashboard.tiles.cover.title",
        descriptionKey: "dashboard.tiles.cover.description",
        icon: "fa-image",
        iconColor: "#28a745",
        enabled: true,
        routes: ["/imageview", "/imagegen", "/text-overlay-editor"],
        primaryRoute: "/imageview"
    },
    {
        step: 4,
        titleKey: "dashboard.tiles.distribute.title",
        descriptionKey: "dashboard.tiles.distribute.description",
        icon: "fa-share-alt",
        iconColor: "#ff9800",
        enabled: true,
        routes: ["/song-releases"],
        primaryRoute: "/song-releases"
    },
    {
        step: 5,
        titleKey: "dashboard.tiles.promote.title",
        descriptionKey: "dashboard.tiles.promote.description",
        icon: "fa-bullhorn",
        iconColor: "#6c757d",
        enabled: false,
        routes: [],
        primaryRoute: ""
    },
    {
        step: 6,
        titleKey: "dashboard.tiles.project.title",
        descriptionKey: "dashboard.tiles.project.description",
        icon: "fa-folder-open",
        iconColor: "#D32F2F",
        enabled: true,
        routes: ["/song-projects"],
        primaryRoute: "/song-projects"
    }
];
