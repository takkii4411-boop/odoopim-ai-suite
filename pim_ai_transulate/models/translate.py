from odoo import models, api, _
from odoo.exceptions import UserError
import requests
import json
import logging

_logger = logging.getLogger(__name__)


class AiEnrichmentConfig(models.Model):
    _inherit = "ai.enrichment.config"

    @api.model
    def perform_ai_translation(self, source_text, target_lang_id):
        # 1. Get Target Language Name
        lang_record = self.env['res.lang'].browse(int(target_lang_id))
        if not lang_record.exists():
            raise UserError(_("Language ID %s not found.") % target_lang_id)

        target_lang_name = lang_record.name

        # 2. Get AI Configuration (Specific search for Groq)
        # We filter by URL containing 'groq' to avoid picking up old Anthropic/Trigger configs
        config = self.search(
            ['&', ('api_url', '!=', False), '|', ('api_url', 'ilike', 'groq'), ('name', 'ilike', 'llama')],
            order='id desc',
            limit=1
        )

        # Fallback if no specific Groq config found, take the newest active one
        if not config:
            config = self.search([('api_url', '!=', False), ('api_key', '!=', False)], order='id desc', limit=1)

        if not config:
            raise UserError(_("No AI Configuration found."))

        # Clean URL/Key
        api_url = config.api_url.strip()
        api_key = config.api_key.strip()
        model_name = config.name.strip() if config.name else "llama-3.3-70b-versatile"

        _logger.info(f"AI DEBUG: Using Config: {model_name} | URL: {api_url}")

        # 3. Construct Payload
        system_prompt = (
            f"Translate the following text into {target_lang_name}. "
            "Return ONLY the translated text. Do not include quotes."
        )

        payload_data = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": source_text}
            ],
            "temperature": 0.1
        }

        # 4. Headers
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        try:
            # 5. Call API
            response = requests.post(api_url, json=payload_data, headers=headers, timeout=30)

            if response.status_code != 200:
                # Log the specific error from Groq
                raise UserError(_("AI Provider Error (%s): %s") % (response.status_code, response.text))

            result_json = response.json()

            # 6. Parse Response
            if 'choices' in result_json and len(result_json['choices']) > 0:
                translated_text = result_json['choices'][0]['message']['content'].strip()
                if translated_text.startswith('"') and translated_text.endswith('"'):
                    translated_text = translated_text[1:-1]
                return translated_text
            else:
                return ""

        except Exception as e:
            _logger.exception("AI Request Failed")
            raise UserError(_("Connection Failed: %s") % str(e))