/** @odoo-module **/

import { CharField } from "@web/views/fields/char/char_field";
import { ChannelTranslationButton } from "@pim_locales_channels/channel_translate/channel_translate";

CharField.components = {
    ...CharField.components,
    ChannelTranslationButton
}