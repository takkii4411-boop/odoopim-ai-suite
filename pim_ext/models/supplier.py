from odoo import fields, models, api, _


class SupplierInformation(models.Model):
    _name = 'supplier.info'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Supplier Information'

    name = fields.Char('Supplier Name', required=True)
    street = fields.Char('Address Line')
    city = fields.Char('City')
    website = fields.Char('Website Link')
    notes = fields.Text('Notes')
    completeness = fields.Float(string='Completeness', compute='_compute_completeness')
    company_id = fields.Many2one('res.company', required=True, readonly=False, default=lambda self: self.env.company)

    def _compute_completeness(self):
        for rec in self:
            required_supplier_fields = self.env['general.attribute'].search([
                ('completeness', '=', True),
                ('related_field.model_id.model', '=', 'supplier.info')
            ])
            field_list = required_supplier_fields.mapped('related_field').mapped('name')
            filled_count = 0
            total_count = 0
            for field in field_list:
                if getattr(rec, field, False):
                    filled_count += 1
                total_count += 1
            if total_count > 0:
                rec.completeness = (filled_count / total_count) * 100
            else:
                rec.completeness = 0
