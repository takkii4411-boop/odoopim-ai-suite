# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json
import base64
import logging

_logger = logging.getLogger(__name__)


class ProductAssociationController(http.Controller):

    @http.route('/pim/association/get_products', type='json', auth='user')
    def get_products(self, current_product_id=None, association_type_id=None,
                     company_id=None, **kwargs):
        """Fetch products for association dialog"""
        try:
            cr = request.env.cr

            if not company_id:
                company_id = request.env.company.id

            # Get existing associations
            existing_associations = []
            if current_product_id and association_type_id:
                cr.execute("""
                           SELECT associated_product_ids
                           FROM product_association
                           WHERE product_id = %s
                             AND association_type_id = %s
                           """, (current_product_id, association_type_id))
                result = cr.fetchone()
                if result and result[0]:
                    existing_associations = result[0] if isinstance(result[0],
                                                                    list) else []

            # Fetch products excluding current one
            exclude_id = current_product_id if current_product_id else 0

            product_query = """
                            SELECT pt.id, \
                                   pt.name, \
                                   pt.sku, \
                                   pt.percentage_complete, \
                                   pt.active, \
                                   pt.family_id, \
                                   pt.company_id
                            FROM product_template pt
                            WHERE pt.active = true
                              AND (pt.company_id = %s OR pt.company_id IS NULL)
                              AND pt.id != %s
                            ORDER BY pt.name \
                            """
            cr.execute(product_query, (company_id, exclude_id))
            products_data = cr.dictfetchall()

            if not products_data:
                return {
                    'success': True,
                    'products': [],
                    'categories': [],
                    'families': [],
                    'existing_associations': existing_associations,
                }

            product_ids = [p['id'] for p in products_data]

            # Fetch images using ORM
            ProductTemplate = request.env['product.template']
            products_orm = ProductTemplate.browse(product_ids)

            product_images = {}
            for p in products_orm:
                if p.image_128:
                    try:
                        product_images[p.id] = p.image_128
                    except Exception as e:
                        _logger.warning(
                            f"Error loading image for product {p.id}: {e}")
                        product_images[p.id] = None

            # Fetch category relationships
            category_relations = self._fetch_category_relations(cr, product_ids,
                                                                company_id)

            product_categories = {}
            for rel in category_relations:
                prod_id = rel['product_template_id']
                if prod_id not in product_categories:
                    product_categories[prod_id] = []
                product_categories[prod_id].append(rel['product_category_id'])

            # Fetch families
            family_ids = list(set([p['family_id'] for p in products_data if
                                   p.get('family_id')]))
            family_names = {}
            if family_ids:
                cr.execute("""
                           SELECT id, code, name
                           FROM family_attribute
                           WHERE id = ANY (%s)
                             AND (company_id = %s OR company_id IS NULL)
                           """, (family_ids, company_id))
                for fam in cr.dictfetchall():
                    family_names[fam['id']] = fam.get('name')

            # Fetch categories
            cr.execute("""
                       SELECT id, name
                       FROM pim_category
                       WHERE active = true
                         AND (company_id = %s OR company_id IS NULL)
                       ORDER BY name
                       """, (company_id,))
            categories = [{'id': c['id'],
                           'name': self._parse_translatable_field(c['name'])}
                          for c in cr.dictfetchall()]

            # Fetch families
            cr.execute("""
                       SELECT id, code, name
                       FROM family_attribute
                       WHERE (company_id = %s OR company_id IS NULL)
                       ORDER BY code
                       """, (company_id,))
            families = [{'id': f['id'], 'name': f.get('name')}
                        for f in cr.dictfetchall()]

            # Process products
            products = []
            for product in products_data:
                product_name = self._parse_translatable_field(product['name'])

                family_tuple = False
                if product.get('family_id') and product[
                    'family_id'] in family_names:
                    family_tuple = [product['family_id'],
                                    family_names[product['family_id']]]

                products.append({
                    'id': product['id'],
                    'name': product_name or '',
                    'sku': product.get('sku') or '',
                    'image_1920': product_images.get(product['id']),
                    'percentage_complete': float(
                        product.get('percentage_complete') or 0),
                    'active': product['active'],
                    'family_id': family_tuple,
                    'pim_category_ids': product_categories.get(product['id'],
                                                               [])
                })

            return {
                'success': True,
                'products': products,
                'categories': categories,
                'families': families,
                'existing_associations': existing_associations,
            }

        except Exception as e:
            _logger.error("Error in get_products: %s", str(e), exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'products': [],
                'categories': [],
                'families': [],
                'existing_associations': [],
            }

    @http.route('/pim/association/get_associated_products', type='json',
                auth='user')
    def get_associated_products(self, product_id, association_type_id,
                                **kwargs):
        """Get associated products for display in form view"""
        try:
            cr = request.env.cr

            # Get association record
            cr.execute("""
                       SELECT associated_product_ids
                       FROM product_association
                       WHERE product_id = %s
                         AND association_type_id = %s
                       """, (product_id, association_type_id))

            result = cr.fetchone()

            if not result or not result[0]:
                return {'success': True, 'products': []}

            product_ids = result[0] if isinstance(result[0], list) else []

            if not product_ids:
                return {'success': True, 'products': []}

            # Fetch product details using ORM
            ProductTemplate = request.env['product.template']
            products = ProductTemplate.browse(product_ids)

            products_data = []
            for p in products:
                products_data.append({
                    'id': p.id,
                    'name': p.name,
                    'sku': p.sku or '',
                    'image_128': p.image_128,
                    'percentage_complete': p.percentage_complete or 0,
                    'active': p.active,
                    'family_id': p.family_id.name if p.family_id else ''
                })

            return {
                'success': True,
                'products': products_data
            }

        except Exception as e:
            _logger.error("Error in get_associated_products: %s", str(e),
                          exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'products': []
            }

    @http.route('/pim/association/save_associations', type='json', auth='user')
    def save_associations(self, source_product_id, associated_product_ids,
                          association_type_id, **kwargs):
        """Save associations"""
        try:
            cr = request.env.cr
            uid = request.env.uid

            if not source_product_id or not association_type_id:
                return {'success': False,
                        'error': 'Missing required parameters'}

            # Check if record exists
            cr.execute("""
                       SELECT id
                       FROM product_association
                       WHERE product_id = %s
                         AND association_type_id = %s
                       """, (source_product_id, association_type_id))

            existing = cr.fetchone()

            # Convert to JSON array
            ids_json = json.dumps(associated_product_ids)

            if existing:
                cr.execute("""
                           UPDATE product_association
                           SET associated_product_ids = %s::jsonb,
                        write_uid = %s
                             , write_date = NOW()
                           WHERE id = %s
                           """, (ids_json, uid, existing[0]))
            else:
                cr.execute("""
                           INSERT INTO product_association
                           (product_id, association_type_id,
                            associated_product_ids, create_uid, create_date,
                            write_uid, write_date)
                           VALUES (%s, %s, %s::jsonb, %s, NOW(), %s, NOW())
                           """,
                           (source_product_id, association_type_id, ids_json,
                            uid, uid))

            cr.commit()

            return {
                'success': True,
                'total': len(associated_product_ids)
            }

        except Exception as e:
            cr.rollback()
            _logger.error("Error in save_associations: %s", str(e),
                          exc_info=True)
            return {'success': False, 'error': str(e)}

    @http.route('/pim/association/get_types', type='json', auth='user')
    def get_association_types(self, company_id=None, product_id=None, **kwargs):
        """Get all active association types with counts"""
        try:
            cr = request.env.cr

            if not company_id:
                company_id = request.env.company.id

            cr.execute("""
                       SELECT id, name, code, color, sequence
                       FROM product_association_type
                       WHERE active = true
                         AND (company_id = %s OR company_id IS NULL)
                       ORDER BY sequence, name
                       """, (company_id,))

            types_data = []
            for atype in cr.dictfetchall():
                count = 0
                if product_id:
                    cr.execute("""
                               SELECT associated_product_ids
                               FROM product_association
                               WHERE product_id = %s
                                 AND association_type_id = %s
                               """, (product_id, atype['id']))
                    result = cr.fetchone()
                    if result and result[0]:
                        ids_list = result[0] if isinstance(result[0],
                                                           list) else []
                        count = len(ids_list)

                types_data.append({
                    'id': atype['id'],
                    'name': self._parse_translatable_field(atype['name']),
                    'code': atype['code'],
                    'color': atype.get('color', 0),
                    'sequence': atype.get('sequence', 10),
                    'count': count
                })

            return {
                'success': True,
                'types': types_data
            }

        except Exception as e:
            _logger.error("Error in get_association_types: %s", str(e),
                          exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'types': []
            }

    def _fetch_category_relations(self, cr, product_ids, company_id):
        """Helper to fetch category relationships"""
        try:
            cr.execute("""
                       SELECT table_name
                       FROM information_schema.tables
                       WHERE table_name LIKE '%product_template%category%rel%'
                         AND table_schema = 'public' LIMIT 1
                       """)
            rel_table_row = cr.fetchone()

            if not rel_table_row:
                return []

            rel_table = rel_table_row[0]

            cr.execute("""
                       SELECT column_name
                       FROM information_schema.columns
                       WHERE table_name = %s
                         AND column_name LIKE '%%category%%' LIMIT 1
                       """, (rel_table,))

            category_col_row = cr.fetchone()
            category_col_name = category_col_row[
                0] if category_col_row else 'pim_category_id'

            query = f"""
                SELECT rel.product_template_id, rel.{category_col_name} as product_category_id 
                FROM {rel_table} rel
                INNER JOIN pim_category cat ON cat.id = rel.{category_col_name}
                WHERE rel.product_template_id = ANY(%s)
                  AND (cat.company_id = %s OR cat.company_id IS NULL)
            """
            cr.execute(query, (product_ids, company_id))
            return cr.dictfetchall()

        except Exception as e:
            _logger.warning("Error fetching category relations: %s", str(e))
            return []

    def _parse_translatable_field(self, value):
        """Parse translatable fields"""
        if not value:
            return ''

        if isinstance(value, str) and value.startswith('{'):
            try:
                value = json.loads(value)
            except:
                return value

        if isinstance(value, dict):
            return value.get('en_US') or list(value.values())[
                0] if value else ''

        return value