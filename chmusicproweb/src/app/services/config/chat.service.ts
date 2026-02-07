import {inject, Injectable} from "@angular/core";
import {HttpClient} from "@angular/common/http";
import {ApiConfigService} from "./api-config.service";
import {PromptConfigService} from "./prompt-config.service";
import {LyricArchitectureService} from "../lyric-architecture.service";
import {firstValueFrom} from "rxjs";

/**
 * ⚠️ CRITICAL: Single Entry Point for Ollama + Prompt Template Integration
 *
 * This service is the ONLY place where Ollama should be called with database templates.
 *
 * ARCHITECTURE:
 * All methods delegate to the central private method: callUnifiedWithValidation()
 * This ensures consistent error handling, validation, and empty response detection.
 *
 * FOR NEW IMPLEMENTATIONS:
 * ✅ Add a new public method that calls callUnifiedWithValidation()
 * ✅ Use preConditionEnhancer callback for custom pre_condition logic
 * ✅ Use userInstructions parameter for user-specific instructions
 * ✅ Ensure template exists in DB first (check prompt_templates table)
 *
 * ❌ NEVER:
 * - Direct Ollama API calls in other services
 * - Bypass callUnifiedWithValidation() - all methods MUST use it
 * - Use templates before they exist in DB (backend has no data!)
 * - Implement custom HTTP calls to unified endpoint
 *
 * DEPRECATED:
 * - validateAndCallUnified() is kept for backward compatibility only
 * - Do NOT use it for new implementations
 *
 * WHY? This is NOT a direct Ollama proxy - it's a Template-Driven Generation System.
 * Templates MUST be in DB first, otherwise backend has no configuration to work with.
 */

interface UnifiedChatRequest {
    pre_condition: string;
    post_condition: string;
    input_text: string;
    user_instructions?: string;
    temperature?: number;
    max_tokens?: number;
    model?: string;
    category?: string;
    action?: string;
}


export interface ChatResponse {
    model: string;
    created_at: string;
    response: string;
    done: boolean;
    done_reason: string;
    total_duration: number;
    load_duration: number;
    prompt_eval_count: number;
    prompt_eval_duration: number;
    eval_count: number;
    eval_duration: number;
}

@Injectable({
    providedIn: "root"
})
export class ChatService {
    private http = inject(HttpClient);
    private apiConfig = inject(ApiConfigService);
    private promptConfig = inject(PromptConfigService);
    private architectureService = inject(LyricArchitectureService);

    /**
     * Central method for all Ollama chat operations with template support.
     *
     * This method handles:
     * - Template loading and validation
     * - Optional pre_condition enhancement via callback
     * - Empty response validation with generic error messages
     * - Request building and execution
     *
     * @param category Template category (e.g., 'music', 'lyrics', 'image')
     * @param action Template action (e.g., 'enhance', 'generate')
     * @param inputText User input text
     * @param preConditionEnhancer Optional callback to modify pre_condition before sending
     * @param userInstructions Optional user-specific instructions
     * @returns AI-generated response text
     * @throws Error if template not found, validation fails, or response is empty
     */
    private async callUnifiedWithValidation(
        category: string,
        action: string,
        inputText: string,
        preConditionEnhancer?: (template: any) => string,
        userInstructions?: string
    ): Promise<string> {
        const template = await firstValueFrom(this.promptConfig.getPromptTemplateAsync(category, action));
        if (!template) {
            throw new Error(`Template ${category}/${action} not found in database`);
        }

        // Validate template has required parameters (model and temperature)
        // Note: max_tokens is optional (null/0 means no limit, let model decide)
        if (!template.model) {
            throw new Error(`Template ${category}/${action} is missing model parameter`);
        }
        if (template.temperature === undefined || template.temperature === null) {
            throw new Error(`Template ${category}/${action} is missing temperature parameter`);
        }

        // Apply pre_condition enhancement if provided, otherwise use template default
        const preCondition = preConditionEnhancer
            ? preConditionEnhancer(template)
            : (template.pre_condition || "");

        const request: UnifiedChatRequest = {
            pre_condition: preCondition,
            post_condition: template.post_condition || "",
            input_text: inputText,
            user_instructions: userInstructions || "",
            temperature: template.temperature,
            max_tokens: template.max_tokens,
            model: template.model,
            category: category,
            action: action
        };

        const data: ChatResponse = await firstValueFrom(
            this.http.post<ChatResponse>(this.apiConfig.endpoints.ollama.chatGenerateUnified, request)
        );

        // Validate response is not empty (can happen with large models hitting token limits)
        if (!data.response || data.response.trim() === "") {
            // Check if token limit was definitively hit (eval_count >= max_tokens && done_reason == "length")
            if (data.eval_count >= (template.max_tokens || 0) && data.done_reason === "length") {
                throw new Error(
                    `AI Model hit token limit (${data.eval_count}/${template.max_tokens} tokens). Try reducing input length or simplifying the request.`
                );
            }

            // Generic empty response error (unknown cause)
            throw new Error(
                `AI Model returned empty response. Please try again or reduce input complexity.`
            );
        }

        return data.response;
    }

    /**
     * @deprecated Use callUnifiedWithValidation() for new implementations.
     * This method is kept for backward compatibility with existing code.
     *
     * Simple wrapper for template-based generation without pre_condition enhancement.
     */
    async validateAndCallUnified(category: string, action: string, inputText: string): Promise<string> {
        return this.callUnifiedWithValidation(category, action, inputText);
    }

