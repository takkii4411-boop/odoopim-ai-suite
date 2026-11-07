/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.PimProductActions = publicWidget.Widget.extend({
    selector: ".pim-actions",

    events: {
        "click .pim-export-pdf": "_onExportPDF",
        "click .pim-export-excel": "_onExportExcel",
    },

    _onExportPDF(ev) {
        ev.preventDefault();
        const productId = ev.currentTarget.dataset.productId;
        window.location.href = `/pim/product/${productId}/export/pdf`;
    },

    _onExportExcel(ev) {
        ev.preventDefault();
        const productId = ev.currentTarget.dataset.productId;
        const url = `/pim/product/${productId}/export/excel`;
        window.location.href = url;
    },
});
