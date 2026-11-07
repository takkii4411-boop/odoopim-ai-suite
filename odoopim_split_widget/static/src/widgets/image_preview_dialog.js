/** @odoo-module **/
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";
import { useState } from "@odoo/owl";

export class ImagePreviewDialog extends ConfirmationDialog {
    static template = "odoopim_split_widget.ImagePreviewDialog";
    static props = {
        ...ConfirmationDialog.props,
        contentClass: { type: String, optional: true },
        product_id: { type: Number, required: true },
        image_ids: { type: Array, required: true },
    };
    static defaultProps = {
        ...ConfirmationDialog.defaultProps,
        title: _t("Image Preview"),
    };

    setup() {
        super.setup();
        this.state = useState({ currentIndex: 0, currentImage: this.imageUrls[0]});
    }

    get imageUrls() {
        if (!this.props.image_ids || this.props.image_ids.length === 0) {
            return [`/web/image/product.template/${this.props.product_id}/image_1920`];
        }
        return this.props.image_ids.map(
            (imageId) => `/web/image/product.image/${imageId}/image_1920`
        );
    }

    get currentImage() {
        return this.imageUrls[this.state.currentIndex];
    }

    nextImage() {
        if (this.state.currentIndex < this.imageUrls.length - 1) {
            this.state.currentIndex++; // Update the index
            this.state.currentImage = this.imageUrls[this.state.currentIndex]; // Update the image
        }
    }

    prevImage() {
        if (this.state.currentIndex > 0) {
            this.state.currentIndex--; // Update the index
            this.state.currentImage = this.imageUrls[this.state.currentIndex]; // Update the image
        }
    }

    selectImage(index) {
        this.state.currentIndex = index;
        this.state.currentImage = this.imageUrls[index]
    }

    get isFirst() {
        return this.state.currentIndex === 0;
    }

    get isLast() {
        return this.state.currentIndex === this.imageUrls.length - 1;
    }
}
