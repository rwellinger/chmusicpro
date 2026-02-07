import {Injectable} from "@angular/core";

export interface TemperatureOption {
    value: number;
    labelKey: string;
    descriptionKey: string;
}

@Injectable({
    providedIn: "root"
})
export class TemperatureOptionsService {
    private readonly temperatureOptions: TemperatureOption[] = [
        {
            value: 0.1,
            labelKey: "promptTemplateEditor.temperature.veryPrecise",
            descriptionKey: "promptTemplateEditor.temperature.veryPreciseDesc"
        },
        {
            value: 0.3,
            labelKey: "promptTemplateEditor.temperature.slightlyVariable",
            descriptionKey: "promptTemplateEditor.temperature.slightlyVariableDesc"
        },
        {
            value: 0.5,
            labelKey: "promptTemplateEditor.temperature.balanced",
            descriptionKey: "promptTemplateEditor.temperature.balancedDesc"
        },
        {
            value: 0.7,
            labelKey: "promptTemplateEditor.temperature.creative",
            descriptionKey: "promptTemplateEditor.temperature.creativeDesc"
        },
        {
            value: 0.9,
            labelKey: "promptTemplateEditor.temperature.veryCreative",
            descriptionKey: "promptTemplateEditor.temperature.veryCreativeDesc"
        }
    ];

    /**
     * Get all available temperature options
     */
    getOptions(): TemperatureOption[] {
        return this.temperatureOptions;
    }

    /**
     * Find temperature option by value
     */
    findByValue(value: number | null | undefined): TemperatureOption | undefined {
        if (value === null || value === undefined) {
            return undefined;
        }
        return this.temperatureOptions.find(opt => opt.value === value);
    }

    /**
     * Get formatted label for temperature value (e.g., "0.7 - Creative")
     * @param value Temperature value
     * @param translateFn Translation function from TranslateService
     * @returns Formatted label or undefined if not found
     */
    getLabel(value: number | null | undefined, translateFn: (key: string) => string): string | undefined {
        const option = this.findByValue(value);
        if (!option) {
            return undefined;
        }
        return `${option.value} - ${translateFn(option.labelKey)}`;
    }
}
