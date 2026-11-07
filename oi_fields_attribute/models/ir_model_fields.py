'''
Created on Feb 24, 2019

@author: Zuhair Hammadi
'''
from odoo import models, fields, api, tools

class IrModelFields(models.Model):
    _inherit = 'ir.model.fields'
    
    attribute_count = fields.Integer(compute = '_calc_attribute_count')
    attribute_ids = fields.One2many("ir.model.fields.attribute", "field_id")
    
    @api.depends('attribute_ids')
    def _calc_attribute_count(self):
        for record in self:
            record.attribute_count = len(record.attribute_ids)
    
    def action_attributes(self):                                                                 
        return {
            'type' : 'ir.actions.act_window',
            'name': 'Attributes',
            'res_model' : 'ir.model.fields.attribute',
            'domain' : [('field_id','=', self.id)],
            'view_mode' : 'tree,form',
            'views' : [(False, 'tree'), (False, 'form')],
            'context' : {
                'default_field_id' : self.id
                }
            }
                                        
    def _update_db(self):
        for model, records in self.grouped('model').items():
            model = self.env[model]
            columns = tools.table_columns(self.env.cr, model._table)
            for record in records:
                field = model._fields[record.name]
                field.update_db(model, columns)
                                
    def _recompute_all_records(self):
        translate_fields = {}
        summary = []
        for model, field_ids in self.grouped('model').items():
            model = self.env[model]
            records = model.search([])
            for field_id in field_ids:
                field = model._fields[field_id.name]                
                if field.store and field.compute:
                    self.env.add_to_compute(field, records)
                    summary.append(f"{field} {len(records)} records computed")
                    if field.translate:
                        for lang,_ in self.env['res.lang'].get_installed() :
                            if lang != self.env.lang:
                                translate_fields.setdefault(lang, []).append((field, records))
                                        
        self.env.flush_all()
        
        for lang, values in translate_fields.items():
            env = self.with_context(lang = lang).env
            for field, records in values:
                env.add_to_compute(field, records.with_env(env))
                summary.append(f"{field} {len(records)} records computed ({lang})")
            env.flush_all()
            
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'info' if summary else "warning",
                'message': '\n'.join(summary) if summary else "field not computed or not stored"
            }
        }
