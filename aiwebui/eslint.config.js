// @ts-check
const eslint = require("@eslint/js");
const tseslint = require("typescript-eslint");
const angular = require("angular-eslint");

module.exports = tseslint.config(
  {
    ignores: [
      "dist/**",
      "build/**",
      "node_modules/**",
      "**/*.spec.ts",
      "src/environments/**",
      "src/polyfills.ts",
      "src/test.ts",
      "src/main.ts",
      "src/assets/**"
    ]
  },
  {
    files: ["**/*.ts"],
    extends: [
      eslint.configs.recommended,
      ...tseslint.configs.recommended,
      ...tseslint.configs.stylistic,
      ...angular.configs.tsRecommended,
    ],
    processor: angular.processInlineTemplates,
    rules: {
      "@angular-eslint/directive-selector": [
        "error",
        {
          type: "attribute",
          prefix: "app",
          style: "camelCase",
        },
      ],
      "@angular-eslint/component-selector": [
        "error",
        {
          type: "element",
          prefix: "app",
          style: "kebab-case",
        },
      ],
      // Deaktiviert 'any' type warnings für bestehenden Code
      "@typescript-eslint/no-explicit-any": "off",
      // Erlaubt constructor injection (nicht nur inject())
      "@angular-eslint/prefer-inject": "warn",
      // Erlaubt inferrable types
      "@typescript-eslint/no-inferrable-types": "off",
      // Erlaubt leere Funktionen
      "@typescript-eslint/no-empty-function": "off",
      // Erlaubt unbenutzte Variablen in catch blocks
      "@typescript-eslint/no-unused-vars": ["error", { "caughtErrors": "none" }],
      // Weniger streng bei generic constructors
      "@typescript-eslint/consistent-generic-constructors": "warn",
    },
  },
  {
    files: ["**/*.html"],
    extends: [
      ...angular.configs.templateRecommended,
      ...angular.configs.templateAccessibility,
    ],
    rules: {
      // Accessibility-Regeln komplett deaktiviert für private App
      "@angular-eslint/template/click-events-have-key-events": "off",
      "@angular-eslint/template/interactive-supports-focus": "off",
    },
  }
);
