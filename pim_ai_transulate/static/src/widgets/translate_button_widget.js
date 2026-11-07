/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { onMounted, onPatched } from "@odoo/owl";
import { AttributeChannelLocalePop } from "@pim_locales_channels/attribute_channel_locale_action/channel_locale_attribute";
import { AiTranslateButton } from "../components/ai_translate_button";

// Register component
AttributeChannelLocalePop.components = {
    ...AttributeChannelLocalePop.components,
    AiTranslateButton
};

patch(AttributeChannelLocalePop.prototype, {

    setup() {
        super.setup();
        this.orm = useService("orm");

        // --- HIDE ENGLISH BUTTONS LOGIC ---
        this.hideEnglishButtons = async () => {
            try {
                // 1. Find English ID from DB
                const result = await this.orm.searchRead("res.lang", [["code", "=", "en_US"]], ["id"]);

                if (result.length > 0) {
                    const engId = result[0].id;

                    // 2. Find all inputs belonging to English
                    const englishInputs = document.querySelectorAll(`input[data-lang-id='${engId}']`);

                    // 3. Hide the button
                    englishInputs.forEach(input => {
                        // --- FIX HERE ---
                        // Use parentElement so it works for both <div> and <td>
                        const parent = input.parentElement;

                        if (parent) {
                            const btn = parent.querySelector('.ai-translate-btn');
                            if (btn) {
                                btn.style.display = 'none'; // Force hide
                            }
                        }
                    });
                }
            } catch (e) {
                console.error("Failed to hide English buttons", e);
            }
        };

        // Run logic on mount and updates
        onMounted(() => {
            this.hideEnglishButtons();
        });

        onPatched(() => {
            this.hideEnglishButtons();
        });
    },

    // --- GROUPED FIELDS FIX ---
    onValueChange(ev) {
        const val = ev.target.value;
        const fieldName = ev.target.dataset.field;
        const langId = parseInt(ev.target.dataset.langId);
        const platform = ev.target.dataset.platform;

        let row = null;
        const platformData = this.state.datas[platform];

        if (!platformData) return;

        if (Array.isArray(platformData)) {
            row = platformData.find(r => r.x_field_name === fieldName);
        } else {
            const allGroups = Object.values(platformData);
            for (const groupArray of allGroups) {
                if (Array.isArray(groupArray)) {
                    const found = groupArray.find(r => r.x_field_name === fieldName);
                    if (found) {
                        row = found;
                        break;
                    }
                }
            }
        }

        if (row && row.langs && row.langs[langId]) {
            row.langs[langId].x_value = val;
        }

        if (!this.state.changes[platform]) {
            this.state.changes[platform] = [];
        }

        const existing = this.state.changes[platform].find(
            c => c.x_field_name === fieldName && c.x_lang_id === langId
        );

        if (existing) {
            existing.x_value = val;
        } else {
            this.state.changes[platform].push({
                x_res_id: this.props.resId,
                x_res_model: this.props.resModel,
                x_field_name: fieldName,
                x_lang_id: langId,
                x_value: val,
            });
        }
    }
});