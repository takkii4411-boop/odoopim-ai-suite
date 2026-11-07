'''
Created on Feb 24, 2019

@author: Zuhair Hammadi
'''
from odoo import models, fields, api, tools, _
import logging
import inspect
from odoo.tools.safe_eval import safe_eval, test_python_expr
from odoo.exceptions import ValidationError
_logger = logging.getLogger(__name__)

_slots = ['tracking', "_depends", "_depends_context"]

for name in dir(fields):
    obj = getattr(fields, name)    
    if inspect.isclass(obj) and issubclass(obj, fields.Field):
        for attr in dir(obj):
            if attr == 'translate':
                continue
            attr_value = getattr(obj, attr)
            if (isinstance(attr_value, (int, str, tuple)) or attr_value is None) and not attr.startswith("_"):
                _slots.append(attr)

_slots = sorted(set(_slots))

class IrModelFieldAttribute(models.Model):
    _name = 'ir.model.fields.attribute'
    _inherit = ['cache.mixin']
    _description = 'Field Attribute'
    _auto_update_registry = True
    
    field_id = fields.Many2one('ir.model.fields', required = True, ondelete = 'cascade')
    model = fields.Char(related='field_id.model', store = True, readonly = True)
    name = fields.Char(related='field_id.name', store = True, readonly = True)
    attribute = fields.Selection([(a, a) for a in _slots], required = True) 
    value = fields.Char(required = True)
    code = fields.Text('Python Code')
    active = fields.Boolean(default = True)
                    
    _sql_constraints = [
        ('uk_attribute', 'unique(field_id, attribute)', 'Attribute must be unique!')
        ]    

    def name_get(self):
        res = []
        for record in self:
            res.append((record.id, '%s.%s - %s' % (record.field_id.model, record.field_id.name, record.attribute)))
        return res
    
    @api.constrains('attribute', "field_id")
    def _check_attribute(self):
        for record in self:
            model = self.env[record.model]
            field = model._fields[record.field_id.name]
            if not hasattr(field, record.attribute) and not model._valid_field_parameter(field, record.attribute):
                raise ValidationError(_("Invalid attribute %s for field %s") % (record.attribute, field))
        
    
    @api.constrains('code')
    def _check_code(self):
        for record in self:
            if record.code:
                msg = test_python_expr(record.code.strip(),mode='exec')
                if msg:
                    raise ValidationError(msg)
                
    @api.constrains('value')
    def _check_value(self):
        for record in self:
            if record.value:
                msg = test_python_expr(record.value.strip(),mode='eval')
                if msg:
                    raise ValidationError(msg)
                        
    def _update_fields_attributes(self):
        cr = self.env.cr
        if not tools.column_exists(cr, 'ir_model_fields_attribute', 'code'):
            return
        cr.execute("select model, name, attribute, value, code from ir_model_fields_attribute where active")
        
        for model_name, name, attribute, value, code in cr.fetchall():
            if attribute == 'translate':
                continue
            model = self.env.get(model_name)
            if model is None:
                continue
            field = model._fields.get(name)
            if field is None:
                continue
            
            localdict = self.env['ir.actions.actions']._get_eval_context()
            localdict['self'] = model
            try:
                if code:
                    safe_eval(code.strip(), localdict, mode='exec', nocopy = True)
                value = safe_eval(value, localdict)
                if attribute=='default' and not callable(value):
                    _value = value
                    value = lambda self: _value
                    
            except Exception as e:
                _logger.exception(e)
                continue
            
            setattr(field, attribute, value)       
            if attribute == 'required' and value and field.type == 'many2one' and field.ondelete == 'set null':
                field.ondelete = 'restrict'
             
    
    def _register_hook(self):
        super()._register_hook()
        self._update_fields_attributes()