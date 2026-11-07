/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

const languageCache = {};

export class AiTranslateButton extends Component {
    static template = "pim_ai_transulate.AiTranslateButton";

    static props = {
        langId: { type: Number, optional: true },
        inputSelector: { type: String, optional: true },
    };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.state = useState({ isVisible: true });

        onWillStart(async () => {
            const id = parseInt(this.props.langId);
            if (!id) return;

            if (languageCache[id]) {
                this.checkAndHide(languageCache[id]);
                return;
            }

            try {
                const result = await this.orm.read("res.lang", [id], ["code"]);
                if (result && result.length > 0) {
                    const code = result[0].code;
                    languageCache[id] = code;
                    this.checkAndHide(code);
                }
            } catch (e) {
                console.error("AiButton: Error fetching lang", e);
            }
        });
    }

    checkAndHide(code) {
        if (code === 'en_US' || code.startsWith('en_')) {
            this.state.isVisible = false;
        }
    }

    async onTranslate(ev) {
        ev.stopPropagation();
        ev.preventDefault();

        const btn = ev.currentTarget;

        // --- UPDATED LOGIC TO FIND INPUT ---
        // Since we are inside a <td>, the input is a sibling of the button.
        // We look at the parent (TD) and find the input inside it.
        const parentContainer = btn.parentElement;
        const inputField = parentContainer.querySelector("input[type='text']");

        const sourceText = inputField ? inputField.value : null;

        if (!sourceText) {
            this.notification.add("Please enter text to translate.", { type: "warning" });
            return;
        }

        const originalOpacity = btn.style.opacity;
        btn.style.opacity = "0.5";
        btn.style.pointerEvents = "none";

        try {
            console.log(`🚀 AI Component: Sending "${sourceText}" (LangID: ${this.props.langId})`);

            const translatedText = await this.orm.call(
                "ai.enrichment.config",
                "perform_ai_translation",
                [sourceText, this.props.langId]
            );

            if (translatedText) {
                inputField.value = translatedText;
                inputField.dispatchEvent(new Event("change", { bubbles: true }));
                inputField.dispatchEvent(new Event("input", { bubbles: true }));
                this.notification.add("Translated!", { type: "success" });
            } else {
                this.notification.add("AI returned no result.", { type: "warning" });
            }

        } catch (error) {
            console.error("AI Error:", error);
            const msg = error.data?.message || error.message;
            this.notification.add(msg, { type: "danger" });
        } finally {
            btn.style.opacity = originalOpacity || "1";
            btn.style.pointerEvents = "auto";
        }
    }
}