from odoo import models, api
from odoo.exceptions import ValidationError

DEFAULT_CHANNEL = "global"


class Base(models.AbstractModel):
    _inherit = "base"

    def is_available_for_translation(self):
        """
        Check whether the current model is enabled for translation.
        Returns:
            bool: True if the model is allowed for translation, else False.
        """
        return bool(self.env.company.lc_available_model_ids.filtered(lambda m: m.model == self._name))

    def available_field_types(self):
        """
        Return the list of field types that are allowed for processing.
        Returns:
            list[str]: A list of allowed field type names.
        """
        return ['char', 'text']

    def update_field_channel_and_locale(self, values):
        """update the channel and lang values to channel.locale.save model """
        return self._update_field_channel_and_locale(values)

    def _update_field_channel_and_locale(self, values):
        """
        Bulk INSERT + ON CONFLICT UPDATE for all channel/locale values.
        Ensures ALL dictionaries are saved (not only the first).
        """
        self.check_access('write')
        if self.is_available_for_translation():
            self.ensure_one()
            for platform, items in values.items():
                model_name = f"x_{platform}_locale_save"
                Model = self.env[model_name]
                table = Model._table

                # Create unique index (x_res_model, x_res_id, x_field_name, x_lang_id)
                self.env.cr.execute(f"""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1
                            FROM pg_indexes
                            WHERE tablename = '{table}'
                            AND indexname = '{table}_unique_index'
                        ) THEN
                            EXECUTE '
                                CREATE UNIQUE INDEX {table}_unique_index
                                ON {table} (x_res_model, x_res_id, x_field_name, x_lang_id)
                            ';
                        END IF;
                    END $$;
                """)
                # Build SQL VALUES for bulk insert
                params = []
                placeholders = []

                for item in items:
                    placeholders.append("(%s, %s, %s, %s, %s)")
                    params.extend([
                        self._name,  # x_res_model
                        self.id,  # x_res_id
                        item["x_field_name"],
                        item["x_lang_id"],
                        item["x_value"],
                    ])

                if not placeholders:
                    continue  # nothing to save
                # Execute UPSERT (INSERT OR UPDATE)
                sql = f"""
                    INSERT INTO {table}
                        (x_res_model, x_res_id, x_field_name, x_lang_id, x_value)
                    VALUES
                        {",".join(placeholders)}
                    ON CONFLICT (x_res_model, x_res_id, x_field_name, x_lang_id)
                    DO UPDATE SET x_value = EXCLUDED.x_value
                """

                self.env.cr.execute(sql, params)

        return True

    def build_table_view(self, complete_list):
        """
        Convert:
            platform → lang → list of field dicts
        Into:
            platform → list of rows with:
                field metadata + lang metadata + value
        """

        # Fetch field labels and IDs
        model_fields = self.env['ir.model.fields'].sudo().search_read(
            [('model', '=', self._name)],
            ['name', 'field_description', 'id', 'ttype']
        )
        field_map = {f["name"]: f for f in model_fields}

        table_view = {}

        for platform, langs in complete_list.items():

            # all languages have same fields → take first lang structure
            first_lang = next(iter(langs.values()))
            field_names = [x["x_field_name"] for x in first_lang]

            table_view[platform] = []

            for fname in field_names:
                field_info = field_map.get(fname, {})

                row = {
                    "field_id": field_info.get("id"),
                    "x_field_name": fname,
                    "ttype": field_info.get('ttype'),
                    "field_label": field_info.get("field_description", fname),
                    "langs": {}
                }

                for lang_id, field_list in langs.items():
                    # find this field
                    lang_data = next((rec for rec in field_list if rec["x_field_name"] == fname), None)

                    if lang_data:
                        row["langs"][lang_id] = {
                            "x_lang_id": lang_id,
                            "lang_code": lang_data["lang_code"],
                            "lang_name": lang_data["lang_name"],
                            "x_value": lang_data["x_value"]
                        }

                table_view[platform].append(row)

        return table_view

    def build_empty_channel_locale_dict(self, field_names, channels):
        languages = self.env.company.pim_available_lang_ids
        empty_dict = {}
        for platform in channels:
            platform_code = platform
            empty_dict[platform_code] = {}
            for lang in languages:
                field_list = []
                for fname in field_names:
                    field_list.append({
                        "x_field_name": fname,
                        "x_value": "",
                        "x_lang_id": lang["id"],
                        "lang_code": lang["code"],
                        "lang_name": lang["name"],
                        "missing": True,
                    })

                empty_dict[platform_code][lang["id"]] = field_list
        return empty_dict

    def prepare_channel_local_vals(self, field_names=False, channels=False):
        return self._prepare_channel_local_vals(field_names, channels)

    def _prepare_channel_local_vals(self, field_names=False, channels=False):
        if not channels:
            channels = [DEFAULT_CHANNEL]
        if not field_names:
            fields = self.env['ir.model.fields'].sudo().search_read(
                [('model', '=', self._name),
                 ('name', 'in', list(self._fields.keys())),
                 ('m_translate', '=', True),
                 ('ttype', 'in', self.available_field_types())],
                ['id', 'name']
            )
            field_names = [f['name'] for f in fields]
        if not field_names:
            return {}
        complete_list = self.build_empty_channel_locale_dict(field_names, channels)
        # Add values from db to empty list
        for platform in channels:
            platform_code = platform
            vals = self.get_channel_locale_vals(field_names, platform_code)

            grouped_vals = {}
            if isinstance(vals, list):
                for item in vals:
                    lang = item["x_lang_id"]
                    grouped_vals.setdefault(lang, []).append(item)
            else:
                grouped_vals = vals

            for lang_id, lang_items in grouped_vals.items():
                if lang_id not in complete_list[platform_code]:
                    continue

                field_list = complete_list[platform_code][lang_id]

                for item in lang_items:
                    fname = item["x_field_name"]

                    for rec in field_list:
                        if rec["x_field_name"] == fname:
                            rec["x_value"] = item.get("x_value", "")
                            rec["missing"] = False
                            break
            for lang_id, field_list in complete_list[platform_code].items():
                for rec in field_list:
                    if rec["missing"]:
                        fname = rec["x_field_name"]
                        if hasattr(self, fname):
                            val = getattr(self, fname)
                            if val:
                                rec["x_value"] = val
                                rec["missing"] = False
        final_list = self.build_table_view(complete_list)
        return final_list

    def get_channel_locale_vals(self, field_names, channel=False, langs=[]):
        active_vals = self.env.user.get_channel_and_translation()

        model_name = f"x_{active_vals['active_channel']}_locale_save"
        if channel:
            model_name = f"x_{channel}_locale_save"

        if isinstance(field_names, str):
            field_names = [field_names]

        pg_array = "{" + ",".join(field_names) + "}"

        query = f"""
            SELECT *
            FROM {model_name}
            WHERE x_res_model = %s
              AND x_res_id = ANY(%s::int[])
              AND x_field_name = ANY(%s::text[])
              AND x_lang_id = ANY(%s::int[])
            ORDER BY x_field_name, x_lang_id;
        """
        if not langs:
            langs = active_vals["allowed_lang_ids"]

        params = [
            self._name,
            self.ids,
            pg_array,
            langs,
        ]

        self._cr.execute(query, params)
        return self._cr.dictfetchall()

    def check_system_ready(self):
        user, company = self.env.user, self.env.company
        if not company.is_channel_locale or not company.pim_available_lang_ids:
            raise ValidationError("You must enable the channel locale also add available languages for each company")
        if not user.m_lang_id:
            raise ValidationError("User Default Language Can not find")

    def action_attr_channel_locale_update(self):
        self.check_system_ready()
        datas = self.prepare_channel_local_vals()
        return {
            'type': 'ir.actions.client',
            'tag': 'attr_channel_locale_update',
            'params': {
                'title': 'All Channel Locale Update',
                'datas': datas,
                'resModel': self._name,
                'resId': self.id
            }
        }

    def get_read_channel(self):
        return DEFAULT_CHANNEL

    @api.model
    def read(self, fields=None, load='_classic_read'):
        res = super(Base, self).read(fields, load)
        active_vals = self.env.user.get_channel_and_translation()
        fields = self.env['ir.model.fields'].sudo().search_read(
            [('model', '=', self._name),
             ('name', 'in', list(self._fields.keys())),
             ('ttype', 'in', self.available_field_types())],
            ['id', 'name']
        )
        if not fields:
            return res
        field_names = [x['name'] for x in fields]
        langs = [active_vals['active_lang_id']]
        channel = self.get_read_channel()
        translations = self.get_channel_locale_vals(field_names, channel, langs)
        if translations:
            trans_map = {}
            for t in translations:
                rid = t["x_res_id"]
                fname = t["x_field_name"]
                val = t["x_value"] or ""

                if rid not in trans_map:
                    trans_map[rid] = {}

                trans_map[rid][fname] = val

            for rec in res:
                rid = rec["id"]
                if rid in trans_map:
                    for fname, tval in trans_map[rid].items():
                        if fname in rec:
                            rec[fname] = tval
        return res

    def prepare_channel_save_value(self, vals):
        channel = self.get_read_channel()
        active_vals = self.env.user.get_channel_and_translation()
        ret_val = {}
        if active_vals['active_lang_id']:
            field_model = self.env['ir.model.fields'].sudo()
            ret_val[channel] = []
            for key, val in vals.items():
                key_field = field_model.search([('ttype', 'in', self.available_field_types()),
                                                ('model', '=', self._name),
                                                ('name', '=', key)])
                if key_field:
                    ret_val[channel].append({'x_res_id': self.id,
                                             'x_res_model': self._name,
                                             'x_field_name': key,
                                             'x_lang_id': active_vals['active_lang_id'],
                                             'x_value': val})
        return ret_val

    def write(self, vals):
        if self.is_available_for_translation():
            values = self.prepare_channel_save_value(vals)
            res = super(Base, self).write(vals)
            if bool(values[self.get_read_channel()]):
                self.update_field_channel_and_locale(values)
            return res
        return super(Base, self).write(vals)
