import requests
import json
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)

class PimSyncLog(models.Model):
    _name = 'pim.sync.log'
    _rec_name = 'sync_id'
    _description = 'PIM Sync Log'
    _order = 'create_date desc'


    # NEW: Add the sequence field
    sync_id = fields.Char(
        string="Sync ID", 
        required=True, 
        copy=False, 
        readonly=True, 
        index=True, 
        default=lambda self: _('New')
    )

    name = fields.Char(string="Operation", required=True, readonly=True)
    platform_id = fields.Many2one('platform.credentials', string="Connector", readonly=True)
    status = fields.Selection([
        ('queued', 'Queued'), ('sent', 'Sent to Channel'), ('processing', 'Processing'),
        ('success', 'Success'), ('partial', 'Partial Success'), ('error', 'Error'),
    ], string="Status", default='queued', readonly=True)
    request_payload = fields.Text(string="Request Payload (Raw)", readonly=True)
    response_text = fields.Text(string="n8n Response (Raw)", readonly=True)
    product_count = fields.Integer(string="Product Count", readonly=True)
    n8n_execution_id = fields.Char(string="Channel Execution ID", readonly=True)
    product_ids = fields.Many2many('product.template', string="Synced Products", readonly=True)
    product_variant_ids = fields.Many2many("product.product", stroing="Synced Products", readonly=True)
    summary_message = fields.Text(string="Summary", readonly=True)
    successful_items = fields.Integer(string="Successful Items", readonly=True)
    failed_items = fields.Integer(string="Failed Items", readonly=True)
    error_details_html = fields.Html(string="Error Details", readonly=True)

    color = fields.Integer(string='Color Index', compute='_compute_color')



    # NEW: Override the create method to generate the sequence
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('sync_id', _('New')) == _('New'):
                vals['sync_id'] = self.env['ir.sequence'].next_by_code('pim.sync.log.sequence') or _('New')
        return super().create(vals_list)


    @api.depends('status')
    def _compute_color(self):
        for log in self:
            if log.status in ['error', 'partial']:
                log.color = 1  # Red
            elif log.status == 'success':
                log.color = 10 # Green
            else:
                log.color = 4  # Yellow/Orange

    def _parse_n8n_execution_data(self):
        """
        Intelligently parses the n8n JSON to get success/fail counts and error messages.
        This version is robust and does not depend on a fixed workflow structure.
        It identifies failed items by looking for an n8n node with 'error' or 'fail' in its name.
        """
        self.ensure_one()
        
        response_text_to_parse = self.env.context.get('temp_response_text') or self.response_text
        if not response_text_to_parse:
            return {}

        try:
            data = json.loads(response_text_to_parse)
            run_data = data.get('data', {}).get('resultData', {}).get('runData', {})
            
            # --- ROBUST PARSING LOGIC ---

            # 1. Collect all items that passed through any node designated for errors.
            failed_items_details = []
            error_node_keywords = ['error', 'fail', 'failed'] # Keywords to identify an error-handling node

            for node_name, executions in run_data.items():
                # Check if the node name suggests it handles errors
                if any(keyword in node_name.lower() for keyword in error_node_keywords):
                    for execution in executions:
                        if execution.get('data', {}).get('main'):
                            for item in execution['data']['main'][0]:
                                if 'json' in item:
                                    failed_items_details.append(item['json'])

            # 2. Build the detailed error messages list from the collected failed items.
            errors = []
            if failed_items_details:
                possible_id_keys = ['sku', 'productNumber', 'id']  # Prioritized list of possible unique identifiers
                id_key = None

                # Determine the identifier key from the first failed item
                first_item = failed_items_details[0]
                for key in possible_id_keys:
                    if key in first_item:
                        id_key = key
                        break
                
                if not id_key:
                    _logger.warning("Could not determine a product identifier (e.g., sku, id) in the error node for log %s.", self.id)
                    errors.append("<li><b>Parsing Error:</b> Could not identify products in the workflow's error output.</li>")
                
                else:
                    for item_json in failed_items_details:
                        item_id = item_json.get(id_key, 'N/A')
                        item_name = item_json.get('name', 'Unknown Product')
                        
                        # Extract the error message
                        error_message = "Unknown error"
                        if 'error' in item_json:
                            error_obj = item_json['error']
                            if isinstance(error_obj, dict):
                                # Look for common keys where n8n or APIs store error text
                                error_message = error_obj.get('message', error_obj.get('description', 'No error message provided.'))
                            elif isinstance(error_obj, str):
                                error_message = error_obj
                        
                        # Clean up escaped characters for better readability
                        error_message = error_message.replace('\\"', '"').replace('\\\\', '\\')
                        errors.append(f"<li><b>Product:</b> {item_name} ({id_key.capitalize()}: {item_id})<br/><b>Reason:</b> {error_message}</li>")

            # 3. Calculate final counts. The total is what we sent, failures are what we found in error nodes.
            total_count = self.product_count
            fail_count = len(failed_items_details)
            success_count = max(0, total_count - fail_count) # Ensure it's not negative

            # 4. Check for top-level workflow errors (e.g., authentication failure before processing items).
            if data.get('status') != 'success' and data.get('error'):
                error_obj = data['error']
                error_message = error_obj.get('description', 'Unknown n8n workflow error.')
                if not any(error_message in e for e in errors):
                    errors.insert(0, f"<li><b>Critical Workflow Error:</b> {error_message}</li>")
                
                # If the whole workflow failed at the top level, all items are considered failed.
                fail_count = total_count
                success_count = 0

            return {
                'success_count': success_count,
                'fail_count': fail_count,
                'errors': errors
            }
        except (json.JSONDecodeError, TypeError, KeyError, IndexError, ValueError) as e:
            _logger.error(f"Critical error parsing n8n execution data for log %s: {str(e)}", self.id, exc_info=True)
            return {'errors': [f"Could not parse the n8n JSON response. It may be malformed or an unexpected structure was returned. Error: {str(e)}"]}
            
    @api.depends('response_text', 'status')
    def _compute_summary_fields(self):
        """Uses the parser to populate the clean UI fields."""
        for log in self:
            if log.status in ('queued', 'sent', 'processing'):
                log.summary_message = "Workflow is in progress. Click 'Check Status from channel' to get the latest result."
                log.successful_items = 0
                log.failed_items = 0
                log.error_details_html = False
                continue

            parsed_data = log._parse_n8n_execution_data()
            
            log.successful_items = parsed_data.get('success_count', 0)
            log.failed_items = parsed_data.get('fail_count', 0)
            errors = parsed_data.get('errors', [])
            
            if log.status == 'success':
                log.summary_message = f"Workflow completed successfully. All {log.successful_items} of {log.product_count} items were processed."
            elif log.status == 'partial':
                log.summary_message = "Workflow completed with some errors."
            elif log.status == 'error':
                log.summary_message = "Workflow failed to complete."
                
            if errors:
                error_list_html = "".join([f"<li>{e}</li>" for e in errors])
                log.error_details_html = f"<ul>{error_list_html}</ul>"
            else:
                log.error_details_html = False

    def action_check_n8n_status(self):
        """
        Pulls the execution log from n8n, intelligently parses it, and sets the
        final status and summary fields accurately.
        """
        get_param = self.env['ir.config_parameter'].sudo().get_param
        n8n_api_url = get_param('n8n.api_url')
        n8n_api_key = get_param('n8n.api_key')
        
        if not all([n8n_api_url, n8n_api_key]):
            raise UserError("n8n API URL or API Key is not configured in System Parameters.")

        for log in self:
            if not log.n8n_execution_id:
                continue

            api_url = f"{n8n_api_url.rstrip('/')}/api/v1/executions/{log.n8n_execution_id}?includeData=true"
            headers = {"X-N8N-API-KEY": n8n_api_key}

            try:
                response = requests.get(api_url, headers=headers, timeout=30)
                if response.status_code != 200:
                    log.write({
                        'status': 'error',
                        'response_text': f"Failed to fetch status from n8n. HTTP {response.status_code}: {response.text}",
                        'summary_message': "Could not connect to the n8n API to get the status."
                    })
                    continue

                execution_data = response.json()
                is_finished = execution_data.get('finished', False) or execution_data.get('stoppedAt')
                
                # Use context to pass the response text to the parser
                parsed_data = log.with_context(temp_response_text=json.dumps(execution_data))._parse_n8n_execution_data()
                
                success_count = parsed_data.get('success_count', 0)
                fail_count = parsed_data.get('fail_count', 0)
                errors = parsed_data.get('errors', [])
                
                vals_to_write = {
                    'response_text': json.dumps(execution_data, indent=2),
                    'successful_items': success_count,
                    'failed_items': fail_count,
                }
                
                if errors:
                    vals_to_write['error_details_html'] = f"<ul>{''.join(errors)}</ul>"
                
                if is_finished:
                    if fail_count > 0 and success_count > 0:
                        vals_to_write['status'] = 'partial'
                        vals_to_write['summary_message'] = f"Workflow completed with errors. {success_count} succeeded, {fail_count} failed."
                    elif fail_count > 0 and success_count == 0:
                        vals_to_write['status'] = 'error'
                        vals_to_write['summary_message'] = f"Workflow failed completely. All {fail_count} items failed."
                    else:
                        vals_to_write['status'] = 'success'
                        vals_to_write['summary_message'] = f"Workflow completed successfully. All {success_count} items were processed."
                else:
                    vals_to_write['status'] = 'processing'
                    vals_to_write['summary_message'] = "Workflow is in progress."

                log.write(vals_to_write)

            except Exception as e:
                _logger.exception("Error checking n8n status for log %s", log.id)
                log.write({'status': 'error', 'response_text': str(e)})

        return {
            'type': 'ir.actions.client', 'tag': 'display_notification',
            'params': {
                'title': 'Status Check Complete', 'message': 'Sync log status has been updated from n8n.',
                'type': 'success', 'next': {'type': 'ir.actions.act_window_close'},
            }
        }
