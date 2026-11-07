from odoo import models, api

class IrUiView(models.Model):
    _inherit = 'ir.ui.view'

    @api.model
    def _get_inheriting_views(self):
        """Filter inheriting views to show only current company's list view"""
        # # Call original method
        # self.clear_caches()
        # self.env['ir.ui.view'].clear_caches()
        self.env.registry.clear_cache()
        views = super(IrUiView, self)._get_inheriting_views()

        # Check if any views are for product.template model
        product_template_views = views.filtered(
            lambda view: view.model_id.model == 'product.template')

        if product_template_views:
            # Get current company suffix
            company_name = self.env.company.name
            company_suffix = company_name.lower().replace(' ', '_').replace('-',
                                                                            '_')
            current_company_view_name = f"pim_product_list_view_columns_{company_suffix}"

            # Find all PIM list views (from all companies)
            pim_list_views = product_template_views.filtered(
                lambda view: view.name.startswith(
                    'pim_product_list_view_columns_')
            )

            if pim_list_views:
                # Filter: keep only current company's view, exclude others
                other_company_views = pim_list_views.filtered(
                    lambda view: view.name != current_company_view_name
                )

                # Remove other company views from the result
                views = views - other_company_views

        return views
