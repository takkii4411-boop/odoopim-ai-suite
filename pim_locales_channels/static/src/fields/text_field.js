/** @odoo-module **/

import { textField, TextField } from "@web/views/fields/text/text_field";
import { ChannelTranslationButton } from "@pim_locales_channels/channel_translate/channel_translate";

TextField.components = {
    ...TextField.components,
    ChannelTranslationButton
}

