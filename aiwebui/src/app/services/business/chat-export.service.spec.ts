import {TestBed} from "@angular/core/testing";
import {ChatExportService} from "./chat-export.service";
import {ConversationService} from "./conversation.service";
import {Conversation, Message} from "../../models/conversation.model";
import {of} from "rxjs";

describe("ChatExportService", () => {
    let service: ChatExportService;
    let conversationServiceSpy: jasmine.SpyObj<ConversationService>;

    beforeEach(() => {
        // Create spy for ConversationService
        const spy = jasmine.createSpyObj("ConversationService", ["getConversationForExport"]);

        TestBed.configureTestingModule({
            providers: [
                ChatExportService,
                {provide: ConversationService, useValue: spy}
            ]
        });

        service = TestBed.inject(ChatExportService);
        conversationServiceSpy = TestBed.inject(ConversationService) as jasmine.SpyObj<ConversationService>;
    });

    it("should be created", () => {
        expect(service).toBeTruthy();
    });

    describe("generateMarkdownContent (via exportToMarkdown)", () => {
        let mockConversation: Conversation;
        let mockMessages: Message[];
        let downloadSpy: jasmine.Spy;

        beforeEach(() => {
            // Mock conversation
            mockConversation = {
                id: "123",
                title: "Test Chat",
                model: "gpt-4",
                provider: "external",
                system_context: "You are a helpful assistant",
                current_token_count: 150,
                context_window_size: 8000,
                created_at: "2024-01-15T10:00:00Z",
                updated_at: "2024-01-15T10:30:00Z",
                user_id: "user-1"
            } as Conversation;

            // Mock messages
            mockMessages = [
                {
                    id: "msg-1",
                    conversation_id: "123",
                    role: "user",
                    content: "Hello, how are you?",
                    created_at: "2024-01-15T10:00:00Z",
                    token_count: 10,
                    is_summary: false
                } as Message,
                {
                    id: "msg-2",
                    conversation_id: "123",
                    role: "assistant",
                    content: "I am doing well, thank you!",
                    created_at: "2024-01-15T10:01:00Z",
                    token_count: 10,
                    is_summary: false
                } as Message
            ];

            // Spy on private methods via exportToMarkdown
            downloadSpy = spyOn<any>(service as any, "downloadFile");
        });

        it("should generate markdown with conversation title", () => {
            service.exportToMarkdown(mockConversation, mockMessages);

            const generatedContent = downloadSpy.calls.mostRecent().args[0];
            expect(generatedContent).toContain("# Test Chat");
        });

        it("should include model and provider metadata", () => {
            service.exportToMarkdown(mockConversation, mockMessages);

            const generatedContent = downloadSpy.calls.mostRecent().args[0];
            expect(generatedContent).toContain("**Model:** gpt-4");
            expect(generatedContent).toContain("**Provider:** external");
        });

        it("should include token count information", () => {
            service.exportToMarkdown(mockConversation, mockMessages);

            const generatedContent = downloadSpy.calls.mostRecent().args[0];
            expect(generatedContent).toContain("**Tokens:** 150 / 8000");
        });

        it("should include system context if present", () => {
            service.exportToMarkdown(mockConversation, mockMessages);

            const generatedContent = downloadSpy.calls.mostRecent().args[0];
            expect(generatedContent).toContain("## System Context");
            expect(generatedContent).toContain("You are a helpful assistant");
        });

        it("should not include system context section if not present", () => {
            mockConversation.system_context = undefined;
            service.exportToMarkdown(mockConversation, mockMessages);

            const generatedContent = downloadSpy.calls.mostRecent().args[0];
            expect(generatedContent).not.toContain("## System Context");
        });

        it("should format user messages correctly", () => {
            service.exportToMarkdown(mockConversation, mockMessages);

            const generatedContent = downloadSpy.calls.mostRecent().args[0];
            expect(generatedContent).toContain("**USER**");
            expect(generatedContent).toContain("Hello, how are you?");
        });

        it("should format assistant messages correctly", () => {
            service.exportToMarkdown(mockConversation, mockMessages);

            const generatedContent = downloadSpy.calls.mostRecent().args[0];
            expect(generatedContent).toContain("**ASSISTANT**");
            expect(generatedContent).toContain("I am doing well, thank you!");
        });

        it("should skip system messages in output", () => {
            const messagesWithSystem = [
                ...mockMessages,
                {
                    id: "msg-3",
                    conversation_id: "123",
                    role: "system",
                    content: "System message",
                    created_at: "2024-01-15T10:02:00Z",
                    token_count: 5,
                    is_summary: false
                } as Message
            ];

            service.exportToMarkdown(mockConversation, messagesWithSystem);

            const generatedContent = downloadSpy.calls.mostRecent().args[0];
            expect(generatedContent).not.toContain("System message");
        });

        it("should include message separators", () => {
            service.exportToMarkdown(mockConversation, mockMessages);

            const generatedContent = downloadSpy.calls.mostRecent().args[0];
            const separatorCount = (generatedContent.match(/---/g) || []).length;
            expect(separatorCount).toBeGreaterThan(0);
        });
    });

    describe("generateFilename (via exportToMarkdown)", () => {
        let mockConversation: Conversation;
        let mockMessages: Message[];
        let downloadSpy: jasmine.Spy;

        beforeEach(() => {
            mockConversation = {
                id: "123",
                title: "Test Chat",
                model: "gpt-4",
                created_at: "2024-01-15T10:00:00Z",
                updated_at: "2024-01-15T10:30:00Z",
                user_id: "user-1"
            } as Conversation;

            mockMessages = [];
            downloadSpy = spyOn<any>(service as any, "downloadFile");
        });

        it("should generate filename with sanitized title", () => {
            mockConversation.title = "My Test Chat!";
            service.exportToMarkdown(mockConversation, mockMessages);

            const filename = downloadSpy.calls.mostRecent().args[1];
            expect(filename).toMatch(/^chat-My-Test-Chat-\d{4}-\d{2}-\d{2}\.md$/);
        });

        it("should remove special characters from filename", () => {
            mockConversation.title = "Test@Chat#With$Special%Characters!";
            service.exportToMarkdown(mockConversation, mockMessages);

            const filename = downloadSpy.calls.mostRecent().args[1];
            expect(filename).not.toContain("@");
            expect(filename).not.toContain("#");
            expect(filename).not.toContain("$");
            expect(filename).not.toContain("%");
            expect(filename).not.toContain("!");
        });

        it("should replace spaces with hyphens", () => {
            mockConversation.title = "Test Chat With Spaces";
            service.exportToMarkdown(mockConversation, mockMessages);

            const filename = downloadSpy.calls.mostRecent().args[1];
            expect(filename).toContain("Test-Chat-With-Spaces");
        });

        it("should preserve German umlauts", () => {
            mockConversation.title = "Testöäü ÖÄÜß Chat";
            service.exportToMarkdown(mockConversation, mockMessages);

            const filename = downloadSpy.calls.mostRecent().args[1];
            expect(filename).toContain("öäü");
            expect(filename).toContain("ÖÄÜß");
        });

        it("should truncate long titles to 50 characters", () => {
            mockConversation.title = "A".repeat(100);
            service.exportToMarkdown(mockConversation, mockMessages);

            const filename = downloadSpy.calls.mostRecent().args[1];
            const titlePart = filename.replace(/^chat-/, "").replace(/-\d{4}-\d{2}-\d{2}\.md$/, "");
            expect(titlePart.length).toBeLessThanOrEqual(50);
        });

        it("should include date in ISO format", () => {
            service.exportToMarkdown(mockConversation, mockMessages);

            const filename = downloadSpy.calls.mostRecent().args[1];
            expect(filename).toMatch(/-\d{4}-\d{2}-\d{2}\.md$/);
        });

        it("should have .md extension", () => {
            service.exportToMarkdown(mockConversation, mockMessages);

            const filename = downloadSpy.calls.mostRecent().args[1];
            expect(filename).toMatch(/\.md$/);
        });
    });

    describe("exportFullToMarkdown", () => {
        it("should fetch full conversation including archived messages", async () => {
            const mockResponse = {
                conversation: {
                    id: "123",
                    title: "Test Chat",
                    model: "gpt-4",
                    created_at: "2024-01-15T10:00:00Z"
                } as Conversation,
                messages: [
                    {
                        id: "msg-1",
                        conversation_id: "123",
                        role: "user",
                        content: "Test message",
                        created_at: "2024-01-15T10:00:00Z",
                        token_count: 5,
                        is_summary: false
                    } as Message
                ]
            };

            conversationServiceSpy.getConversationForExport.and.returnValue(of(mockResponse));
            spyOn<any>(service as any, "downloadFile");

            await service.exportFullToMarkdown("123", "Test Chat");

            expect(conversationServiceSpy.getConversationForExport).toHaveBeenCalledWith("123");
        });

        it("should filter out summary messages", async () => {
            const mockResponse = {
                conversation: {
                    id: "123",
                    title: "Test Chat",
                    model: "gpt-4",
                    created_at: "2024-01-15T10:00:00Z"
                } as Conversation,
                messages: [
                    {
                        id: "msg-1",
                        conversation_id: "123",
                        role: "user",
                        content: "Real message",
                        created_at: "2024-01-15T10:00:00Z",
                        token_count: 5,
                        is_summary: false
                    } as Message,
                    {
                        id: "msg-2",
                        conversation_id: "123",
                        role: "assistant",
                        content: "Summary message",
                        created_at: "2024-01-15T10:01:00Z",
                        token_count: 5,
                        is_summary: true
                    } as Message
                ]
            };

            conversationServiceSpy.getConversationForExport.and.returnValue(of(mockResponse));
            const downloadSpy = spyOn<any>(service as any, "downloadFile");

            await service.exportFullToMarkdown("123", "Test Chat");

            const generatedContent = downloadSpy.calls.mostRecent().args[0];
            expect(generatedContent).toContain("Real message");
            expect(generatedContent).not.toContain("Summary message");
        });

        it("should throw error if export fails", async () => {
            // Suppress console.error output during error handling test
            spyOn(console, "error");

            conversationServiceSpy.getConversationForExport.and.throwError("Network error");

            await expectAsync(
                service.exportFullToMarkdown("123", "Test Chat")
            ).toBeRejected();

            // Verify error was logged
            expect(console.error).toHaveBeenCalledWith(
                "Error exporting full conversation:",
                jasmine.any(Error)
            );
        });
    });
});
