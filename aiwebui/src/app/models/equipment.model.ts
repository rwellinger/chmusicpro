/**
 * Equipment Models - TypeScript interfaces and enums for equipment management.
 */

export enum EquipmentType {
    SOFTWARE = "Software",
    PLUGIN = "Plugin"
}

export enum LicenseManagement {
    ONLINE = "online",
    ILOK = "ilok",
    LICENSE_KEY = "license_key",
    OTHER = "other"
}

export enum EquipmentStatus {
    ACTIVE = "active",
    TRIAL = "trial",
    EXPIRED = "expired",
    ARCHIVED = "archived"
}

export interface Equipment {
    id: string;
    type: EquipmentType;
    name: string;
    version?: string;
    description?: string;
    software_tags?: string;
    plugin_tags?: string;
    manufacturer?: string;
    url?: string;
    username?: string;
    password?: string;
    license_management?: LicenseManagement;
    license_key?: string;
    license_description?: string;
    purchase_date?: string; // ISO format
    price?: string; // Format: "299.99 EUR"
    system_requirements?: string;
    status: EquipmentStatus;
    created_at: string; // ISO format
    updated_at?: string; // ISO format
}

export interface EquipmentListItem {
    id: string;
    type: EquipmentType;
    name: string;
    manufacturer?: string;
    status: EquipmentStatus;
    created_at: string;
}

export interface EquipmentListResponse {
    data: EquipmentListItem[];
    pagination: {
        total: number;
        limit: number;
        offset: number;
        has_more: boolean;
    };
}

export interface EquipmentDetailResponse {
    data: Equipment;
    message?: string;
}

export interface EquipmentCreateRequest {
    type: EquipmentType;
    name: string;
    version?: string;
    description?: string;
    software_tags?: string;
    plugin_tags?: string;
    manufacturer?: string;
    url?: string;
    username?: string;
    password?: string;
    license_management?: LicenseManagement;
    license_key?: string;
    license_description?: string;
    purchase_date?: string; // ISO format
    price?: string;
    system_requirements?: string;
    status?: EquipmentStatus;
}

export interface EquipmentUpdateRequest {
    name?: string;
    version?: string;
    description?: string;
    software_tags?: string;
    plugin_tags?: string;
    manufacturer?: string;
    url?: string;
    username?: string;
    password?: string;
    license_management?: LicenseManagement;
    license_key?: string;
    license_description?: string;
    purchase_date?: string;
    price?: string;
    system_requirements?: string;
    status?: EquipmentStatus;
}

// Attachment interfaces
export interface EquipmentAttachment {
    id: string;
    filename: string;
    file_size: number;
    content_type: string;
    uploaded_at: string; // ISO format
    download_url: string; // Backend proxy URL
}

export interface EquipmentAttachmentListResponse {
    data: EquipmentAttachment[];
}

export interface EquipmentAttachmentUploadResponse {
    data: EquipmentAttachment;
    message: string;
}