    async improveImagePrompt(prompt: string): Promise<string> {
        return this.validateAndCallUnified("image", "enhance", prompt);
    }

    async improveImagePromptFast(prompt: string): Promise<string> {
        return this.validateAndCallUnified("image", "enhance-fast", prompt);
    }

    async enhanceCoverPrompt(prompt: string): Promise<string> {
        return this.validateAndCallUnified("image", "enhance-cover", prompt);
    }

    async improveMusicStylePrompt(prompt: string): Promise<string> {
        return this.validateAndCallUnified("music", "enhance", prompt);
    }

    async improveMusicStylePromptForSuno(prompt: string, gender?: "male" | "female"): Promise<string> {
        return this.callUnifiedWithValidation("music", "enhance-suno", prompt, (template) => {
            let enhanced = template.pre_condition || "";
            if (gender) {
                const genderInstruction = gender === "male"
                    ? "\n\nVocal preference: Male voice with natural pitch (avoid unnaturally high male vocals)"
                    : "\n\nVocal preference: Female voice with natural pitch";
                enhanced += genderInstruction;
            }
            return enhanced;
        });
    }

    async generateLyrics(inputText: string): Promise<string> {
        return this.generateLyricsWithArchitecture(inputText);
    }

    async generateLyricsWithArchitecture(inputText: string): Promise<string> {
        return this.callUnifiedWithValidation("lyrics", "generate", inputText, (template) => {
            const architectureString = this.architectureService.generateArchitectureString();
            let enhanced = template.pre_condition || "";
            if (architectureString.trim()) {
                enhanced = architectureString + "\n\n" + enhanced;
            }
            return enhanced;
        });
    }

    async translateLyric(prompt: string): Promise<string> {
        return this.validateAndCallUnified("lyrics", "translate", prompt);
    }

    async translateMusicStylePrompt(prompt: string): Promise<string> {
        return this.validateAndCallUnified("music", "translate", prompt);
    }

    async translateImagePrompt(prompt: string): Promise<string> {
        return this.validateAndCallUnified("image", "translate", prompt);
    }

    async interpretLyricPrompt(lyric: string): Promise<string> {
        return this.validateAndCallUnified("image", "interpret-lyric", lyric);
    }

    async generateTitle(inputText: string): Promise<string> {
        return this.validateAndCallUnified("titel", "generate", inputText);
    }

    async generateTitleFast(inputText: string): Promise<string> {
        return this.validateAndCallUnified("titel", "generate-fast", inputText);
    }

    async improveLyricSection(
        sectionLabel: string,
        sectionContent: string,
        fullContext: string,
        userInstructions?: string
    ): Promise<string> {
        return this.callUnifiedWithValidation(
            "lyrics",
            "improve-section",
            sectionContent,
            (template) => `You are improving only the "${sectionLabel}" section.\n\nFull song context:\n${fullContext}\n\n${template.pre_condition || ""}`,
            userInstructions
        );
    }

    async rewriteLyricSection(
        sectionLabel: string,
        sectionContent: string,
        userInstructions?: string
    ): Promise<string> {
        return this.callUnifiedWithValidation(
            "lyrics",
            "rewrite-section",
            sectionContent,
            (template) => `You are rewriting the "${sectionLabel}" section.\n\n${template.pre_condition || ""}`,
            userInstructions
        );
    }

    async optimizeLyricPhrasing(lyricContent: string, userInstructions?: string): Promise<string> {
        return this.callUnifiedWithValidation("lyrics", "optimize-phrasing", lyricContent, undefined, userInstructions);
    }

    async condenseLyricSection(
        sectionLabel: string,
        sectionContent: string,
        userInstructions?: string
    ): Promise<string> {
        return this.callUnifiedWithValidation(
            "lyrics",
            "condense-section",
            sectionContent,
            (template) => `You are condensing the "${sectionLabel}" section into concise, singable lyrics.\n\n${template.pre_condition || ""}`,
            userInstructions
        );
    }

    // Workshop AI methods

    async generateInspirations(topic: string): Promise<string> {
        return this.callUnifiedWithValidation("workshop", "connect-inspire", topic);
    }

    async generateMindmap(topic: string, inspirations?: string): Promise<string> {
        return this.callUnifiedWithValidation("workshop", "collect-mindmap", topic, (template) => {
            let enhanced = template.pre_condition || "";
            if (inspirations) {
                enhanced += `\n\nExisting inspirations to build upon:\n${inspirations}`;
            }
            return enhanced;
        });
    }

    async generateStories(topic: string, context?: string): Promise<string> {
        return this.callUnifiedWithValidation("workshop", "collect-stories", topic, (template) => {
            let enhanced = template.pre_condition || "";
            if (context) {
                enhanced += `\n\nContext and collected material:\n${context}`;
            }
            return enhanced;
        });
    }

    async generateWordLibrary(topic: string): Promise<string> {
        return this.callUnifiedWithValidation("workshop", "collect-words", topic);
    }

    async generateRhymes(words: string): Promise<string> {
        return this.callUnifiedWithValidation("workshop", "shape-rhymes", words);
    }

    async generateDraft(collectedMaterial: string, userInstructions?: string): Promise<string> {
        return this.callUnifiedWithValidation("workshop", "shape-draft", collectedMaterial, undefined, userInstructions);
    }
}
