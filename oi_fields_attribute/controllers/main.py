'''
Created on Feb 26, 2019

@author: Zuhair Hammadi
'''
import json
from odoo import http, tools
from odoo.http import request
from ..models.ir_model_fields_attribute import _slots  

class FieldsAttribute(http.Controller):
    
    @http.route('/oi_fields_attribute/info', type='json', auth='user')
    def info(self, field_id):
                
        field_id = request.env['ir.model.fields'].browse(field_id)
        model = request.env[field_id.model]
        field = model._fields[field_id.name]
        
        attrs = {}
        for name in _slots:
            if name.startswith('_'):
                continue
            if not hasattr(field, name):
                continue
            value = getattr(field, name, None)
            if name =="compute" and isinstance(value, str):
                func = getattr(model, value, value)
                value = ("$FUNC", json.dumps(value), getattr(func, "__code__", None))
            
            elif callable(value):
                value = ("$FUNC", repr(value), getattr(value, "__code__", None))
                
            attrs[name] = value
        
        return {
            'model' : field_id.model,
            'name' : field_id.name,
            'type' : '%s.%s' % (type(field).__module__ ,  type(field).__name__),
            'attrs' : sorted(attrs.items())
            }
        

    @http.route('/oi_fields_attribute/database_info', type='json', auth='user')
    def database_info(self, field_id):
                
        field_id = request.env['ir.model.fields'].browse(field_id)
        model = request.env[field_id.model]
        field = model._fields[field_id.name]
        
        columns = tools.table_columns(request.env.cr, model._table)  # @UndefinedVariable
        attrs = columns.get(field_id.name)
        
        return {
            'model' : field_id.model,
            'name' : field_id.name,
            'type' : '%s.%s' % (type(field).__module__ ,  type(field).__name__),
            'attrs' : attrs and sorted(attrs.items()) or []
            }
        
