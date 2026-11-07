/** @odoo-module **/

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, onWillStart, useState, onWillUpdateProps } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { ImagePreviewDialog } from "./image_preview_dialog";
import { _t } from "@web/core/l10n/translation";


export class ProductHeader extends Component {

    setup() {
        // Initialization code can go here if needed
        super.setup();
        this.dialog = useService("dialog");
        this.orm = useService("orm");
        this.state = useState({
            display_name : this.props.record.data.name,
        })
        onWillStart(async ()=>{
            await this.set_display_name();
        });
        onWillUpdateProps(async () => {
            await this.set_display_name();
        });
    }

    async set_display_name(){
        var record = this.props.record;
        var [vals] = await this.orm.searchRead(record.resModel, [['id','=',record.resId]], ['display_name']);
        this.state.display_name = vals.display_name;
    }

    showImagePreview(){
    this.dialog.add(ImagePreviewDialog, {
        product_id: this.props.record.data.id,
        image_ids: this.props.record.data.image_ids?._currentIds || [],
        confirmLabel: _t("Close"),
        close: () => {},
    });
}


    get image_url(){
        return `/web/image/product.template/${this.props.record.resId}/image_1920`;
    }
    get primaryImageUrl() {
        return this.props.record.data.primary_image_url ||
               `/web/image/${this.props.record.resModel}/${this.props.record.resId}/image_1920?unique=${Date.now()}`;
    }
    get displayValue() {
        const val = this.props.record.data.percentage_complete || 0;
        return Math.round(val) + "%";   // rounds to nearest integer
    }
    get progressWidth() {
        return (this.props.record.data.percentage_complete || 0) + "%";
    }
    get getBgClass() {
        let percentage = this.props.record.data.percentage_complete || 0;
        if (percentage >= 70) {
            return "oe_green_bg";
        } else if (percentage >= 55 && percentage < 70) {
            return "oe_light_green_bg";
        } else if (percentage >= 40 && percentage < 55) {
            return "oe_yellow_bg";
        } else if (percentage >= 25 && percentage < 40) {
            return "oe_orange_bg";
        } else if (percentage >= 0 && percentage < 25) {
            return "oe_red_bg";
        } else {
            return ""; // default or invalid value
        }
    }

    get categories_name() {
        const categories = this.props.record.data.pim_category_ids;
        if (categories && categories.count > 0) {
            let names = categories.records.map(cat => cat.data.display_name);
            return names.join(", ");
        }
        return "N/A";
    }

    get_quality_field_name(){
        let currentCompanyName = this.env.services.company.currentCompany.name;
        currentCompanyName = currentCompanyName.toLowerCase().replace(/\s+/g, "_");
        return `x_prod_quality_${currentCompanyName}`;
    }

//    get quality_image_url() {
//       const fieldName = this.get_quality_field_name();
//       debugger;
//        let val = this.props.record.data[fieldName];
//        if(val){
//            return `/odoopim_split_widget/static/src/icons/${val[1]}.png`;
//        }
//        return `/odoopim_split_widget/static/src/icons/A.png`;
//    }

    get quality_image_url() {
       const qualityType = this.props.record?.data.quality_type;
        if(qualityType){
            const imageName = qualityType.toUpperCase();
            return `/odoopim_split_widget/static/src/icons/${imageName}.png`;
        }
        return `/odoopim_split_widget/static/src/icons/A.png`;
    }
}

ProductHeader.template = "odoopim_split_widget.ProductHeader";
ProductHeader.props = {
    ...standardFieldProps,
};

// Register properly with component key
registry.category("fields").add("product_header", {
    component: ProductHeader,
    supportedTypes: ["char"], // pick types you want
});
