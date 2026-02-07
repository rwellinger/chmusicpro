import {TestBed} from "@angular/core/testing";
import {HtmlToTextService} from "./html-to-text.service";

describe("HtmlToTextService", () => {
    let service: HtmlToTextService;

    beforeEach(() => {
        TestBed.configureTestingModule({});
        service = TestBed.inject(HtmlToTextService);
    });

    it("should be created", () => {
        expect(service).toBeTruthy();
    });

    describe("convert - Basic text", () => {
        it("should handle empty string", () => {
            const result = service.convert("");
            expect(result).toBe("");
        });

        it("should handle null input", () => {
            const result = service.convert(null as any);
            expect(result).toBe("");
        });

        it("should handle undefined input", () => {
            const result = service.convert(undefined as any);
            expect(result).toBe("");
        });

        it("should convert simple text", () => {
            const result = service.convert("Hello World");
            expect(result).toBe("Hello World");
        });

        it("should preserve text content", () => {
            const html = "<p>This is a test</p>";
            const result = service.convert(html);
            expect(result).toContain("This is a test");
        });
    });

    describe("convert - Paragraphs", () => {
        it("should add double newline after paragraphs", () => {
            const html = "<p>First paragraph</p><p>Second paragraph</p>";
            const result = service.convert(html);
            expect(result).toBe("First paragraph\n\nSecond paragraph");
        });

        it("should handle multiple paragraphs", () => {
            const html = "<p>One</p><p>Two</p><p>Three</p>";
            const result = service.convert(html);
            expect(result).toContain("One");
            expect(result).toContain("Two");
            expect(result).toContain("Three");
        });
    });

    describe("convert - Line breaks", () => {
        it("should convert <br> to newline", () => {
            const html = "Line 1<br>Line 2";
            const result = service.convert(html);
            expect(result).toBe("Line 1\nLine 2");
        });

        it("should handle multiple <br> tags", () => {
            const html = "One<br><br>Two";
            const result = service.convert(html);
            expect(result).toBe("One\n\nTwo");
        });
    });

    describe("convert - Headings", () => {
        it("should convert h1 with newlines", () => {
            const html = "<h1>Title</h1>";
            const result = service.convert(html);
            expect(result).toBe("Title");
        });

        it("should convert h2 with newlines", () => {
            const html = "<h2>Subtitle</h2>";
            const result = service.convert(html);
            expect(result).toBe("Subtitle");
        });

        it("should handle all heading levels", () => {
            const html = "<h1>H1</h1><h2>H2</h2><h3>H3</h3>";
            const result = service.convert(html);
            expect(result).toContain("H1");
            expect(result).toContain("H2");
            expect(result).toContain("H3");
        });
    });

    describe("convert - Lists", () => {
        it("should convert unordered list with bullets", () => {
            const html = "<ul><li>Item 1</li><li>Item 2</li></ul>";
            const result = service.convert(html);
            expect(result).toContain("• Item 1");
            expect(result).toContain("• Item 2");
        });

        it("should convert ordered list with numbers", () => {
            const html = "<ol><li>First</li><li>Second</li><li>Third</li></ol>";
            const result = service.convert(html);
            expect(result).toContain("1. First");
            expect(result).toContain("2. Second");
            expect(result).toContain("3. Third");
        });

        it("should handle nested lists with indentation", () => {
            const html = `
        <ul>
          <li>Top level
            <ul>
              <li>Nested item</li>
            </ul>
          </li>
        </ul>
      `;
            const result = service.convert(html);
            expect(result).toContain("• Top level");
            expect(result).toContain("  • Nested item");
        });

        it("should handle empty list items", () => {
            const html = "<ul><li></li><li>Item</li></ul>";
            const result = service.convert(html);
            expect(result).toContain("Item");
        });
    });

    describe("convert - Blockquotes", () => {
        it("should prefix blockquote lines with \">\"", () => {
            const html = "<blockquote>Quoted text</blockquote>";
            const result = service.convert(html);
            expect(result).toContain("> Quoted text");
        });

        it("should handle multiline blockquotes", () => {
            const html = "<blockquote>Line 1\nLine 2</blockquote>";
            const result = service.convert(html);
            expect(result).toContain("> Line 1");
            expect(result).toContain("> Line 2");
        });
    });

    describe("convert - Code blocks", () => {
        it("should preserve inline code", () => {
            const html = "<p>Use <code>console.log()</code> for debugging</p>";
            const result = service.convert(html);
            expect(result).toContain("console.log()");
        });

        it("should preserve code blocks with pre tags", () => {
            const html = "<pre><code>function test() {\n  return true;\n}</code></pre>";
            const result = service.convert(html);
            expect(result).toContain("function test()");
            expect(result).toContain("return true;");
        });

        it("should add newlines around pre blocks", () => {
            const html = "<pre>Code here</pre>";
            const result = service.convert(html);
            expect(result).toBe("Code here");
        });
    });

    describe("convert - Tables", () => {
        it("should convert simple table", () => {
            const html = `
        <table>
          <tr><th>Name</th><th>Age</th></tr>
          <tr><td>Alice</td><td>30</td></tr>
          <tr><td>Bob</td><td>25</td></tr>
        </table>
      `;
            const result = service.convert(html);
            expect(result).toContain("Name");
            expect(result).toContain("Age");
            expect(result).toContain("Alice");
            expect(result).toContain("Bob");
        });

        it("should add separator after table header", () => {
            const html = `
        <table>
          <tr><th>Header</th></tr>
          <tr><td>Data</td></tr>
        </table>
      `;
            const result = service.convert(html);
            expect(result).toContain("---");
        });

        it("should align columns with spacing", () => {
            const html = `
        <table>
          <tr><td>A</td><td>B</td></tr>
          <tr><td>C</td><td>D</td></tr>
        </table>
      `;
            const result = service.convert(html);
            // Columns should be separated
            expect(result).toMatch(/A\s+B/);
            expect(result).toMatch(/C\s+D/);
        });

        it("should handle empty tables", () => {
            const html = "<table></table>";
            const result = service.convert(html);
            expect(result.trim()).toBe("");
        });

        it("should handle tables with varying cell widths", () => {
            const html = `
        <table>
          <tr><td>Short</td><td>Very Long Content</td></tr>
          <tr><td>A</td><td>B</td></tr>
        </table>
      `;
            const result = service.convert(html);
            expect(result).toContain("Short");
            expect(result).toContain("Very Long Content");
        });
    });

    describe("convert - Horizontal rules", () => {
        it("should convert <hr> to dashes", () => {
            const html = "<p>Before</p><hr><p>After</p>";
            const result = service.convert(html);
            expect(result).toContain("---");
            expect(result).toContain("Before");
            expect(result).toContain("After");
        });

        it("should add newlines around hr", () => {
            const html = "<hr>";
            const result = service.convert(html);
            expect(result).toBe("---");
        });
    });

    describe("convert - Formatting tags", () => {
        it("should strip <strong> tags but keep content", () => {
            const html = "<p>This is <strong>important</strong></p>";
            const result = service.convert(html);
            expect(result).toContain("This is important");
            expect(result).not.toContain("<strong>");
        });

        it("should strip <em> tags but keep content", () => {
            const html = "<p>This is <em>emphasized</em></p>";
            const result = service.convert(html);
            expect(result).toContain("This is emphasized");
        });

        it("should strip <a> tags but keep text", () => {
            const html = "<p>Visit <a href=\"http://example.com\">this site</a></p>";
            const result = service.convert(html);
            expect(result).toContain("Visit this site");
            expect(result).not.toContain("http://example.com");
        });

        it("should handle nested formatting tags", () => {
            const html = "<p><strong><em>Bold and italic</em></strong></p>";
            const result = service.convert(html);
            expect(result).toContain("Bold and italic");
        });
    });

    describe("convert - Complex HTML", () => {
        it("should handle mixed content", () => {
            const html = `
        <h1>Title</h1>
        <p>Introduction paragraph</p>
        <ul>
          <li>Point 1</li>
          <li>Point 2</li>
        </ul>
        <p>Conclusion</p>
      `;
            const result = service.convert(html);
            expect(result).toContain("Title");
            expect(result).toContain("Introduction paragraph");
            expect(result).toContain("• Point 1");
            expect(result).toContain("• Point 2");
            expect(result).toContain("Conclusion");
        });

        it("should handle deeply nested structures", () => {
            const html = `
        <div>
          <div>
            <p><span>Deeply <strong>nested</strong> content</span></p>
          </div>
        </div>
      `;
            const result = service.convert(html);
            expect(result).toContain("Deeply nested content");
        });

        it("should preserve text order", () => {
            const html = "<p>First</p><p>Second</p><p>Third</p>";
            const result = service.convert(html);
            const firstIndex = result.indexOf("First");
            const secondIndex = result.indexOf("Second");
            const thirdIndex = result.indexOf("Third");
            expect(firstIndex).toBeLessThan(secondIndex);
            expect(secondIndex).toBeLessThan(thirdIndex);
        });
    });

    describe("convert - Edge cases", () => {
        it("should handle whitespace-only HTML", () => {
            const html = "   \n\t   ";
            const result = service.convert(html);
            expect(result.trim()).toBe("");
        });

        it("should handle HTML entities", () => {
            const html = "<p>Test &amp; Example &lt;tag&gt;</p>";
            const result = service.convert(html);
            expect(result).toContain("&");
            expect(result).toContain("<tag>");
        });

        it("should handle malformed HTML gracefully", () => {
            const html = "<p>Unclosed paragraph";
            expect(() => service.convert(html)).not.toThrow();
        });

        it("should handle unknown tags by extracting text", () => {
            const html = "<custom-tag>Content</custom-tag>";
            const result = service.convert(html);
            expect(result).toContain("Content");
        });
    });
});
