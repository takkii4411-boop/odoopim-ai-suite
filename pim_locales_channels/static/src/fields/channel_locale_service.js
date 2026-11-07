/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

const ChannelLocaleService = {
    dependencies: ["orm"],

    start(env, { orm }) {
        const cache = new Map(); // companyId → data

        function buildCombinations(channels = [], langs = []) {
            const result = [];
            for (const channel of channels) {
                for (const lang of langs) {
                    result.push({
                        channel,
                        lang,
                        key: `${channel.id}-${lang.code}`,     // unique key (critical!)
                        channelId: channel.id,
                        langId: lang.id,
                        langCode: lang.code,
                        value: null,
                        display: `${channel.name} → ${lang.name}`,
                    });
                }
            }
            return result;
        }

        async function getChannelLocaleData({ record, fieldName }) {
            if (!record || !fieldName) return null;
            const companyId = record.currentCompanyId
            const model = record.model.resModel;
            var [ fieldData ] = await orm.searchRead(
                "ir.model.fields",
                [["name", "=", fieldName]],
                ["m_translate", "m_channelization"],
                { limit: 1 }
            )
            if(Boolean(fieldData.m_translate) || Boolean(fieldData.m_channelization)){
                if(!companyId){
                    return {};
                }
                const cacheKey = `${companyId}:${model}:${fieldName}`;
                if (cache.has(cacheKey)) {
                    return cache.get(cacheKey);
                }

                var company_data = await orm.call("res.company", "get_langs_and_channels", [companyId])

                if (!company_data){
                    return {};
                }
                const combinations = buildCombinations(
                    company_data.channels || [],
                    company_data.langs || []
                );

                const result = {
                    ...company_data,
                    combinations: combinations,
                    translate: Boolean(fieldData.m_translate),
                    channelisation: Boolean(fieldData.m_channelization),
                    loaded: true,
                };
                cache.set(cacheKey, result);
                return result;
            }
            return {
                translate: Boolean(fieldData.m_translate),
                channelisation: Boolean(fieldData.m_channelization),
                loaded: false,
            }
        }

        return { getChannelLocaleData };
    },
};

registry.category("services").add("channel_locale", ChannelLocaleService);