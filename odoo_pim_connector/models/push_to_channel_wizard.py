import json
import logging
import requests
import time
from datetime import datetime, timezone # <-- Import datetime for timestamp checking
from odoo import models, fields, api
from odoo.exceptions import UserError
import base64
import mimetypes

_logger = logging.getLogger(__name__)

class PushToChannelWizard(models.TransientModel):
    _name = 'push.to.channel.wizard'
    _description = 'Push Selected Products to Channel'

    # ... (all fields and compute methods remain the same) ...
    platform_id = fields.Many2one(
        'platform.credentials', string='Choose Channel', required=True,
        domain="[('is_active', '=', True), ('is_coming_soon', '=', False)]"
    )
    mapping_id = fields.Many2one(
        'pim.platform.mapping', string="Field Mapping Used", readonly=True,
        compute='_compute_mapping_id', store=True, compute_sudo=True
    )
    product_ids = fields.Many2many('product.template', string="Products to Push", readonly=True)
    product_variant_ids = fields.Many2many("product.product", string="Products to push", readonly=True)
    product_count = fields.Integer(string="Product Count", compute='_compute_product_count')
    platform_logo = fields.Binary(related='platform_id.logo_image', readonly=True)
    platform_status = fields.Char(related='platform_id.Status', readonly=True)

    @api.depends('product_ids','product_variant_ids')
    def _compute_product_count(self):
        for rec in self:
            rec.product_count = len(rec.product_ids)
            if rec.product_variant_ids:
                rec.product_count = len(rec.product_variant_ids)

    @api.depends('platform_id')
    def _compute_mapping_id(self):
        for rec in self:
            if rec.platform_id:
                mapping = self.env['pim.platform.mapping'].search([('platform_id', '=', rec.platform_id.id)], limit=1)
                rec.mapping_id = mapping
            else:
                rec.mapping_id = False

    def action_push(self):
        self.ensure_one()
        
        # --- Configuration loading remains the same ---
        get_param = self.env['ir.config_parameter'].sudo().get_param
        n8n_api_key = get_param('n8n.api_key') # We still need the key for the log link, but not for polling.

        config = self.env['n8n.workflow.config'].search([
            ('platform', '=', self.platform_id.platform),
            ('is_active', '=', True)
        ], limit=1)

        if not config or not config.n8n_webhook_url:
            raise UserError(f"No active N8N workflow or webhook URL configured for {self.platform_id.platform}.")
        
        webhook_url = config.n8n_webhook_url
        
        mapping_dict = {
            line.external_field_key: line.odoo_field_id.name
            for line in self.mapping_id.mapping_line_ids
        }
        products_list = []
        products = self.product_ids
        if self.product_variant_ids:
            products = self.product_variant_ids
        for product in products:
            product_data = {}
            for external_key, odoo_field_name in mapping_dict.items():
                field_value = getattr(product, odoo_field_name, None)
                if isinstance(field_value, models.BaseModel) and 'name' in field_value:
                    value = field_value.name
                else:
                    value = field_value

                if external_key == 'handle' and isinstance(value, str):
                    value = value.lower()

                if isinstance(value, (bytes, bytearray)):
                    mime_type = "image/jpeg"
                    base64_str = base64.b64encode(value).decode("utf-8")
                    value = f"data:{mime_type};base64,{base64_str}"
                    
                product_data[external_key] = value

            products_list.append(product_data)

        payload = {
            "products": products_list,
            "credential": self.platform_id.get_credential_info()
        }
        _logger.info("Prepared payload for n8n: %s", json.dumps(payload, indent=2, default=str))

        status = 'error'
        response_text = 'An unknown error occurred.'
        n8n_execution_id = None
        
        try:
            headers = {"Content-Type": "application/json"}
            # --- NEW LOGIC: Capture the webhook response directly ---
            response = requests.post(webhook_url, json=payload, headers=headers, timeout=15)
            
            # Check if the webhook call was successful
            response.raise_for_status() # This will raise an HTTPError for bad responses (4xx or 5xx)

            # Parse the JSON response from n8n
            response_data = response.json()
            _logger.info("Received direct response from n8n webhook: %s", response_data)
            
            # Extract the execution ID
            n8n_execution_id = response_data.get('executionId')
            
            if n8n_execution_id:
                status = 'sent' # 'sent' is more accurate than 'processing' at this stage
                response_text = json.dumps(response_data, indent=2)
                _logger.info("SUCCESS: Received new n8n execution ID directly: %s", n8n_execution_id)
            else:
                response_text = "Webhook was triggered successfully, but the n8n response did not contain an 'executionId'. Check the n8n Webhook node configuration."
                _logger.error(response_text)

        except requests.exceptions.RequestException as e:
            response_text = f"Failed to connect to n8n webhook: {str(e)}"
            _logger.exception("Exception during push to n8n: %s", e)
        except json.JSONDecodeError:
            response_text = "Failed to parse JSON response from n8n. Response was: " + response.text
            _logger.error(response_text)
        except Exception as e:
            response_text = f"An unexpected error occurred: {str(e)}"
            _logger.exception("Unexpected exception during push to n8n: %s", e)
            
        # --- Log creation remains the same ---
        new_log = self.env['pim.sync.log'].create({
            'name': '/',
            'platform_id': self.platform_id.id,
            'status': status,
            'product_count': self.product_count,
            'request_payload': json.dumps(payload, indent=2, default=str),
            'response_text': response_text,
            'n8n_execution_id': n8n_execution_id,
            'product_ids': [(6, 0, self.product_ids.ids)],
            'product_variant_ids': [(6, 0, self.product_variant_ids.ids)],

        })

        new_log.write({'name': new_log.sync_id})

        # --- Notification logic remains the same ---
        message = f"Successfully sent {self.product_count} products to {self.platform_id.name} for processing."
        if status == 'error':
            message = f"Failed to send products. Check Configuration > Sync Logs for details."

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Publish to Channel',
                'message': message,
                'type': 'success' if status == 'sent' else 'danger',
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }
