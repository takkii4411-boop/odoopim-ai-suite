/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.PXMShopPage = publicWidget.Widget.extend({
    selector: "#wrap",

    start: function () {
        this.initViewToggle();
        this.initDropdown();
        this.initFilters();
        this.initMobileFilterPanel();
        return this._super.apply(this, arguments);
    },

    // SHOW / HIDE SPINNER

    showSpinner: function () {
        $("#pxmSpinner").addClass("active");
    },

    hideSpinner: function () {
        $("#pxmSpinner").removeClass("active");
    },

    // GRID / LIST VIEW TOGGLE

    initViewToggle: function () {
        const $gridBtn = $("#gridViewBtn");
        const $listBtn = $("#listViewBtn");
        const $galleryBtn = $("#galleryViewBtn");
        const $productContainer = $("#productContainer");

        $gridBtn.on("click", function () {
            $productContainer.removeClass("list-view gallery-view");
            $gridBtn.addClass("active");
            $listBtn.removeClass("active");
            $galleryBtn.removeClass("active");
        });

        $listBtn.on("click", function () {
            $productContainer.addClass("list-view").removeClass("gallery-view");
            $listBtn.addClass("active");
            $gridBtn.removeClass("active");
            $galleryBtn.removeClass("active");
        });

        $galleryBtn.on("click", function () {
            $productContainer.addClass("gallery-view").removeClass("list-view");
            $galleryBtn.addClass("active");
            $gridBtn.removeClass("active");
            $listBtn.removeClass("active");
        });
    },

    // FIXED DROPDOWN OPEN / CLOSE

    initDropdown: function () {
        $(document).on("click", function (e) {
            if (!$(e.target).closest(".pxm-dropdown").length) {
                $(".pxm-dropdown").removeClass("open");
            }
        });

        $(".pxm-dropdown-trigger").on("click", function (e) {
            e.stopPropagation();
            const $parent = $(this).parent();
            $(".pxm-dropdown").not($parent).removeClass("open");
            $parent.toggleClass("open");
        });
    },

    // FAMILY & CATEGORY FILTER EVENTS

    initFilters: function () {
        const self = this;

        $(".family-item").on("click", function () {
            let value = $(this).data("value") || "";
            $("#family_id_input").val(value);

            $(this).closest(".pxm-dropdown")
                .find(".pxm-dropdown-value")
                .text($(this).text().trim());

            // ⭐ Show spinner before submitting the form
            self.showSpinner();
            $("#pxmFilterForm").submit();
        });

        $(".category-item").on("click", function () {
            let value = $(this).data("value") || "";
            $("#category_id_input").val(value);

            $(this).closest(".pxm-dropdown")
                .find(".pxm-dropdown-value")
                .text($(this).text().trim());

            // ⭐ Show spinner before submitting the form
            self.showSpinner();
            $("#pxmFilterForm").submit();
        });
        // Brand filter
            $(".brand-item").on("click", function () {
                let value = $(this).data("value") || "";
                $("#brand_id_input").val(value);

                $(this).closest(".pxm-dropdown")
                    .find(".pxm-dropdown-value")
                    .text($(this).text().trim());

                self.showSpinner();
                $("#pxmFilterForm").submit();
            });


    },

    // MOBILE FILTER PANEL (SLIDE-IN)

    initMobileFilterPanel: function () {
        const $toggleBtn = $("#pxmMobileFilterToggle");
        const $panel = $("#pxmMobileFilterPanel");
        const $closeBtn = $("#pxmMobileFilterClose");
        const $backdrop = $("#pxmFilterBackdrop");

        if (!$toggleBtn.length) return;

        function openPanel() {
            $panel.addClass("active");
            $backdrop.addClass("active");
            $("body").css("overflow", "hidden");
        }

        function closePanel() {
            $panel.removeClass("active");
            $backdrop.removeClass("active");
            $("body").css("overflow", "");
        }

        $toggleBtn.on("click", openPanel);
        $closeBtn.on("click", closePanel);
        $backdrop.on("click", closePanel);
    },
});


