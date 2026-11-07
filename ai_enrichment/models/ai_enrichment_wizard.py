import requests
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
import json

_logger = logging.getLogger(__name__)

TRIGGER_API_KEY = 'tr_prod_7ePqzXb9sWosq2amdx4D'
TASK_IDENTIFIER = "product-enrichment"
TRIGGER_API_URL = f"https://api.trigger.dev/api/v1/tasks/{TASK_IDENTIFIER}/trigger"


class AIEnrichmentWizard(models.TransientModel):
    _name = 'ai.enrichment.wizard'
    _description = 'AI Enrichment Wizard'

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        index=True
    )

    provider = fields.Selection(
        selection=lambda self: self._get_providers(),
        string="AI Provider",
        required=True
    )

    config_id = fields.Many2one(
        'ai.enrichment.config',
        string="AI Model",
        required=True,
        domain="[('provider', '=', provider)]"
    )

    update_field = fields.Many2many(
        "ai.enrichment.field",
        string="Fields to Update",
        domain="update_field_domain",
    )

    update_field_domain = fields.Char(compute="_compute_update_field_domain")

    product_ids = fields.Many2many('product.product', string="Products")
    product_count = fields.Integer(string="Product Count", compute="_compute_product_count")
    prompt_type_config = fields.Many2one('ai.prompt.type', string="Prompt Type")


    @api.depends('product_ids')
    def _compute_update_field_domain(self):
        for wizard in self:
            company_id = wizard.company_id.id

            families = wizard.product_ids.mapped("product_tmpl_id.family_id")

            # Fetch family attribute IDs that are enrichable
            family_attribute_ids = families.mapped(
                "family_attribute_ids.attribute_id"
            ).filtered(
                lambda a: a.is_ai_enrichable and a.display_type in ['char', 'text']
            ).ids

            # If no product → show GENERAL enrichable attributes only
            if not family_attribute_ids:
                wizard.update_field_domain = json.dumps([
                    '&', '|',
                    ('company_id', '=', company_id),
                    ('company_id', '=', False),
                    ('source_model', '=', 'general.attribute'),
                    ('is_enrichable', '=', True),
                ])
                continue

            domain = [
                '&', '|',
                ('company_id', '=', company_id),
                ('company_id', '=', False),

                ('is_enrichable', '=', True),

                # '|',
                # # General attributes
                # ('source_model', '=', 'general.attribute'),

                '&',
                ('source_model', '=', 'product.attribute'),
                ('source_id', 'in', family_attribute_ids),
            ]

            wizard.update_field_domain = json.dumps(domain)


    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        active_model = self.env.context.get("active_model")
        active_ids = self.env.context.get("active_ids")
        current_company_id = self.env.company.id

        # Load enrichable general attributes
        general_attrs = self.env["general.attribute"].search([
            ("is_ai_enrichable", "=", True),
        ])

        enrichment_fields = []

        for gattr in general_attrs:
            existing = self.env["ai.enrichment.field"].search([
                ("source_model", "=", "general.attribute"),
                ("source_id", "=", gattr.id)
            ], limit=1)

            if existing:
                enrichment_fields.append(existing.id)
            else:
                field_rec = self.env["ai.enrichment.field"].create({
                    "name": gattr.name,
                    "source_model": "general.attribute",
                    "source_id": gattr.id,
                })
                enrichment_fields.append(field_rec.id)

        if active_model in ["product.product", "product.template"] and active_ids:
            if active_model == "product.template":
                products = self.env["product.template"].browse(active_ids).product_variant_ids
            else:
                products = self.env["product.product"].browse(active_ids)

            family_attributes = products.mapped('product_tmpl_id.family_id.family_attribute_ids')

            attribute_ids = family_attributes.mapped('attribute_id').filtered(
                lambda a: a.is_ai_enrichable and (not a.company_id or a.company_id.id == current_company_id)
            )

            for attr in attribute_ids:
                field_rec = self.env["ai.enrichment.field"].search([
                    ("source_model", "=", "product.attribute"),
                    ("source_id", "=", attr.id)
                ], limit=1)

                if not field_rec:
                    field_rec = self.env["ai.enrichment.field"].create({
                        "name": attr.name,
                        "source_model": "product.attribute",
                        "source_id": attr.id,
                    })

                enrichment_fields.append(field_rec.id)

        res["update_field"] = [(6, 0, list(set(enrichment_fields)))]

        latest_prompt_type = self.env["ai.prompt.type"].search([], order="create_date desc", limit=1)
        if latest_prompt_type:
            res["prompt_type_config"] = latest_prompt_type.id

        if active_ids:
            if active_model == "product.product":
                valid_ids = [pid for pid in active_ids if self.env["product.product"].browse(pid).exists()]
                res["product_ids"] = [(6, 0, valid_ids)]
            elif active_model == "product.template":
                templates = self.env["product.template"].browse(active_ids).exists()
                if templates:
                    res["product_ids"] = [(6, 0, templates.product_variant_ids.ids)]

        return res


    @api.model
    def _get_providers(self):
        providers = self.env['ai.enrichment.config'].search([]).mapped('provider')
        selection = dict(self.env['ai.enrichment.config'].fields_get()['provider']['selection'])
        return [(p, selection[p]) for p in set(providers)]

    @api.depends('product_ids')
    def _compute_product_count(self):
        for rec in self:
            rec.product_count = len(rec.product_ids)


    def get_credential_context(self):
        """Prepare context credentials for api"""
        context = {
            "source": "odoo",
            "odoo_url": self.get_base_url(),
            "odoo_db": self.env.cr.dbname,
            "odoo_username": self.env.user.login,
            "odoo_password": "V1a^R@ZracQYpaRu"
        }
        if self.config_id.manual_credentials:
            context = {
                "source": "odoo",
                "odoo_url": self.get_base_url(),
                "odoo_db": self.env.cr.dbname,
                "odoo_username": self.config_id.user_name,
                "odoo_password": self.config_id.password
            }
        return context


    def action_enrich(self):
        if not self.product_ids:
            raise UserError(_("No products selected for enrichment."))

        products_payload = [{
            "id": p.id,
            "name": p.name,
            "sku": p.default_code,
            "list_price": p.list_price,
            "standard_price": p.standard_price,
            "hsn_code": getattr(p, "l10n_in_hsn_code", False),
            "tracking": getattr(p.product_tmpl_id, "tracking", "none"),
            "supplier_taxes": [t.name for t in p.supplier_taxes_id],
            "sales_taxes": [t.name for t in p.taxes_id],
            "sale_ok": p.sale_ok,
            "purchase_ok": p.purchase_ok,
        } for p in self.product_ids]

        event_payload = {
            "name": "product.enrich",
            "payload": {"products": products_payload},
            "context": self.get_credential_context(),
            "ai": {
                "provider": self.config_id.provider,
                "model": self.config_id.code,
                "token": self.config_id.api_token,
                "url": self.config_id.api_url,
                "key": self.config_id.api_key,
            },
            "prompt_type": {"type": self.prompt_type_config.name if self.prompt_type_config else ''},
            "count": {"product": str(len(products_payload))},
            "update_attribute": {
                "fields": [{'field': x.original_name, 'label': x.name} for x in self.update_field]
            },
        }

        try:
            response = requests.post(
                TRIGGER_API_URL,
                headers={"Content-Type": "application/json",
                         "Authorization": f"Bearer {TRIGGER_API_KEY}"},
                json={"payload": event_payload},
                timeout=15
            )
            response.raise_for_status()

            response_json = response.json()
            run_id = response_json.get('id')

            if run_id:
                # Include ALL variant products
                # Include ALL variants for both template or product selections
                all_products = self.env['product.product']

                for p in self.product_ids:
                    if p._name == "product.product":
                        all_products |= p
                    else:
                        all_products |= p.product_variant_ids
                self.env['ai.enrichment.queue.log'].create({
                    'name': run_id,
                    'config_id': self.config_id.id,
                    'product_ids': [(6, 0, all_products.ids)],
                    'prompt_type': self.prompt_type_config.name,
                    'update_field': self.update_field,
                    'event_payload': str(response_json),
                    'state': 'queued',
                })

        except requests.exceptions.RequestException as e:
            raise UserError(_("Failed to send data to enrichment service: %s") % e)

        return {
            'effect': {
                'fadeout': 'fast',
                'message': 'Enrichment process started successfully',
                'type': 'rainbow_man',
            }
        }


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def action_push_to_channel(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('AI Enrichment'),
            'res_model': 'ai.enrichment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'active_ids': self.env.context.get('active_ids', self.ids),
                'active_model': self.env.context.get('active_model', self._name),
            }
        }


