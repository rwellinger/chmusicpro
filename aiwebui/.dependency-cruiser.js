/** @type {import('dependency-cruiser').IConfiguration} */
module.exports = {
  forbidden: [
    /* ============================================================================
     * CRITICAL ARCHITECTURE RULES (from CLAUDE.md)
     * ============================================================================ */

    {
      name: 'services-no-components',
      severity: 'error',
      comment: 'Services must not depend on UI components (violation of separation of concerns)',
      from: {
        path: '^src/app/services',
      },
      to: {
        path: '^src/app/(pages|components)',
      },
    },

    {
      name: 'services-use-api-config',
      severity: 'error',
      comment: 'Services MUST use ApiConfigService, NOT environment.apiUrl directly (CLAUDE.md: API Routing & Security)',
      from: {
        path: '^src/app/services',
        pathNot: 'api-config\\.service\\.ts$',
      },
      to: {
        path: 'environments/environment',
      },
    },

    {
      name: 'no-hardcoded-urls',
      severity: 'error',
      comment: 'NEVER hardcode API URLs - use ApiConfigService.endpoints (CLAUDE.md: API Routing)',
      from: {
        path: '^src/app/services',
      },
      to: {
        path: 'environments/environment',
      },
    },

    {
      name: 'no-circular',
      severity: 'warn',
      comment: 'Circular dependencies make code harder to understand and test',
      from: {},
      to: {
        circular: true,
      },
    },

    {
      name: 'models-independent',
      severity: 'error',
      comment: 'Models (interfaces/types) should not depend on services or components',
      from: {
        path: '^src/app/models',
      },
      to: {
        path: '^src/app/(services|components|pages)',
      },
    },

    {
      name: 'guards-no-components',
      severity: 'error',
      comment: 'Guards should only depend on services, not UI components',
      from: {
        path: '^src/app/guards',
      },
      to: {
        path: '^src/app/(components|pages)',
      },
    },

    {
      name: 'interceptors-no-components',
      severity: 'error',
      comment: 'Interceptors should only depend on services, not UI components',
      from: {
        path: '^src/app/interceptors',
      },
      to: {
        path: '^src/app/(components|pages)',
      },
    },

    /* ============================================================================
     * OLLAMA + PROMPT TEMPLATE INTEGRATION RULES (MANDATORY WORKFLOW)
     * ============================================================================ */

    {
      name: 'ollama-use-chat-service',
      severity: 'error',
      comment: 'ALL Ollama calls MUST go through ChatService.validateAndCallUnified (CLAUDE.md: Ollama + Prompt Template Integration)',
      from: {
        path: '^src/app/services',
        pathNot: 'chat\\.service\\.ts$',
      },
      to: {
        path: 'ollama',
        pathNot: '(^|/)node_modules/',
      },
    },
  ],

  options: {
    /* Modules from which to start detecting dependencies */
    doNotFollow: {
      path: 'node_modules',
    },

    /* Which modules to include in the report */
    includeOnly: {
      path: '^src/app',
    },

    /* TypeScript & Angular support */
    tsConfig: {
      fileName: 'tsconfig.json',
    },

    /* Output format when running depcruise */
    reporterOptions: {
      dot: {
        collapsePattern: '^src/app/[^/]+',
      },
      text: {
        highlightFocused: true,
      },
    },
  },
};
