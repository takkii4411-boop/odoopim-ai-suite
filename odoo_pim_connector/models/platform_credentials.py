import base64
import os
import requests
from odoo import models, fields, api
from odoo.tools.misc import file_path
from odoo.exceptions import ValidationError

class PlatformCredentials(models.Model):
    _name = "platform.credentials"
    _description = "Platform Credentials"

    name = fields.Char(required=True, readonly=True)
    platform = fields.Selection(
        [
            ("shopware", "Shopware"),   
            ("magento", "Magento 2"),
            ("sellercloud", "Sellercloud"),
            ("shopify", "Shopify"),
            ("amazon", "Amazon"),
            ("flipkart", "Flipkart"),
            ("ebay", "eBay"),
            ("walmart", "Walmart"),
            ("b2b", "Business to Business"),
        ],
        required=True,
        readonly=True,
    )

    category = fields.Selection([
        ("ecommerce", "E-commerce Channels"),
        ("marketplace", "Marketplace Channels"),
        ("marketing", "Marketing Channels"),
        ("others", "Other Channels"),
    ], string="Channel Category", required=True, default="ecommerce", readonly=True)
    is_active = fields.Boolean(string="Active", readonly=True, copy=False, default=False)
    is_coming_soon = fields.Boolean(string="Coming Soon", default=False)
    Status = fields.Char(string="Connection Status", readonly=True, copy=False, default="Not tested")

    last_sync_date = fields.Datetime(string="Last Sync", compute="_compute_last_sync_date", readonly=True)
    error_log_count = fields.Integer(string="Error Logs", compute="_compute_last_sync_date", readonly=True)

    # --- NEW FIELDS FOR KANBAN DASHBOARD ---
    active_connectors_kpi = fields.Integer(compute="_compute_dashboard_kpis")
    queued_logs_kpi = fields.Integer(compute="_compute_dashboard_kpis")
    error_logs_kpi = fields.Integer(compute="_compute_dashboard_kpis")
    pushed_today_kpi = fields.Integer(compute="_compute_dashboard_kpis")
    graph_view_id = fields.Many2one('ir.ui.view', compute="_compute_dashboard_kpis")

    # Platform-specific fields
    shopware_base_url = fields.Char("Shopware URL")
    shopware_username = fields.Char("Shopware Username")
    shopware_password = fields.Char("Shopware Password")
    magento_base_url = fields.Char("Magento URL")
    # magento_access_token = fields.Char("Magento Access Token")
    magento_admin_username = fields.Char("Magento Admin Username")
    magento_admin_password = fields.Char("Magento Admin Password")
    # Shopify fields
    shopify_shop_subdomain = fields.Char("Shopify Shop Subdomain")
    shopify_client_id = fields.Char("Shopify Client ID")
    shopify_client_secret = fields.Char("Shopify Client Secret")
    shopify_access_token = fields.Char("Shopify Access Token")

    # b2b fields
    b2b_shop_subdomain = fields.Char("B2B Shop Subdomain")
    b2b_client_id = fields.Char("B2B Client ID")
    b2b_client_secret = fields.Char("B2B Client Secret")
    b2b_access_token = fields.Char("B2B Access Token")

    logo_image = fields.Binary(string="Platform Logo", compute='_compute_logo_image')
    mapping_count = fields.Integer(compute='_compute_mapping_count')

    n8n_workflow_id = fields.Char("n8n Workflow ID")
    n8n_webhook_url = fields.Char("n8n Webhook URL")

    @api.onchange('shopware_base_url', 'shopware_username', 'shopware_password', 'magento_admin_username', 'magento_admin_password', 'magento_base_url','shopify_shop_subdomain','shopify_client_id','shopify_client_secret','shopify_access_token')
    def _on_credentials_change(self):
        """When user edits credentials, reset status and deactivate."""
        if self.is_active or self.Status != 'Not tested':
            self.Status = 'Not tested'
            self.is_active = False

    def get_credential_info(self):
        """Prepares a dictionary of credentials to be sent to the external service."""
        self.ensure_one()
        
        info = {
            "platform": self.platform,
            "channel_name": self.name,
            "status": self.Status,
        }

        if self.platform == 'shopware':
            info.update({
                "base_url": self.shopware_base_url,
                "username": self.shopware_username,
                "password": self.shopware_password,
                # Add other non-sensitive shopware fields if needed
            })
        elif self.platform == 'magento':
            info.update({
                "base_url": self.magento_base_url,
                "username": self.magento_admin_username,
                "password": self.magento_admin_password,
            })
        elif self.platform == 'shopify':
            info.update({
                "shop_subdomain": self.shopify_shop_subdomain,
                "client_id": self.shopify_client_id,
                "client_secret": self.shopify_client_secret,
                "access_token": self.shopify_access_token,
            })
        # Add elif blocks for other platforms (akeneo, shopify) here
        return info

    @api.depends('platform')
    def _compute_logo_image(self):
        for rec in self:
            if rec.platform:
                try:
                    img_path = file_path(f'odoo_pim_connector/static/src/img/{rec.platform}.png')
                    with open(img_path, 'rb') as f:
                        rec.logo_image = base64.b64encode(f.read())
                except (IOError, FileNotFoundError):
                    rec.logo_image = False
            else:
                rec.logo_image = False

    def _compute_mapping_count(self):
        for rec in self:
            rec.mapping_count = self.env['pim.platform.mapping'].search_count([('platform_id', '=', rec.id)])

    def get_formview_action(self, access_uid=None):
        self.ensure_one()
        if self.is_coming_soon:
            return {
                'type': 'ir.actions.act_window', 'name': 'Coming Soon',
                'res_model': 'coming.soon.wizard', 'view_mode': 'form',
                'target': 'new',
            }
        return super().get_formview_action(access_uid=access_uid)

    def action_deactivate(self):
        self.write({
            'is_active': False,
            'Status': 'Deactivated by user. Please re-test credentials.'
        })

    def test_connection(self):
        self.ensure_one()
        status_message = "Not tested"
        is_active = False

        if self.platform == 'shopware':
            if not all([self.shopware_base_url, self.shopware_username, self.shopware_password]):
                raise ValidationError("Please fill in all Shopware credentials.")
            
            url = f"{self.shopware_base_url.rstrip('/')}/api/oauth/token"
            payload = {
                "grant_type": "password",
                "client_id": "administration",
                "scopes": "write",
                "username": self.shopware_username,
                "password": self.shopware_password,
            }
            headers = {"Content-Type": "application/json"}

            try:
                response = requests.post(url, json=payload, headers=headers, timeout=10)
                if response.status_code == 200:
                    status_message = "Shopware Connection Successful!"
                    is_active = True
                else:
                    try:
                        error_details = response.json().get('errors', [{}])[0].get('detail', "No details provided.")
                    except Exception:
                        error_details = response.text if response.text else "No details provided."
                    status_message = f"Shopware Failed: {response.status_code} - {error_details}"
            except requests.exceptions.RequestException as e:
                status_message = f"Shopware Connection Error: {e}"

        elif self.platform == 'magento':
            if not all([self.magento_base_url, self.magento_admin_username, self.magento_admin_password]):
                raise ValidationError("Please fill in all Magento credentials.")
            
            url = f"{self.magento_base_url.rstrip('/')}/rest/V1/integration/admin/token"
            payload = {
                "username": self.magento_admin_username,
                "password": self.magento_admin_password,
            }
            headers = {"Content-Type": "application/json"}

            try:
                response = requests.post(url, json=payload, headers=headers, timeout=10)
                if response.status_code == 200:
                    token = response.json()  # Magento returns token as string
                    if isinstance(token, str) and len(token) > 10:
                        status_message = "Magento Connection Successful!"
                        is_active = True
                    else:
                        status_message = "Magento response invalid."
                else:
                    try:
                        error_details = response.json().get('message', "No details provided.")
                    except Exception:
                        error_details = response.text if response.text else "No details provided."
                    status_message = f"Magento Failed: {response.status_code} - {error_details}"
            except requests.exceptions.RequestException as e:
                status_message = f"Magento Connection Error: {e}"
        
        elif self.platform == 'shopify':
            if not all([self.shopify_shop_subdomain, self.shopify_client_id, self.shopify_client_secret]):
                raise ValidationError("Please fill in all Shopify credentials.")

            print("Testing Shopify OAuth connection...")
            shop_url = f"https://{self.shopify_shop_subdomain}.myshopify.com/admin/api/2023-01/shop.json"

            try:
                response = requests.get(
                    shop_url,
                    headers={"X-Shopify-Access-Token": self.shopify_access_token },
                    timeout=10
                )
                print("Shopify response status:", response.status_code)
                print("Shopify response text:", response.text)
                if response.status_code == 200:
                    status_message = "Shopify Connection Successful!"
                    is_active = True
                elif response.status_code == 401:
                    status_message = "Unauthorized – check Access Token / Subdomain."
                else:
                    status_message = f"Shopify API error {response.status_code}: {response.text}"
            except requests.exceptions.RequestException as e:
                status_message = f"Shopify Connection Error: {e}"

        elif self.platform == 'b2b':
            # TODO add fucntion for b2b platforms now testing purpose only
            is_active = True
            status_message = "Business to Business Connection Success"
        # TODO: Add other platforms (shopify, sellercloud, etc.) later...

        self.write({'Status': status_message, 'is_active': is_active})
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Connection Test Result',
                'message': status_message,
                'sticky': False,
                'type': 'success' if is_active else 'danger',
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }


    def action_open_mappings(self):
        """
        This is the action for the 'Field Mappings' smart button.
        It finds or creates the mapping config for this platform and opens its form view.
        """
        self.ensure_one()
        # Search for an existing mapping configuration for this connector
        mapping = self.env['pim.platform.mapping'].search([('platform_id', '=', self.id)], limit=1)
        
        # If no mapping exists, create one. The create() method will auto-populate the lines.
        if not mapping:
            mapping = self.env['pim.platform.mapping'].create({'platform_id': self.id})
        
        return {
            'type': 'ir.actions.act_window',
            'name': f"{self.name} Field Mappings",
            'res_model': 'pim.platform.mapping',
            'view_mode': 'form',
            'res_id': mapping.id,
            'target': 'current',
            'context': dict(self.env.context, platform=self.platform),
        }

    def _compute_last_sync_date(self):
        logs = self.env['pim.sync.log'].search_read(
            [('platform_id', 'in', self.ids)],
            ['platform_id', 'create_date', 'status']
        )
        # Group logs by platform_id
        logs_by_platform = {
            p_id: [l for l in logs if l['platform_id'][0] == p_id]
            for p_id in self.ids
        }
        for rec in self:
            platform_logs = logs_by_platform.get(rec.id, [])
            rec.last_sync_date = max(l['create_date'] for l in platform_logs) if platform_logs else False
            rec.error_log_count = sum(1 for l in platform_logs if l['status'] in ['error', 'partial'])

    @api.model
    def get_pim_dashboard_data(self):
        """Returns a dictionary of all data needed for the dashboard."""
        
        # KPI Calculations
        active_connectors = self.env['platform.credentials'].search_count([('is_active', '=', True)])
        total_logs = self.env['pim.sync.log'].search_count([])
        total_mappings = self.env['pim.platform.mapping'].search_count([])
        total_products = self.env['product.template'].search_count([])

        # Get the raw XML architecture of the graph views
        graph_by_platform_arch = self.env.ref('odoo_pim_connector.view_pim_sync_log_graph_by_platform').arch
        graph_by_status_arch = self.env.ref('odoo_pim_connector.view_pim_sync_log_graph_by_status').arch

        return {
            'active_connectors': active_connectors,
            'total_logs': total_logs,
            'total_mappings': total_mappings,
            'total_products': total_products,
            'archs': {
                'graph_by_platform': graph_by_platform_arch,
                'graph_by_status': graph_by_status_arch,
            }
        }
