import {Routes} from "@angular/router";
import {AuthGuard} from "./guards/auth.guard";

export const routes: Routes = [
    {path: "", redirectTo: "/ai-chat", pathMatch: "full"},
    {
        path: "login",
        loadComponent: () => import("./auth/login/login.component").then(m => m.LoginComponent)
    },
    {
        path: "ai-chat",
        canActivate: [AuthGuard],
        loadComponent: () => import("./pages/ai-chat/ai-chat.component").then(m => m.AiChatComponent)
    },
    {
        path: "external-chat",
        canActivate: [AuthGuard],
        loadComponent: () => import("./pages/external-chat/external-chat.component").then(m => m.ExternalChatComponent)
    },
    {
        path: "openai-chat",
        redirectTo: "/external-chat",
        pathMatch: "full"
    },
    {
        path: "song-sketch-creator",
        canActivate: [AuthGuard],
        loadComponent: () => import("./pages/song-sketch-creator/song-sketch-creator.component").then(m => m.SongSketchCreatorComponent)
    },
    {
        path: "song-sketch-library",
        canActivate: [AuthGuard],
        loadComponent: () => import("./pages/song-sketch-library/song-sketch-library.component").then(m => m.SongSketchLibraryComponent)
    },
    {
        path: "lyriccreation",
        canActivate: [AuthGuard],
        loadComponent: () => import("./pages/lyric-creation/lyric-creation.component").then(m => m.LyricCreationComponent)
    },
    {
        path: "music-style-prompt",
        canActivate: [AuthGuard],
        loadComponent: () => import("./pages/music-style-prompt/music-style-prompt.component").then(m => m.MusicStylePromptComponent)
    },
    {
        path: "imagegen",
        canActivate: [AuthGuard],
        loadComponent: () => import("./pages/image-generator/image-generator.component").then(m => m.ImageGeneratorComponent)
    },
    {
        path: "imageview",
        canActivate: [AuthGuard],
        loadComponent: () => import("./pages/image-view/image-view.component").then(m => m.ImageViewComponent)
    },
    {
        path: "profile",
        canActivate: [AuthGuard],
        loadComponent: () => import("./pages/user-profile/user-profile.component").then(m => m.UserProfileComponent)
    },
    {
        path: "prompt-templates",
        canActivate: [AuthGuard],
        loadComponent: () => import("./pages/prompt-templates/prompt-templates.component").then(m => m.PromptTemplatesComponent)
    },
    {
        path: "prompt-template-editor",
        canActivate: [AuthGuard],
        loadComponent: () => import("./pages/prompt-template-editor/prompt-template-editor.component").then(m => m.PromptTemplateEditorComponent)
    },
    {
        path: "lyric-parsing-rules",
        canActivate: [AuthGuard],
        loadComponent: () => import("./pages/lyric-parsing-rules/lyric-parsing-rules.component").then(m => m.LyricParsingRulesComponent)
    },
    {
        path: "text-overlay-editor",
        canActivate: [AuthGuard],
        loadComponent: () => import("./pages/text-overlay-editor/text-overlay-editor.component").then(m => m.TextOverlayEditorComponent)
    },
    {
        path: "equipment-gallery",
        canActivate: [AuthGuard],
        loadComponent: () => import("./pages/equipment-gallery/equipment-gallery.component").then(m => m.EquipmentGalleryComponent)
    },
    {
        path: "equipment-editor",
        canActivate: [AuthGuard],
        loadComponent: () => import("./pages/equipment-editor/equipment-editor.component").then(m => m.EquipmentEditorComponent)
    },
    {
        path: "equipment-editor/:id",
        canActivate: [AuthGuard],
        loadComponent: () => import("./pages/equipment-editor/equipment-editor.component").then(m => m.EquipmentEditorComponent)
    },
    {
        path: "song-projects",
        canActivate: [AuthGuard],
        loadComponent: () => import("./pages/song-projects/song-projects.component").then(m => m.SongProjectsComponent)
    },
    {
        path: "song-releases/new",
        canActivate: [AuthGuard],
        loadComponent: () => import("./pages/song-release-editor/song-release-editor.component").then(m => m.SongReleaseEditorComponent)
    },
    {
        path: "song-releases/edit/:id",
        canActivate: [AuthGuard],
        loadComponent: () => import("./pages/song-release-editor/song-release-editor.component").then(m => m.SongReleaseEditorComponent)
    },
    {
        path: "song-releases",
        canActivate: [AuthGuard],
        loadComponent: () => import("./pages/song-release-gallery/song-release-gallery.component").then(m => m.SongReleaseGalleryComponent)
    },
    {
        path: "text-workshop",
        canActivate: [AuthGuard],
        loadComponent: () => import("./pages/text-workshop/text-workshop.component").then(m => m.TextWorkshopComponent)
    },
    {
        path: "text-workshop/:id",
        canActivate: [AuthGuard],
        loadComponent: () => import("./pages/text-workshop/text-workshop.component").then(m => m.TextWorkshopComponent)
    }
];
