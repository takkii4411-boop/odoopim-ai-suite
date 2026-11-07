import requests
import json
import logging
from odoo import api, fields, models, _
import pytz

_logger = logging.getLogger(__name__)

# --- CHANGE: Hardcoded API Key ---
# Note: Storing keys in code is not recommended for production environments.
# Consider using Odoo's System Parameters for better security and flexibility.
TRIGGER_API_KEY = 'tr_prod_7ePqzXb9sWosq2amdx4D'


class AIEnrichmentQueueLog(models.Model):
    _name = 'ai.enrichment.queue.log'
    _description = 'AI Enrichment Queue Log'
    _order = 'create_date desc'

    name = fields.Char(string="Run ID", required=True, readonly=True, index=True)
    reference = fields.Char(string="Reference", readonly=True)

    state = fields.Selection([
        ('queued', 'Queued'),
        ('processing', 'Processing'),
        ('done', 'Done'),
        ('failed', 'Failed'),
    ], string="Sync Status", default='queued', readonly=True, copy=False)

    config_id = fields.Many2one('ai.enrichment.config', string="AI Configuration", readonly=True)
    product_ids = fields.Many2many('product.product', string="Products")
    event_payload = fields.Char()
    # compute='_compute_product_ids', readonly=True)

    # product_templates = fields.Many2many(
    #     'product.template',
    #     string="Product Templates",
    #     # compute='_compute_product_templates',
    #     # store=False,
    # )
    #
    # def _compute_product_ids(self):
    #     for record in self:
    #         if hasattr(record, 'sku') and record.sku:
    #             products = self.env['product.template'].search([('default_code', '=', record.sku)])
    #             record.product_ids = products
    #         else:
    #             record.product_ids = False

    # product_tmpl_ids = fields.Many2many(
    #     'product.template',
    #     string="Product Templates",
    #     # compute="_compute_product_tmpl_ids",
    #     store=False,
    # )
    product_count = fields.Integer(string="Total Products", compute="_compute_product_count", store=True)

    type = fields.Char(string="Type", default="Product Ai Enrichment", readonly=True)

    prompt_type = fields.Char(string="Prompt Type", readonly=True)
    # update_field = fields.Char(string="Updated Field", readonly=True)

    update_field = fields.Char(string="Updated Field", readonly=True)
    update_field_label = fields.Char(string="Updated Field", compute="_compute_update_field_label", store=False)

    product_templates = fields.Many2many(
        'product.template',
        string="Product Templates",
        compute='_compute_products',
        store=False,
    )

    product_variants = fields.Many2many(
        'product.product',
        string="Product Variants",
        compute='_compute_products',
        store=False,
    )

    def _compute_products(self):
        for record in self:
            variants = record.product_ids
            # templates = variants.mapped('product_tmpl_id')
            templates = self.env['product.template']
            if record.product_ids:
                templates = record.product_ids.mapped('product_tmpl_id')
            record.product_templates = templates

            # Set variants only if product has variants
            record.product_variants = variants.filtered(lambda v: v.product_tmpl_id.has_variant)

    @api.model
    def get_sync_count(self):
        """Return count of unique references"""
        references = self.search_read([], ['reference'])
        unique_references = set(ref['reference'] for ref in references if ref['reference'])
        return len(unique_references)

    # @api.model
    # def get_update_success_count(self):
    #     """Return total Odoo update success count across all logs"""
    #     try:
    #         logs = self.env['ai.enrichment.queue.log'].search([])
    #         success_total = sum(log.update_success_count for log in logs)
    #         return success_total
    #     except Exception as e:
    #         return 0

    @api.depends('update_field')
    def _compute_update_field_label(self):
        for log in self:
            label = ''
            if log.update_field and isinstance(log.update_field, str):
                print("Processing update_field:", log.update_field)

                # Case 1: Normal product field (This part is fine)
                field_obj = self.env['product.product']._fields.get(log.update_field)
                if field_obj:
                    label = field_obj.string

                # Case 2: ai.enrichment.field with IDs inside
                # --- FIX 1: Changed startswith check from "product.attribute(" ---
                elif log.update_field.startswith("ai.enrichment.field("):
                    print("Processing as ai.enrichment.field with IDs")
                    try:
                        # Extract the string of IDs: "18, 23, 24, 1647, 1654"
                        ids_str = log.update_field.split("(", 1)[1].split(")", 1)[0]
                        # Convert to a list of integers
                        ids = [int(x.strip()) for x in ids_str.split(",") if x.strip().isdigit()]
                        if ids:
                            print("Found field IDs:", ids)
                            # --- FIX 2: Changed model from 'product.attribute' to 'ai.enrichment.field' ---
                            records = self.env['ai.enrichment.field'].browse(ids)
                            # Assuming the 'ai.enrichment.field' model has a 'name' field for the label
                            names = records.mapped('name')
                            label = ", ".join(names)
                    except (ValueError, IndexError):
                        # In case of a malformed string, just use the original value
                        label = log.update_field

                else:
                    label = log.update_field

            elif log.update_field:
                label = str(log.update_field)

            log.update_field_label = label

    generation_success_count = fields.Integer(string="Generation Success", readonly=True)
    generation_failed_count = fields.Integer(string="Generation Failed", readonly=True)
    update_success_count = fields.Integer(string="Odoo Update Success", readonly=True)
    update_failed_count = fields.Integer(string="Odoo Update Failed", readonly=True)
    results_json = fields.Text(string="Detailed Results (JSON)", readonly=True)
    error_message = fields.Text(string="Error Message", readonly=True)

    create_date_formatted = fields.Char(
        string="Queued",
        compute='_compute_create_date_formatted',
        store=True  # Storing is good for performance if the view will be loaded often
    )

    @api.depends('create_date')
    def _compute_create_date_formatted(self):
        for log in self:
            if log.create_date:
                user_local_time = fields.Datetime.context_timestamp(log, log.create_date)

                # 2. Now, format the NEW timezone-aware datetime object.
                log.create_date_formatted = "{} - {} - {} | {}".format(
                    user_local_time.strftime('%d'),
                    user_local_time.strftime('%b').upper(),
                    user_local_time.strftime('%Y'),
                    user_local_time.strftime('%I:%M %p')
                )
            else:
                log.create_date_formatted = ''

    @api.depends('product_ids')
    def _compute_product_count(self):
        for log in self:
            log.product_count = len(log.product_ids)

    @api.model
    def get_update_trends(self, days=10):
        """Return last N days of product counts grouped by create_date."""
        days = int(days) if days else 10

        self._cr.execute("""
            SELECT
                DATE(create_date) AS log_date,
                SUM(product_count) AS total_products
            FROM ai_enrichment_queue_log
            WHERE create_date >= NOW() - interval '%s days'
            GROUP BY DATE(create_date)
            ORDER BY log_date ASC
        """, (days,))

        rows = self._cr.dictfetchall()

        results = []
        for row in rows:
            results.append({
                "date": row["log_date"].strftime("%Y-%m-%d"),
                "count": row["total_products"] or 0,
            })
        return results

    # --- CHANGE: Removed _get_trigger_api_key method ---
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('reference'):
                vals['reference'] = self.env['ir.sequence'].next_by_code('sync.queue.code')
        return super().create(vals_list)

    def write(self, vals):
        return super().write(vals)

    @api.model
    def get_sync_data_for_chart(self, limit=20):
        """ Fetches the latest sync data for the line chart """
        # Group by 'reference' to get unique sync runs
        # For each reference, get the latest log entry (assuming it has the final counts)
        self._cr.execute("""
            SELECT DISTINCT ON (reference)
                id,  
                reference as sync_id,
                update_success_count as success_count,
                update_failed_count as failed_count,
                create_date
            FROM ai_enrichment_queue_log
            WHERE reference IS NOT NULL
            ORDER BY reference, create_date DESC
            LIMIT %s
        """, (limit,))

        results = self._cr.dictfetchall()
        return results

    def action_refresh_status(self):
        """Button action to manually refresh the status from Trigger.dev."""
        if not TRIGGER_API_KEY:
            _logger.warning("Trigger.dev API Key is not set in the model file.")
            return

        for log in self:
            if log.state not in ['queued', 'processing']:
                continue

            run_id = log.name
            url = f"https://api.trigger.dev/api/v3/runs/{run_id}"
            headers = {"Authorization": f"Bearer {TRIGGER_API_KEY}"}

            vals_to_write = {}
            try:
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                data = response.json()
                print("Data from trigger retrive api", data)

                trigger_status = data.get('status')
                if trigger_status in ('QUEUED', 'EXECUTING', 'PENDING'):
                    vals_to_write['state'] = 'processing'
                elif trigger_status == 'COMPLETED':
                    if data.get('isSuccess'):
                        vals_to_write['state'] = 'done'
                        output = data.get('output')
                        if output:
                            if isinstance(output, str):
                                output = json.loads(output)
                            log.event_payload = str(output)
                            # ooo = {
                            #     'results': [
                            #         {
                            #             'id': 1651,
                            #             'sku': 'MT024109',
                            #             'name': 'Imperial Red Paracord 550 Type III',
                            #             'generationStatus': 'success',
                            #             'updateStatus': 'success',
                            #             'updatePayload': {'x_att1425_paracord_demo': 'Outdoor Rope',
                            #                               'x_att1375_paracord_demo': 'Solid'}
                            #         },
                            #         {
                            #             'id': 1652,
                            #             'sku': 'MT024868',
                            #             'name': 'Black Paracord Type II - 50 m Spool',
                            #             'generationStatus': 'success',
                            #             'updateStatus': 'success',
                            #             'updatePayload': {
                            #                 'x_att1425_paracord_demo': 'Black Paracord Type II - 50m Spool',
                            #                 'x_att1375_paracord_demo': 'Solid'}
                            #         }
                            #     ]
                            # }

                            results = output.get('results', [])
                            error_lines = []

                            for res in results:
                                gen_status = res.get('generationStatus')
                                upd_status = res.get('updateStatus')
                                if gen_status == 'failed' or upd_status in ('failed', 'skipped'):
                                    sku = res.get('sku') or res.get('id')
                                    err = res.get('error') or 'Unknown error'
                                    error_lines.append(f"{sku}: {err}")

                            generation_success = sum(1 for r in results if r.get('generationStatus') == 'success')
                            generation_failed = sum(1 for r in results if r.get('generationStatus') != 'success')
                            update_success = sum(1 for r in results if r.get('updateStatus') == 'success')
                            update_failed = sum(1 for r in results if r.get('updateStatus') != 'success')

                            # vals_to_write.update({
                            #     'generation_success_count': output.get('generationSuccess', 0),
                            #     'generation_failed_count': output.get('generationFailed', 0),
                            #     'update_success_count': output.get('updateSuccess', 0),
                            #     'update_failed_count': output.get('updateFailedOrSkipped', 0),
                            #     'error_message': "\n".join(error_lines),
                            #     'results_json': json.dumps(results, indent=2),
                            # })
                            vals_to_write.update({
                                'generation_success_count': generation_success,
                                'generation_failed_count': generation_failed,
                                'update_success_count': update_success,
                                'update_failed_count': update_failed,
                                'error_message': "\n".join(
                                    f"{r.get('sku')}: {r.get('error', 'Unknown error')}"
                                    for r in results
                                    if r.get('generationStatus') == 'failed' or r.get('updateStatus') in ('failed',
                                                                                                          'skipped')
                                ),
                                'results_json': json.dumps(results, indent=2),
                            })
                            if results:
                                # Create lookup map {product_id: updatePayload}
                                update_map = {
                                    int(val['id']): val.get('updatePayload', {})
                                    for val in results
                                    if val.get('id')
                                }

                                for product in log.product_ids:
                                    payload = update_map.get(product.id)
                                    if payload:
                                        # Validate payload fields
                                        valid_payload = {k: v for k, v in payload.items() if k in product._fields}
                                        if valid_payload:
                                            product.write(valid_payload)

                            # vals_to_write.update({
                            #     'generation_success_count': output.get('generationSuccess', 0),
                            #     'generation_failed_count': output.get('generationFailed', 0),
                            #     'update_success_count': output.get('updateSuccess', 0),
                            #     'update_failed_count': output.get('updateFailedOrSkipped', 0),
                            #     'error_message': output.get()
                                # 'error_message': "\n".join(
                                #     f"{res.get('error')}"
                                #     for res in output.get('results', [])
                                #     if res.get('generationStatus') == 'failed' or res.get('updateStatus') in ('skipped',
                                #                                                                               'failed')),
                                #
                                # 'results_json': json.dumps(output.get('results', []), indent=2),
                            # })
                    elif data.get('isFailed'):
                        vals_to_write['state'] = 'failed'
                        error = data.get('error', {})
                        vals_to_write['error_message'] = error.get('message', 'Unknown failure.')
                elif trigger_status == 'CANCELLED':
                    vals_to_write['state'] = 'failed'
                    vals_to_write['error_message'] = 'Run was cancelled.'

                # 🔥 Important: actually write changes to DB
                if vals_to_write:
                    log.write(vals_to_write)

            except requests.exceptions.RequestException as e:
                _logger.error(f"Failed to connect to Trigger.dev for run {run_id}: {e}")
            except Exception as e:
                _logger.error(f"An unexpected error occurred while processing run {run_id}: {e}")
                log.write({'state': 'failed', 'error_message': str(e)})

        """Button action to manually refresh the status from Trigger.dev."""
        # --- CHANGE: Use the static API key ---
        if not TRIGGER_API_KEY:
            _logger.warning("Trigger.dev API Key is not set in the model file.")
            return

        for log in self:
            if log.state not in ['queued', 'processing']:
                continue

            run_id = log.name
            url = f"https://api.trigger.dev/api/v3/runs/{run_id}"
            headers = {"Authorization": f"Bearer {TRIGGER_API_KEY}"}

            vals_to_write = {}
            try:
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                data = response.json()
                print("Data from trigger retrive api", data)

                trigger_status = data.get('status')
                if trigger_status in ('QUEUED', 'EXECUTING', 'PENDING'):
                    vals_to_write['state'] = 'processing'
                elif trigger_status == 'COMPLETED':
                    if data.get('isSuccess'):
                        vals_to_write['state'] = 'done'
                        output = data.get('output')
                        if output:
                            if isinstance(output, str):
                                output = json.loads(output)
                            vals_to_write.update({
                                'generation_success_count': output.get('generationSuccess', 0),
                                'generation_failed_count': output.get('generationFailed', 0),
                                'update_success_count': output.get('updateSuccess', 0),
                                'update_failed_count': output.get('updateFailedOrSkipped', 0),
                                'results_json': json.dumps(output.get('results', []), indent=2),
                            })
                    elif data.get('isFailed'):
                        vals_to_write['state'] = 'failed'
                        error = data.get('error', {})
                        vals_to_write['error_message'] = error.get('message', 'Unknown failure.')
                elif trigger_status == 'CANCELLED':
                    vals_to_write['state'] = 'failed'
                    vals_to_write['error_message'] = 'Run was cancelled.'


            except requests.exceptions.RequestException as e:
                _logger.error(f"Failed to connect to Trigger.dev for run {run_id}: {e}")
            except Exception as e:
                _logger.error(f"An unexpected error occurred while processing run {run_id}: {e}")
                log.write({'state': 'failed', 'error_message': str(e)})

    @api.model
    def _cron_check_pending_runs(self):
        """Cron job to check all queued or processing runs."""
        _logger.info("Running cron job to check pending AI enrichment runs...")
        pending_logs = self.search([('state', 'in', ['queued', 'processing'])])
        pending_logs.action_refresh_status()
        _logger.info(f"Cron job finished. Checked {len(pending_logs)} runs.")


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def action_redirect_to_product(self):
        # Redirects to the product variant form view
        return {
            "type": "ir.actions.act_window",
            "name": "Product",
            "res_model": "product.template",
            "view_mode": "form",
            "target": "current",
            # "res_id": self.product_variant_id.id if self.product_variant_id else False,
            "res_id": self.id,  # open current product.template record
            "views": [(self.env.ref("pim_ext.view_product_creation_split_view_custom").id, "form")],
        }

class ProductProduct(models.Model):
    _inherit = "product.product"

    def action_redirect_to_product_variant(self):
        # Redirects to the product variant form view
        return {
                "type": "ir.actions.act_window",
                "name": "Product",
                "res_model": "product.product",
                "view_mode": "form",
                "target": "current",
                "res_id": self.id,  # open current product.template record
                "views": [(self.env.ref("pim_ext.view_product_product_creation_split_view_custom").id, "form")],
            }
