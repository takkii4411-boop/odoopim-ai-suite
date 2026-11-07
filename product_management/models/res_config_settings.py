# -*- coding: utf-8 -*-

from lxml import etree
from lxml.builder import E

from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval

ALREADYADDEDFIELDS = [
    "image_128", "categ_id", "type", "lst_price", "product_variant_count", "product_variant_ids", "currency_id",
    "sale_ok", "purchase_ok", "purchase_ok", "qty_available", "uom_id", "website_published",
]


class res_config_settings(models.TransientModel):
    """
    Overwrite to add settings required for product management interface
    """
    _inherit = "res.config.settings"

    @api.onchange("module_product_management_website_sale")
    def _compute_product_management_eshop_categories_option(self):
        """
        Compute method method for module_product_management_website_sale
        """
        for conf in self:
            if not conf.module_product_management_website_sale:
                conf.product_management_eshop_categories_option = False

    @api.depends("ir_actions_server_ids_str")
    def _compute_ir_actions_server_prm_default_model_id(self):
        """
        Compute method for ir_actions_server_prm_default_model_id
        """
        template_model_id = self.env["ir.model"].search([("model", "=", "product.template")], limit=1).id
        for conf in self:
            conf.ir_actions_server_prm_default_model_id = template_model_id

    @api.depends("ir_actions_server_ids_str")
    def _compute_ir_actions_server_ids(self):
        """
        Compute method for ir_actions_server_ids
        """
        for setting in self:
            ir_actions_server_ids = []
            if setting.ir_actions_server_ids_str:
                try:
                    actions_list = safe_eval(setting.ir_actions_server_ids_str)
                    ir_actions_server_ids = self.env["ir.actions.server"].search([("id", "in", actions_list)]).ids
                except Exception as e:
                    ir_actions_server_ids = []
            setting.ir_actions_server_ids = [(6, 0, ir_actions_server_ids)]

    @api.depends("kanban_fields_ids_str")
    def _compute_kanban_fields_ids(self):
        """
        Compute method for kanban_fields_ids
        """
        for setting in self:
            kanban_fields_ids = []
            if setting.kanban_fields_ids_str:
                try:
                    kanban_fields_list = safe_eval(setting.kanban_fields_ids_str)
                    kanban_fields_ids = self.env["ir.model.fields"].search([("id", "in", kanban_fields_list)]).ids
                except:
                    kanban_fields_ids = []
            setting.kanban_fields_ids = [(6, 0, kanban_fields_ids)]

    def _inverse_ir_actions_server_ids(self):
        """
        Inverse method for ir_actions_server_ids
        """
        for setting in self:
            ir_actions_server_ids_str = ""
            if setting.ir_actions_server_ids:
                ir_actions_server_ids_str = "{}".format(setting.ir_actions_server_ids.ids)
            setting.ir_actions_server_ids_str = ir_actions_server_ids_str

    def _inverse_kanban_fields_ids(self):
        """
        Inverse method for kanban_fields_ids
        """
        for setting in self:
            kanban_fields_ids_str = ""
            if setting.kanban_fields_ids:
                kanban_fields_ids_str = "{}".format(setting.kanban_fields_ids.ids)
            if setting.kanban_fields_ids_str != kanban_fields_ids_str:
                setting.sudo()._update_kanban_view(setting.kanban_fields_ids)
                setting.kanban_fields_ids_str = kanban_fields_ids_str

    module_product_management_website_sale = fields.Boolean(string="E-commerce mass actions")
    module_product_management_accounting = fields.Boolean(string="Accounting mass actions")
    module_product_management_stock = fields.Boolean(string="Warehouse mass actions")
    module_product_management_purchase = fields.Boolean(string="Purchase mass actions")
    product_management_export_option = fields.Boolean(
        string="Export products",
        config_parameter="product_management_export_option"
    )
    product_management_attributes_option = fields.Boolean(
        string="Filter by attribute values",
        config_parameter="product_management_attributes_option",
    )
    product_management_tags_option = fields.Boolean(
        string="Filter by tags",
        config_parameter="product_management_tags_option",
    )
    product_management_eshop_categories_option = fields.Boolean(
        string="Filter by eCommerce categories",
        config_parameter="product_management_eshop_categories_option",
        compute=_compute_product_management_eshop_categories_option,
        store=True,
        readonly=False,
    )
    ir_actions_server_prm_default_model_id = fields.Many2one(
        "ir.model",
        compute=_compute_ir_actions_server_prm_default_model_id,
        string="Default PRM model"
    )
    ir_actions_server_ids = fields.Many2many(
        "ir.actions.server",
        compute=_compute_ir_actions_server_ids,
        inverse=_inverse_ir_actions_server_ids,
        string="Product mass actions",
        domain=[("model_name", "=", "product.template")],
    )
    ir_actions_server_ids_str = fields.Char(
        string="Product mass actions (Str)",
        config_parameter="product_management.ir_actions_server_ids",
    )
    kanban_fields_ids = fields.Many2many(
        "ir.model.fields",
        compute=_compute_kanban_fields_ids,
        inverse=_inverse_kanban_fields_ids,
        string="Kanban Fields",
    )
    kanban_fields_ids_str = fields.Char(
        string="Kanban Fields (Str)",
        config_parameter="product_management.kanban_fields_ids"
    )

    @api.model
    def _update_kanban_view(self, cfields):
        """
        The method to update the view of product.template kanban

        Args:
         * cfields - ir.model.fields recordset
        """
        view_id = self.env["ir.ui.view"].search([("key", "=", "prmnt_custom_product_template_kanban")], limit=1)
        if not view_id:
            xml_content = """
                <data>
                    <ul name="custom_properties" position="after"/>
                    <ul name="custom_checkboxes" position="after"/>
                </data>
            """
            values = {
                "arch": xml_content,
                "model": "product.template",
                "key": "prmnt_custom_product_template_kanban",
                "type": "kanban",
                "inherit_id": self.sudo().env.ref("product_management.product_template_kanban_view").id,
            }
            view_id = self.env["ir.ui.view"].create(values)
        xml_content = ""
        xml_checkboxes = []
        xml_properties = []
        for cfield in cfields:
            if cfield.name not in ALREADYADDEDFIELDS:
                if cfield.ttype == "boolean":
                    attrs = {"widget": "boolean"}
                    xml_checkboxes.append(E.li(E.field(name=cfield.name, **attrs), cfield.field_description))
                else:
                    attrs = {}
                    if cfield.ttype in ["one2many", "many2many"]:
                        attrs.update({"widget": "many2many_tags"})
                    if cfield.ttype in ["html"]:
                        attrs.update({"widget": "html"})
                    xml_properties.append(E.li(cfield.field_description, ": ", E.field(name=cfield.name, **attrs)))

        xml_properties = E.ul(
            E.ul(*(xml_properties), name="custom_properties",), name="custom_properties", position="replace",
        )
        xml_checkboxes = E.ul(
            E.ul(*(xml_checkboxes), name="custom_checkboxes",), name="custom_checkboxes", position="replace",
        )
        xml_content += etree.tostring(xml_properties, pretty_print=True, encoding="unicode")
        xml_content += etree.tostring(xml_checkboxes, pretty_print=True, encoding="unicode")
        xml_content = u"<data>{}</data>".format(xml_content)
        view_id.write({"arch": xml_content})
