import {Injectable} from "@angular/core";
import {environment} from "../../../environments/environment";

@Injectable({
    providedIn: "root"
})
export class ApiConfigService {
    private readonly baseUrl = environment.apiUrl;

    // API Endpoints
    readonly endpoints = {
        song: {
            list: (limit?: number, offset?: number, status?: string) => {
                const params = new URLSearchParams();
                if (limit !== undefined) params.append("limit", limit.toString());
                if (offset !== undefined) params.append("offset", offset.toString());
                if (status) params.append("status", status);
                const query = params.toString();
                return `${this.baseUrl}/api/v1/song/list${query ? "?" + query : ""}`;
            },
            detail: (songId: string) => `${this.baseUrl}/api/v1/song/${songId}`,
            delete: (songId: string) => `${this.baseUrl}/api/v1/song/${songId}`,
            update: (songId: string) => `${this.baseUrl}/api/v1/song/${songId}`,
            updateChoiceRating: (choiceId: string) => `${this.baseUrl}/api/v1/song/choice/${choiceId}/rating`,
            bulkDelete: `${this.baseUrl}/api/v1/song/bulk-delete`,
            assignToProject: (songId: string) => `${this.baseUrl}/api/v1/song/${songId}/assign-to-project`,
            unassignFromProject: (songId: string) => `${this.baseUrl}/api/v1/song/${songId}/unassign-from-project`,
            // S3 Proxy endpoints (serves audio from S3)
            choiceMp3: (choiceId: string) => `${this.baseUrl}/api/v1/song/choice/${choiceId}/mp3`,
            choiceFlac: (choiceId: string) => `${this.baseUrl}/api/v1/song/choice/${choiceId}/flac`,
            choiceWav: (choiceId: string) => `${this.baseUrl}/api/v1/song/choice/${choiceId}/wav`,
            choiceStems: (choiceId: string) => `${this.baseUrl}/api/v1/song/choice/${choiceId}/stems`
        },
        image: {
            generate: `${this.baseUrl}/api/v1/image/generate`,
            status: (taskId: string) => `${this.baseUrl}/api/v1/image/status/${taskId}`,
            tasks: `${this.baseUrl}/api/v1/image/tasks`,
            list: (limit?: number, offset?: number) => `${this.baseUrl}/api/v1/image/list${limit !== undefined || offset !== undefined ? "?" : ""}${limit !== undefined ? `limit=${limit}` : ""}${limit !== undefined && offset !== undefined ? "&" : ""}${offset !== undefined ? `offset=${offset}` : ""}`,
            listForTextOverlay: `${this.baseUrl}/api/v1/image/list-for-text-overlay`,
            detail: (id: string) => `${this.baseUrl}/api/v1/image/${id}`,
            delete: (id: string) => `${this.baseUrl}/api/v1/image/${id}`,
            update: (id: string) => `${this.baseUrl}/api/v1/image/${id}`,
            bulkDelete: `${this.baseUrl}/api/v1/image/bulk-delete`,
            addTextOverlay: `${this.baseUrl}/api/v1/image/add-text-overlay`,
            assignToProject: (id: string) => `${this.baseUrl}/api/v1/image/id/${id}/assign-to-project`,
            unassignFromProject: (imageId: string, projectId: string) => `${this.baseUrl}/api/v1/image/id/${imageId}/unassign-from-project/${projectId}`,
            getProjects: (id: string) => `${this.baseUrl}/api/v1/image/id/${id}/projects`
        },
        prompt: {
            list: `${this.baseUrl}/api/v1/prompts`,
            category: (category: string) => `${this.baseUrl}/api/v1/prompts/${category}`,
            specific: (category: string, action: string) => `${this.baseUrl}/api/v1/prompts/${category}/${action}`,
            update: (category: string, action: string) => `${this.baseUrl}/api/v1/prompts/${category}/${action}`,
            create: `${this.baseUrl}/api/v1/prompts`,
            delete: (category: string, action: string) => `${this.baseUrl}/api/v1/prompts/${category}/${action}`
        },
        conversation: {
            list: (skip?: number, limit?: number, provider?: string, archived?: boolean) => {
                const params = new URLSearchParams();
                if (skip !== undefined) params.append("skip", skip.toString());
                if (limit !== undefined) params.append("limit", limit.toString());
                if (provider) params.append("provider", provider);
                if (archived === true) params.append("archived", "true");
                if (archived === false) params.append("archived", "false");
                // archived === undefined means default (only non-archived)
                const query = params.toString();
                return `${this.baseUrl}/api/v1/conversations${query ? "?" + query : ""}`;
            },
            detail: (id: string) => `${this.baseUrl}/api/v1/conversations/${id}`,
            create: `${this.baseUrl}/api/v1/conversations`,
            update: (id: string) => `${this.baseUrl}/api/v1/conversations/${id}`,
            delete: (id: string) => `${this.baseUrl}/api/v1/conversations/${id}`,
            sendMessage: (id: string) => `${this.baseUrl}/api/v1/conversations/${id}/messages`,
            compress: (id: string, keepRecent?: number) => {
                const query = keepRecent !== undefined ? `?keep_recent=${keepRecent}` : "";
                return `${this.baseUrl}/api/v1/conversations/${id}/compress${query}`;
            },
            restoreArchive: (id: string) => `${this.baseUrl}/api/v1/conversations/${id}/restore-archive`,
            exportFull: (id: string) => `${this.baseUrl}/api/v1/conversations/${id}/export-full`
        },
        ollama: {
            tags: `${this.baseUrl}/api/v1/ollama/tags`,
            chatModels: `${this.baseUrl}/api/v1/ollama/chat/models`,
            chatGenerateUnified: `${this.baseUrl}/api/v1/ollama/chat/generate-unified`
        },
        openai: {
            models: `${this.baseUrl}/api/v1/openai/chat/models`
        },
        claude: {
            models: `${this.baseUrl}/api/v1/claude/chat/models`
        },
        lyricParsingRule: {
            list: (ruleType?: string, activeOnly?: boolean) => {
                const params = new URLSearchParams();
                if (ruleType) params.append("rule_type", ruleType);
                if (activeOnly !== undefined) params.append("active_only", activeOnly.toString());
                const query = params.toString();
                return `${this.baseUrl}/api/v1/lyric-parsing-rules${query ? "?" + query : ""}`;
            },
            detail: (id: number) => `${this.baseUrl}/api/v1/lyric-parsing-rules/${id}`,
            create: `${this.baseUrl}/api/v1/lyric-parsing-rules`,
            update: (id: number) => `${this.baseUrl}/api/v1/lyric-parsing-rules/${id}`,
            delete: (id: number) => `${this.baseUrl}/api/v1/lyric-parsing-rules/${id}`,
            reorder: `${this.baseUrl}/api/v1/lyric-parsing-rules/reorder`
        },
        sketch: {
            create: () => `${this.baseUrl}/api/v1/sketches`,
            list: (limit?: number, offset?: number, workflow?: string, search?: string, sketchType?: string) => {
                const params = new URLSearchParams();
                if (limit !== undefined) params.append("limit", limit.toString());
                if (offset !== undefined) params.append("offset", offset.toString());
                if (workflow) params.append("workflow", workflow);
                if (search) params.append("search", search);
                if (sketchType) params.append("sketch_type", sketchType);
                const query = params.toString();
                return `${this.baseUrl}/api/v1/sketches${query ? "?" + query : ""}`;
            },
            detail: (id: string) => `${this.baseUrl}/api/v1/sketches/${id}`,
            update: (id: string) => `${this.baseUrl}/api/v1/sketches/${id}`,
            delete: (id: string) => `${this.baseUrl}/api/v1/sketches/${id}`,
            duplicate: (id: string) => `${this.baseUrl}/api/v1/sketches/${id}/duplicate`,
            assignToProject: (id: string) => `${this.baseUrl}/api/v1/sketches/${id}/assign-to-project`,
            unassignFromProject: (id: string) => `${this.baseUrl}/api/v1/sketches/${id}/unassign-from-project`
        },
        workshop: {
            create: () => `${this.baseUrl}/api/v1/workshops`,
            list: (limit?: number, offset?: number, search?: string, phase?: string) => {
                const params = new URLSearchParams();
                if (limit !== undefined) params.append("limit", limit.toString());
                if (offset !== undefined) params.append("offset", offset.toString());
                if (search) params.append("search", search);
                if (phase) params.append("phase", phase);
                const query = params.toString();
                return `${this.baseUrl}/api/v1/workshops${query ? "?" + query : ""}`;
            },
            detail: (id: string) => `${this.baseUrl}/api/v1/workshops/${id}`,
            update: (id: string) => `${this.baseUrl}/api/v1/workshops/${id}`,
            delete: (id: string) => `${this.baseUrl}/api/v1/workshops/${id}`,
            exportToSketch: (id: string) => `${this.baseUrl}/api/v1/workshops/${id}/export-to-sketch`
        },
        equipment: {
            create: () => `${this.baseUrl}/api/v1/equipment`,
            list: (limit?: number, offset?: number, type?: string, status?: string, search?: string) => {
                const params = new URLSearchParams();
                if (limit !== undefined) params.append("limit", limit.toString());
                if (offset !== undefined) params.append("offset", offset.toString());
                if (type) params.append("type", type);
                if (status) params.append("status", status);
                if (search) params.append("search", search);
                const query = params.toString();
                return `${this.baseUrl}/api/v1/equipment${query ? "?" + query : ""}`;
            },
            detail: (id: string) => `${this.baseUrl}/api/v1/equipment/${id}`,
            update: (id: string) => `${this.baseUrl}/api/v1/equipment/${id}`,
            delete: (id: string) => `${this.baseUrl}/api/v1/equipment/${id}`
        },
        user: {
            profile: `${this.baseUrl}/api/v1/user/profile`,
            update: `${this.baseUrl}/api/v1/user/profile`
        },
        costs: {
            openaiCurrent: `${this.baseUrl}/api/v1/openai/costs/current`,
            openaiMonth: (year: number, month: number) => `${this.baseUrl}/api/v1/openai/costs/${year}/${month}`,
            openaiAllTime: `${this.baseUrl}/api/v1/openai/costs/all-time`
        },
        songProject: {
            create: `${this.baseUrl}/api/v1/song-projects`,
            list: (limit?: number, offset?: number, search?: string, tags?: string, projectStatus?: string) => {
                const params = new URLSearchParams();
                if (limit !== undefined) params.append("limit", limit.toString());
                if (offset !== undefined) params.append("offset", offset.toString());
                if (search) params.append("search", search);
                if (tags) params.append("tags", tags);
                if (projectStatus) params.append("project_status", projectStatus);
                const query = params.toString();
                return `${this.baseUrl}/api/v1/song-projects${query ? "?" + query : ""}`;
            },
            detail: (id: string) => `${this.baseUrl}/api/v1/song-projects/${id}`,
            update: (id: string) => `${this.baseUrl}/api/v1/song-projects/${id}`,
            delete: (id: string) => `${this.baseUrl}/api/v1/song-projects/${id}`,
            uploadFile: (id: string) => `${this.baseUrl}/api/v1/song-projects/${id}/files`,
            clearFolder: (projectId: string, folderId: string) => `${this.baseUrl}/api/v1/song-projects/${projectId}/folders/${folderId}/clear`
        },
        songRelease: {
            create: `${this.baseUrl}/api/v1/song-releases`,
            list: (limit?: number, offset?: number, statusFilter?: string, search?: string) => {
                const params = new URLSearchParams();
                if (limit !== undefined) params.append("limit", limit.toString());
                if (offset !== undefined) params.append("offset", offset.toString());
                if (statusFilter) params.append("status_filter", statusFilter);
                if (search) params.append("search", search);
                const query = params.toString();
                return `${this.baseUrl}/api/v1/song-releases${query ? "?" + query : ""}`;
            },
            detail: (id: string) => `${this.baseUrl}/api/v1/song-releases/${id}`,
            update: (id: string) => `${this.baseUrl}/api/v1/song-releases/${id}`,
            delete: (id: string) => `${this.baseUrl}/api/v1/song-releases/${id}`
        }
    };

    getBaseUrl(): string {
        return this.baseUrl;
    }

    getEndpoint(category: keyof typeof this.endpoints, action: string, ...params: unknown[]): string {
        const categoryEndpoints = this.endpoints[category] as Record<string, unknown>;
        const endpoint = categoryEndpoints[action];
        return typeof endpoint === "function" ? endpoint(...params) : endpoint as string;
    }
}
