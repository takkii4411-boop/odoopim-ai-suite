#coding: utf-8

import json
import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval


_logger = logging.getLogger(__name__)


class product_template(models.Model):
    """
    Re-write to add methods required by js interface
    """
    _inherit = "product.template"

    @api.depends("attribute_line_ids", "attribute_line_ids.attribute_id", "attribute_line_ids.value_ids")
    def _compute_attribute_values_to_search_ids(self):
        """
        Compute method for attribute_values_to_search_ids
        """
        for templ in self:
            value_ids = []
            attribute_ids = []
            for attr_line in templ.attribute_line_ids:
                value_ids += attr_line.value_ids.ids
                attribute_ids.append(attr_line.attribute_id.id)
            templ.attribute_values_to_search_ids = [(6, 0, value_ids)]
            templ.attribute_to_search_ids = [(6, 0, attribute_ids)]

    attribute_values_to_search_ids = fields.Many2many(
        "product.attribute.value",
        "product_attribute_value_product_template_prm_rel_table",
        "product_attribute_value_id",
        "product_template_id",
        string="All possible values",
        compute=_compute_attribute_values_to_search_ids,
        store=True,
    )
    attribute_to_search_ids = fields.Many2many(
        "product.attribute",
        "product_attribute_product_template_prm_rel_table",
        "product_attribute_id",
        "product_template_id",
        string="All possible attributes",
        compute=_compute_attribute_values_to_search_ids,
        store=True,
    )

    @api.model
    def action_return_mass_actions(self):
        """
        The method to return available mass actions in js format

        Returns:
         * list of dict
           ** id
           ** name
        """
        result = []
        self = self.sudo()
        Config = self.env["ir.config_parameter"].sudo()
        mass_actions_list = safe_eval(Config.get_param("product_management.ir_actions_server_ids", "[]"))
        mass_action_ids = self.env["ir.actions.server"].search([("id", "in", mass_actions_list)])
        for mass_action in mass_action_ids:
            if not mass_action.groups_id or (self.env.user.groups_id & mass_action.groups_id):
                result.append({"id": mass_action.id, "name": mass_action.name})
        return result

    @api.model
    def action_return_export_conf(self):
        """
        The method to return available mass actions in js format

        Returns:
         * bool
        """
        Config = self.env["ir.config_parameter"].sudo()
        export_conf = safe_eval(Config.get_param("product_management_export_option", "False"))
        return export_conf

    @api.model
    def action_proceed_mass_action(self, products_list, action_id):
        """
        The method to trigger mass action for selected products

        Args:
         * products_list - list of ints (product IDs)
         * action_id - int - ir.actions.server id

        Methods:
         * run() of ir.actions.server

        Returns:
         * dict: either action dict, or special view dict, or empty dict if no result

        Extra info:
         * we use api@model with search to make sure each record exists (e.g. deleted in meanwhile)
        """
        product_ids = self.env["product.template"].with_context(active_test=False).search([("id", "in", products_list)])
        result = {}
        if product_ids:
            action_server_id = self.env["ir.actions.server"].browse(action_id)
            if action_server_id.exists():
                action_context = {
                    "active_id": product_ids[0].id,
                    "active_ids": product_ids.ids,
                    "active_model": self._name,
                    "record": product_ids[0],
                    "records": product_ids,
                    "default_product_tmpl_id": product_ids[0].id, # just to make "action_open_routes_diagram' work
                }
                result = action_server_id.with_context(action_context).run()
                if result and result.get("type"):
                    local_context = {}
                    if result.get("context"):
                        local_context = result.get("context")
                        if not isinstance(local_context, dict):
                            local_context = json.loads(result.get("context"))
                    local_context.update({"default_product_ids": [(6, 0, product_ids.ids)]})
                    result["context"] = local_context
        return result or {}

    @api.model
    def action_get_hierarchy(self, key):
        """
        The method to prepare hierarchy

        Args:
         * key - string - js tree reference

        Methods:
         * _return_categories_hierarchy of product.category
         * _return_attributes_and_values of product.attribute
         * _return_eshop_categories_hierarchy of product template
         * _return_tags_hierarchy of product.tag

        Returns:
         * list of dicts
        """
        result = []
        if key == "categories":
            result = self.env["product.category"]._return_categories_hierarchy()
        elif key == "attributes":
            result = self.env["product.attribute"]._return_attributes_and_values()
        elif key == "eshop_categories":
            result = self.env["product.template"]._return_eshop_categories_hierarchy()
        elif key == "product_tags":
            result = self.env["product.tag"]._return_tags_hierarchy()
        return result

    @api.model
    def _return_eshop_categories_hierarchy(self):
        """
        The method to return hierarchy of e-shop categories in jstree format
        DUMMY method to be implemented in product_management_website_sale
        """
        return []