class AIEnrichmentField(models.Model):
    _name = "ai.enrichment.field"
    _description = "Unified Enrichment Field"

    name = fields.Char(string="Field Name", required=True)

    source_model = fields.Selection([
        ('product.attribute', 'Product Attribute'),
        ('general.attribute', 'General Attribute'),
        ('family.attribute', 'Family Attribute'),
    ], required=True)

    source_id = fields.Integer(string="Source ID")
    original_name = fields.Char(string="Original Field Name",
                                compute="_compute_original_name", store=True)

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        compute='_compute_company_id',
        store=True,
        index=True
    )

    is_enrichable = fields.Boolean(compute="_compute_is_enrichable")

    @api.depends('source_model', 'source_id')
    def _compute_company_id(self):
        for rec in self:
            rec.company_id = False
            if rec.source_model and rec.source_id:
                source = self.env[rec.source_model].sudo().browse(rec.source_id).exists()
                if source and 'company_id' in source._fields:
                    rec.company_id = source.company_id

    @api.depends('source_model', 'source_id')
    def _compute_is_enrichable(self):
        for rec in self:
            rec.is_enrichable = False
            if rec.source_model == 'product.attribute':
                rec.is_enrichable = bool(self.env['product.attribute'].browse(rec.source_id).is_ai_enrichable)
            elif rec.source_model == 'general.attribute':
                rec.is_enrichable = bool(self.env['general.attribute'].browse(rec.source_id).is_ai_enrichable)

    @api.depends("source_model", "source_id")
    def _compute_original_name(self):
        for rec in self:
            name = rec.name
            try:
                attribute = self.env[rec.source_model].browse(rec.source_id)
                if attribute.exists() and hasattr(attribute, 'original_name'):
                    name = attribute.original_name
            except:
                pass
            rec.original_name = name


