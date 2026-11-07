/** @odoo-module **/

import { registry } from "@web/core/registry";
import { ImageField } from "@web/views/fields/image/image_field";
import { useService } from "@web/core/utils/hooks";
import { useState, useRef } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { getDataURLFromFile } from "@web/core/utils/urls";
import { isBinarySize } from "@web/core/utils/binary";
import { url } from "@web/core/utils/urls";

const PLACEHOLDER = "/web/static/img/placeholder.png";

export class ImageDNDField extends ImageField {
    setup() {
        super.setup();
        this.notification = useService("notification");
        
        // Specific reference for our hidden input
        this.fileInputRef = useRef("file_input_dnd");
        
        this.state = useState({
            isDragging: false,
            preview: null, // Stores immediate preview URL
        });
    }

    get imageUrl() {
      
        if (this.state.preview) {
            return this.state.preview;
        }

        const value = this.props.record.data[this.props.name];

        if (!value) {
            return PLACEHOLDER;
        }

        if (isBinarySize(value)) {
            return url("/web/image", {
                model: this.props.record.resModel,
                id: this.props.record.resId,
                field: this.props.name,
                unique: this.props.record.data.__last_update,
            });
        }

        if (typeof value === "string") {
            // Check if it already has the prefix
            if (value.startsWith("data:image")) {
                return value;
            }
            // Add prefix for display
            return `data:image/png;base64,${value}`;
        }

        return PLACEHOLDER;
    }


    onFileOpen() {
        // Trigger the hidden file input
        if (this.fileInputRef.el) {
            this.fileInputRef.el.click();
        }
    }

    async onFileRemove() {
        this.state.preview = null;
        await this.props.record.update({ [this.props.name]: false });
    }

    onDragEnter(ev) {
        ev.preventDefault();
        ev.stopPropagation();
        this.state.isDragging = true;
    }

    onDragLeave(ev) {
        ev.preventDefault();
        ev.stopPropagation();
        // Prevent flickering when hovering child elements
        if (ev.currentTarget.contains(ev.relatedTarget)) return;
        this.state.isDragging = false;
    }

    onDragOver(ev) {
        ev.preventDefault();
        ev.stopPropagation();
        this.state.isDragging = true;
    }

    async onDrop(ev) {
        ev.preventDefault();
        ev.stopPropagation();
        this.state.isDragging = false;

        const files = ev.dataTransfer.files;
        if (!files || files.length === 0) return;
        
        await this.processUpload(files[0]);
    }


    async onFileInputChange(ev) {
        const files = ev.target.files;
        if (!files || files.length === 0) return;
        
        await this.processUpload(files[0]);
        
        ev.target.value = ""; 
    }

    async processUpload(file) {
        if (!this.isValidFile(file)) {
            this.notification.add(_t("Invalid file type! Please upload an Image."), {
                type: "danger",
            });
            return;
        }

        try {
           
            const dataUrl = await getDataURLFromFile(file);

         
            this.state.preview = dataUrl;

           
            const base64Data = dataUrl.split(',')[1];

           
            await this.props.record.update({ [this.props.name]: base64Data });
            
        } catch (error) {
            
            this.notification.add(_t("Could not process file."), { type: "danger" });
        }
    }

    isValidFile(file) {
        const allowed = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml', 'video/mp4'];
        return allowed.includes(file.type);
    }
}

ImageDNDField.template = "pim_ext.ImageDNDField";

ImageDNDField.props = { ...ImageField.props };

export const imageDNDField = {
    component: ImageDNDField,
    displayName: _t("Image Drag & Drop"),
    supportedTypes: ["binary"],
};

registry.category("fields").add("image_dnd", imageDNDField);
