from odoo import models, fields, api, _


class CloneProductWizard(models.TransientModel):
    _name = 'delete.family.wizard'
    _description = 'Delete family attribute before assign another family'

    family_id = fields.Many2one('family.attribute',string="Alternate Family", domain="[('id','!=',current_family_id)]")
    current_family_id = fields.Many2one('family.attribute', string="Current Family")
    company_id = fields.Many2one('res.company', required=True, readonly=True, default=lambda self: self.env.company)

    def change_family(self):
        products = self.env['product.management'].search([('family_id','=',self.current_family_id.id)])
        products.write({'family_id': self.family_id.id})

        self.current_family_id.unlink()

        return {
        'name': _('Family'),
        'view_type': 'list',
        'view_mode': 'list',
        'view_id': self.env.ref('pim_ext.view_family_attribute_tree').id,
        'res_model': 'family.attribute',
        # 'context': "{'type':'out_invoice'}",
        'type': 'ir.actions.act_window',
        'target': 'current',
    }

