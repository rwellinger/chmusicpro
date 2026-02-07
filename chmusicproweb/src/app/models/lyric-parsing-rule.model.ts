export type RuleType = "cleanup" | "section";

export interface LyricParsingRule {
    id: number;
    name: string;
    description?: string;
    pattern: string;
    replacement: string;
    rule_type: RuleType;
    active: boolean;
    order: number;
    created_at: string;
    updated_at?: string;
}

export interface LyricParsingRuleCreate {
    name: string;
    description?: string;
    pattern: string;
    replacement: string;
    rule_type: RuleType;
    active: boolean;
    order: number;
}

export interface LyricParsingRuleUpdate {
    name?: string;
    description?: string;
    pattern?: string;
    replacement?: string;
    rule_type?: RuleType;
    active?: boolean;
    order?: number;
}

export interface LyricParsingRuleListResponse {
    rules: LyricParsingRule[];
    total: number;
}

export interface LyricParsingRuleReorderRequest {
    rule_ids: number[];
}
