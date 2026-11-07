
from odoo import http
from odoo.http import request, Response
import json
import re
import requests
from odoo import models, fields, api
import difflib  # <-- ADD THIS IMPORT
import time


class AiBotController(http.Controller):

    # -------------------------------
    #  Ccommon AI Summarization Function
    # -------------------------------
    def summarize_with_ai(self, user_question, raw_data, context=""):
        """Send any DB results + question to AI for summarization"""
        try:
            api_key = request.env['ir.config_parameter'].sudo().get_param('ai_bot_odoopim.ai_bot_odoopim_api_key')
            ai_model = request.env['ir.config_parameter'].sudo().get_param('ai_bot_odoopim.ai_bot_odoopim_model')
            ai_url = 'https://api.groq.com/openai/v1/chat/completions'

            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}'
            }

            ai_prompt = f"""
    User Question: "{user_question}"

    Context: {context}

    Database Result:
    {json.dumps(raw_data, indent=2, ensure_ascii=False)}

    Instructions: Provide a clear, concise natural language summary.
    Do not ignore DB results. If count is 0, clearly say no products found.
                """

            payload = {
                "model": ai_model,
                "messages": [{"role": "user", "content": ai_prompt}],
                "stream": False,
                "temperature": 0.3,
                "max_tokens": 1200,
                "top_p": 1
            }

            response = requests.post(ai_url, headers=headers, json=payload)
            if response.status_code == 200:
                content = response.json()
                return content['choices'][0]['message'].get('content', '')
            else:
                return f"(AI summarization failed, status {response.status_code}). Raw: {raw_data}"

        except Exception as e:
            return f"Error in AI summarization: {str(e)} | Raw: {raw_data}"

    @http.route('/get_api_key', auth='public', methods=['GET'], csrf=False)
    def get_api_key(self):
        api_key = request.env['ir.config_parameter'].sudo().get_param('ai_bot_odoopim.ai_bot_odoopim_api_key')
        ai_model = request.env['ir.config_parameter'].sudo().get_param('ai_bot_odoopim.ai_bot_odoopim_model')
        return request.make_response(json.dumps({'api_key': api_key, 'model': ai_model}),
                                     headers={'Content-Type': 'application/json'})

    @http.route('/groq_api/stop', auth='public', methods=['POST'], csrf=False)
    def stop_process_route(self, **kwargs):
        # Set the stop flag to True
        AiBotController.stop_process = True
        print("Response Stopped")
        return json.dumps({'message': 'Stop signal received, process will be aborted.'})



    #
    # def ai_summarize(message, ai_model, ai_url, headers):
    #     ai_prompt = f"Give a very short and polite response to the user:\n{message}"
    #     payload = {
    #         "model": ai_model,
    #         "messages": [{"role": "user", "content": ai_prompt}],
    #         "stream": False,
    #         "temperature": 0.5,
    #         "max_tokens": 50,
    #         "top_p": 1
    #     }
    #     try:
    #         response = requests.post(ai_url, headers=headers, json=payload)
    #         if response.status_code == 200:
    #             content = response.json()['choices'][0]['message'].get('content', '').strip()
    #             return content if content else message
    #     except Exception as e:
    #         print("ERROR in AI summarization:", str(e))
    #     return message  # fallback

    @http.route('/groq_api', auth='public', methods=['POST'], csrf=False)
    def main_route(self, **kwargs):
        print("DEBUG: /groq_api called")
        AiBotController.stop_process = False

        if AiBotController.stop_process:
            print("DEBUG: Process stopped early")
            return json.dumps({'message': 'Process stopped by user'})

        try:
            request_data = json.loads(request.httprequest.data)
            user_question = request_data.get('question', 'No question provided')
            print("DEBUG: User Question:", user_question)

            # Initialize conversation history
            if 'conversation_history' not in request.session:
                request.session['conversation_history'] = []
                print("DEBUG: Initialized conversation history")

            # --- Keyword definitions ---
            sales_keywords = ["sales order", "sale order", "sale number", "sale", "order details", "order status",
                              "sales", "quotation"]
            contact_keywords = ["who", "who is", "customer", "persons", "person", "contact", "contacts", "about",
                                "associations", "association"]
            odoopim_keywords = ["odoopim", "sku","id=","id"]
            product_count_keywords = ["how many products", "product count", "number of products", "total products"]
            brand_keywords = ["brand", "brands"]
            completeness_keywords = ["completeness", "completed", "complete", "completion", "progress",
                                     "percentage complete"]
            quality_keywords = ["quality", "grade", "category a", "category b", "category c", "category d",
                                "category e"]

            # --- Flags ---
            is_sales_related = any(keyword in user_question.lower() for keyword in sales_keywords)
            is_contact_related = any(keyword in user_question.lower() for keyword in contact_keywords)
            is_odoopim_related = any(keyword in user_question.lower() for keyword in odoopim_keywords)
            is_product_count_related = any(keyword in user_question.lower() for keyword in product_count_keywords)
            is_brand_related = any(keyword in user_question.lower() for keyword in brand_keywords)
            is_completeness_related = any(keyword in user_question.lower() for keyword in completeness_keywords)
            is_quality_related = any(keyword in user_question.lower() for keyword in quality_keywords)

            print(
                f"DEBUG: Flags - Sales: {is_sales_related}, Contact: {is_contact_related}, OdooPIM: {is_odoopim_related}, "
                f"Product Count: {is_product_count_related}, Brand: {is_brand_related}, "
                f"Completeness: {is_completeness_related}, Quality: {is_quality_related}")

            response_message = ""
            odoopim_content = None

                # api_key = request.env['ir.config_parameter'].sudo().get_param('ai_bot.ai_bot_api_key')
            api_key = request.env['ir.config_parameter'].sudo().get_param('ai_bot_odoopim.ai_bot_odoopim_api_key')
            ai_model = request.env['ir.config_parameter'].sudo().get_param('ai_bot_odoopim.ai_bot_odoopim_model')

            # ai_model = request.env['ir.config_parameter'].sudo().get_param('ai_bot.ai_bot_model')
            ai_url = 'https://api.groq.com/openai/v1/chat/completions'
            headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {api_key}'}

            # --- 1. Brand Queries ---
            if is_brand_related:
                print("DEBUG: Brand-related question detected")
                brand_match = re.search(r'(?:in|for|of|under)\s+([\w\s]+?)(?:\s+brand|$)', user_question.lower())
                brand_name = brand_match.group(1).strip() if brand_match else None
                print("DEBUG: Extracted Brand Name:", brand_name)

                if brand_name:
                    domain = ['|', ('brand_id.name', 'ilike', brand_name), ('name', 'ilike', brand_name)]
                    if 'brand' in request.env['product.template']._fields:
                        domain.insert(0, '|')
                        domain.append(('brand', 'ilike', brand_name))
                    products = request.env['product.template'].sudo().search(domain)
                    product_count = len(products)
                    print(f"DEBUG: Found {product_count} products for brand '{brand_name}'")

                    product_data = []
                    for p in products[:20]:
                        # product_data.append({
                        #     "name": p.name,
                        #     "sku": p.default_code or "N/A",
                        #     "brand": p.brand_id.name if p.brand_id else "Not specified"
                        # })
                        product_data.append({
                            "name": p.name,
                            "sku": p.default_code or "N/A",
                            # If brand is not set, infer it from product name
                            "brand": p.brand_id.name if p.brand_id else
                            ("Whirlpool" if "whirlpool" in p.name.lower() else
                             "Samsung" if "samsung" in p.name.lower() else
                             "Godrej" if "godrej" in p.name.lower() else
                             "Inferred from product name")
                        })
                    print("DEBUG: Prepared product data for AI summarization")

                    try:
                        # ai_prompt = f"Summarize the following product list for user query: '{user_question}'. Provide concise, clear information.\nProducts: {json.dumps(product_data, indent=2)}"
                        # payload = {
                        #     "model": ai_model,
                        #     "messages": [{"role": "user", "content": ai_prompt}],
                        #     "stream": False,
                        #     "temperature": 0.7,
                        #     "max_tokens": 500,
                        #     "top_p": 1
                        # }
                        # print("DEBUG: Sending Brand AI Payload to AI")

                        ai_prompt = f"""User Query: "{user_question}"

                        Database Search Result: Found {product_count} products for brand '{brand_name}'

                        Product Details:
                        {json.dumps(product_data, indent=2)}

                        Instructions: Based on the database results above, provide a clear summary. If products are found, list them. Do not ignore the database results."""

                        payload = {
                            "model": ai_model,
                            "messages": [{"role": "user", "content": ai_prompt}],
                            "stream": False,
                            "temperature": 0.3,  # Lower temperature for more consistent results
                            "max_tokens": 1500,
                            "top_p": 1
                        }
                        print("DEBUG: Sending Improved Brand AI Payload to AI")
                        response = requests.post(ai_url, headers=headers, json=payload)
                        if response.status_code == 200:
                            response_content = response.json()
                            response_message = response_content['choices'][0]['message'].get('content', '')
                            print("DEBUG: AI Response for Brand:", response_message)
                        else:
                            response_message = f"Found {product_count} products for '{brand_name}', but AI summarization failed."
                            print("DEBUG: Brand AI call failed with status:", response.status_code)
                    except Exception as e:
                        response_message = f"Error during AI summarization: {str(e)}"
                        print("ERROR in Brand AI summarization:", str(e))
                # else:
                #     response_message = "Please specify a brand name (e.g., 'products in Samsung brand')."
                #     print("DEBUG: Brand name not found in query")

                    # ... [previous code] ...

                else:
                    # Brand name not found in query. Use AI to generate a helpful response.
                    print("DEBUG: Brand name not found in query, generating AI-powered response.")
                    try:
                        # Create a prompt that explains the situation to the AI
                        ai_error_prompt = f"""
                        User Query: "{user_question}"

                        The user is asking about products by brand in Odoo, but the specific brand name could not be clearly identified from their query.

        Your Task: Generate a short, two-line response. You MUST follow these instructions exactly:

        - **First Line:** You MUST use this exact sentence: 'Please specify a brand name (e.g., 'products in Samsung brand').'
        - **Second Line:** Write a short, follow-up sentence that explains why using this specific format is necessary for an accurate search.

        **Important:** Do not use markdown. Just write the two lines of text.
        """

                        error_payload = {
                            "model": ai_model,
                            "messages": [{"role": "user", "content": ai_error_prompt}],
                            "stream": False,
                            "temperature": 0.7,  # Slightly higher temp for more varied phrasing
                            "max_tokens": 150,
                        }
                        # Call the AI to generate the dynamic error message
                        error_response = requests.post(ai_url, headers=headers, json=error_payload)
                        if error_response.status_code == 200:
                            error_content = error_response.json()
                            # Use the AI's generated message
                            response_message = error_content['choices'][0]['message'].get('content',
                                                                                          'Please specify a brand name (e.g., "Samsung products").')
                            print("DEBUG: Dynamic AI Error Response:", response_message)
                        else:
                            # Fallback to a static message if the AI call fails
                            response_message = "I'd be happy to help you find products by brand. Could you please specify which brand you're looking for? For example, you could ask about 'Samsung products'."
                            print("DEBUG: AI Error call failed, using fallback.")
                    except Exception as e:
                        response_message = "I'd be happy to help you find products by brand. Could you please specify which brand you're looking for?"
                        print("ERROR generating dynamic error message:", str(e))

            # --- 2. Product Count Queries ---
            elif is_product_count_related:
                print("DEBUG: Product count related question detected")

                # 1. Detect company name from query
                company_match = re.search(r'in\s+([\w\s]+?)\s+company', user_question.lower())
                company_name = company_match.group(1).strip() if company_match else None
                print("DEBUG: Extracted Company Name:", company_name)

                # 2. Detect category if mentioned (optional)
                category_match = re.search(r'in\s+category\s+([\w\s]+)', user_question.lower())
                category_name = category_match.group(1).strip() if category_match else None
                print("DEBUG: Extracted Category Name:", category_name)

                domain = []

                # 3. Filter by company if detected
                if company_name:
                    company_record = request.env['res.company'].sudo().search([('name', 'ilike', company_name)],
                                                                              limit=1)
                    if company_record:
                        domain.append(('company_id', '=', company_record.id))
                    else:
                        print(f"DEBUG: Company '{company_name}' not found in database")
                        response_message = f"No company found with name '{company_name}'"
                        return Response(json.dumps({'status': 'success', 'message': response_message}),
                                        content_type='application/json')

                # 4. Filter by category if detected
                if category_name:
                    domain.append(('categ_id.name', 'ilike', category_name))

                # 5. Count products
                product_count = request.env['product.template'].sudo().search_count(domain)
                print("DEBUG: Product Count:", product_count)

                # 6. AI summarization
                # response_message = self.summarize_with_ai(
                #     user_question,
                #     {"count": product_count, "category": category_name or "all", "company": company_name or "all"},
                #     context="Product count query"
                # )

                response_message = self.summarize_with_ai(
                    user_question,
                    {"count": product_count, "category": category_name or "all", "company": company_name or "all"},
                    context="Product count query"
                )
                response_message = response_message.replace(
                    f"{product_count} products",
                    f"**{product_count} products**"
                )


                print("DEBUG: Product Count Response:", response_message)




            # --- 3. Product Detail Queries ---
            # --- 3. Product Detail Queries ---
            elif "product detail" in user_question.lower() or re.search(r'\b[A-Z0-9]{6,}\b', user_question.upper()):
                print("DEBUG: Product detail query detected")

                product = None
                sku_code = None

                # --- Try explicit "sku XXXX"
                sku_match = re.search(r'sku\s*([A-Za-z0-9_-]+)', user_question, re.IGNORECASE)
                if sku_match:
                    sku_code = sku_match.group(1).strip()
                    print("DEBUG: Extracted SKU (with keyword):", sku_code)

                # --- If no 'sku', try raw code
                if not sku_code:
                    raw_match = re.search(r'\b([A-Z]+[0-9]+[A-Z0-9]*)\b', user_question.upper())
                    if raw_match:
                        sku_code = raw_match.group(1).strip()
                        print("DEBUG: Extracted SKU (raw):", sku_code)

                # --- Search by SKU
                if sku_code:
                    product = request.env['product.template'].sudo().search([('default_code', '=', sku_code)], limit=1)
                    print("DEBUG: Product search by SKU result:", product.name if product else "None")

                # --- If not found, clean query for name search
                if not product:
                    print("DEBUG: No SKU match, trying name search...")

                    # Try extracting text inside quotes first
                    quoted = re.findall(r'"([^"]+)"', user_question)
                    if quoted:
                        cleaned_query = quoted[0]
                    else:
                        cleaned_query = user_question

                    # Remove numbering like "1.", "2.", "3."
                    cleaned_query = re.sub(r'^\s*\d+\.\s*', '', cleaned_query)

                    # Remove generic phrases
                    cleaned_query = re.sub(r'give me the product detail of', '', cleaned_query, flags=re.IGNORECASE)
                    cleaned_query = re.sub(r'in odoo', '', cleaned_query, flags=re.IGNORECASE)

                    # Final cleanup
                    cleaned_query = cleaned_query.strip(" ?")
                    print("DEBUG: Cleaned query for name search:", cleaned_query)

                    if cleaned_query:
                        # --- FUZZY SEARCH USING difflib ---
                        all_products = request.env['product.template'].sudo().search([])
                        product_names = {p.name: p for p in all_products}
                        best_match = difflib.get_close_matches(cleaned_query, product_names.keys(), n=1, cutoff=0.6)
                        if best_match:
                            product = product_names[best_match[0]]
                            print("DEBUG: Fuzzy matched product:", product.name)
                        else:
                            print("DEBUG: No close match found for product name")

                # --- Final response
                if product:
                    product_data = {
                        "id": product.id,
                        "name": product.name,
                        "sku": product.default_code or "N/A",
                        "price": product.list_price,
                        "category": product.categ_id.name if product.categ_id else "N/A",
                        "company": product.company_id.name if product.company_id else "N/A"
                    }
                    print("DEBUG: Product data prepared for AI summarization:", product_data)

                    response_message = self.summarize_with_ai(
                        user_question,
                        product_data,
                        context="Product detail query"
                    )
                else:
                    # response_message = "No product found for your query."
                    ai_prompt = f"""
                    User Question: "{user_question}"

                    Context: You did not find any matching product in the database.

                    Instructions: Provide a short, polite, human-readable response telling the user that no product was found.
                    Do NOT explain about the database result or empty dictionary.
                    """
                    response_message = self.summarize_with_ai(
                        user_question,
                        raw_data={},  # still pass empty
                        context=ai_prompt
                    )
                    print("DEBUG: AI response for no product found:", response_message)
                    # response_message = self.summarize_with_ai(
                    #     user_question,
                    #     raw_data={},  # empty because no product found
                    #     context="Product detail query: No matching product found"
                    # )
                    print("DEBUG: AI response for no product found:", response_message)
                    print("DEBUG: Product detail query returned no results")





            # --- 3. OdooPIM Queries ---
            elif is_odoopim_related:
                print("DEBUG: OdooPIM related question detected")
                try:
                    # id_match = re.search(r'id=(\d+)', user_question.lower())
                    # Match id=122, id 122, id:122
                    id_match = re.search(r'id\s*[:=]?\s*(\d+)', user_question.lower())
                    id_match = re.search(r'id\s*[:=]?\s*(\d+)', user_question.lower())
                    if id_match:
                        record_id = int(id_match.group(1))
                        print("DEBUG: Extracted Product ID:", record_id)

                        product = request.env['product.template'].sudo().search([('id', '=', record_id)], limit=1)
                        if product:
                            product_data = {
                                "id": product.id,
                                "name": product.name,
                                "sku": product.default_code or "N/A",
                                "price": product.list_price,
                                "category": product.categ_id.name if product.categ_id else "N/A",
                                "company": product.company_id.name if product.company_id else "N/A"
                            }
                            print("DEBUG: Product data prepared for AI summarization:", product_data)
                        else:
                            print("DEBUG: No product found with ID", record_id)
                            product_data = None

                    if id_match:
                        record_id = int(id_match.group(1))
                        print("DEBUG: Extracted Product ID:", record_id)
                        result = request.env['product.template'].sudo().get_sku_by_id(record_id)
                        print("DEBUG: OdooPIM DB Result:", result)

                        if result:
                            # ---------- Case 1: Product Found ----------
                            product_data = {
                                "id": record_id,
                                "name": result.get('product_name'),
                                "sku": result['skus'][0]['sku'] if result.get('skus') else None,
                                "brand": result.get('brand'),
                                "company": result.get('company'),
                                "price": result.get('list_price'),
                                "category": result.get('categ_id')
                            }
                            print("DEBUG: Product Data Prepared:", product_data)
                            ai_prompt = (
                                f"Provide a short one-line summary of this OdooPIM product.\n"
                                f"Only include: Product ID, Name, SKU, and mention missing fields.\n"
                                f"Question: {user_question}\n"
                                f"Product Data: {json.dumps(product_data, indent=2)}"
                            )
                            payload = {"model": ai_model, "messages": [{"role": "user", "content": ai_prompt}],
                                       "stream": False, "temperature": 0.5, "max_tokens": 150, "top_p": 1}
                            print("DEBUG: Sending OdooPIM Payload to AI")

                            response = requests.post(ai_url, headers=headers, json=payload)
                            if response.status_code == 200:
                                response_content = response.json()
                                response_message = response_content['choices'][0]['message'].get('content', '').strip()
                                print("DEBUG: AI Response for OdooPIM:", response_message)
                            else:
                                response_message = f"Product: {result.get('product_name')} | SKU: {result.get('sku')}"
                                print("DEBUG: OdooPIM AI call failed with status:", response.status_code)

                        else:
                            # ---------- Case 2: Product ID but not in DB ----------
                            system_message = "No product found with given ID."
                            ai_prompt = f"Rewrite the following system message in a short, polite response:\n{system_message}"
                            payload = {"model": ai_model, "messages": [{"role": "user", "content": ai_prompt}],
                                       "stream": False, "temperature": 0.5, "max_tokens": 50, "top_p": 1}
                            print("DEBUG: Sending 'Product not found' Payload to AI")

                            try:
                                response = requests.post(ai_url, headers=headers, json=payload)
                                if response.status_code == 200:
                                    response_content = response.json()
                                    response_message = response_content['choices'][0]['message'].get('content',
                                                                                                     '').strip()
                                    if not response_message:
                                        response_message = system_message
                                    print("DEBUG: AI Summarized Response (not found):", response_message)
                                else:
                                    response_message = system_message
                                    print("DEBUG: AI call failed for 'Product not found'")
                            except Exception as e:
                                response_message = system_message
                                print("ERROR in AI summarization (not found):", str(e))

                    else:
                        print("Please specify a product ID using 'id=123' format")
                        # ---------- Case 3: No Product ID ----------
                        system_message = "Please specify a product ID using 'id=123' format"
                        # ai_prompt = f"Rewrite the following system message in a short, polite response:\n{system_message}"
                        # ai_prompt = f"""
                        # You are an assistant for OdooPIM.
                        # Always respond in strict JSON format only.
                        #
                        # If the user did not provide a product ID, return this structure:
                        # {{
                        #   "status": "error",
                        #   "message": "Please specify a product ID using 'id=123' format"
                        # }}
                        # """

                        ai_prompt = f"""
                        You are an AI assistant. 
                        Write a **short, polite, human-readable response** if the user did not provide a product ID. 
                        Do NOT use JSON, code blocks, or technical formatting.

                        Original message: {system_message}
                        """
                        payload = {"model": ai_model, "messages": [{"role": "user", "content": ai_prompt}],
                                   "stream": False, "temperature": 0.5, "max_tokens": 50, "top_p": 1}
                        print("DEBUG: Sending 'No ID found' Payload to AI")

                        try:
                            response = requests.post(ai_url, headers=headers, json=payload)
                            if response.status_code == 200:
                                response_content = response.json()
                                response_message = response_content['choices'][0]['message'].get('content', '').strip()
                                if not response_message:
                                    response_message = system_message
                                print("DEBUG: AI Summarized Response (no ID):", response_message)
                            else:
                                response_message = system_message
                                print("DEBUG: AI call failed for 'No ID found'")
                        except Exception as e:
                            response_message = system_message
                            print("ERROR in AI summarization (no ID):", str(e))

                except Exception as e:
                    print("ERROR in OdooPIM branch:", str(e))
                    return Response(json.dumps({"status": "error", "message": f"Invalid PIM request: {str(e)}"}),
                                    content_type='application/json')


            # --- 4. Completeness Queries ---
            elif is_completeness_related:
                print("DEBUG: Completeness query detected")
                fully = request.env['product.template'].sudo().search_count(
                    [('progress_state', '=', 'fully_completed')])
                almost = request.env['product.template'].sudo().search_count(
                    [('progress_state', '=', 'almost_completed')])
                partially = request.env['product.template'].sudo().search_count(
                    [('progress_state', '=', 'partially_completed')])
                not_completed = request.env['product.template'].sudo().search_count(
                    [('progress_state', '=', 'not_completed')])
                incomplete = request.env['product.template'].sudo().search_count(
                    [('progress_state', '=', 'incomplete')])
                total = request.env['product.template'].sudo().search_count([])
                response_message = f"""Product Completeness Overview:
    • Fully Completed: {fully}
    • Almost Completed: {almost}
    • Partially Completed: {partially}
    • Not Completed: {not_completed}
    • Incomplete: {incomplete}
    • Total Products: {total}"""
                print("DEBUG: Completeness Response:", response_message)

 
    #
            elif is_quality_related:
                print("DEBUG: Quality query detected")
                quality_mapping = {
                    'A': 'fully_completed',
                    'B': 'almost_completed',
                    'C': 'partially_completed',
                    'D': 'not_completed',
                    'E': 'incomplete'
                }

                quality_products = {}
                for letter, state in quality_mapping.items():
                    products = request.env['product.template'].sudo().search([('progress_state', '=', state)])
                    quality_products[letter] = products

                # Prepare data for AI
                ai_data = {}
                for letter, products in quality_products.items():
                    ai_data[letter] = [{"name": p.name, "sku": p.default_code or "N/A"} for p in products]

                ai_summary = self.summarize_with_ai(
                    user_question=f"Summarize all products in Quality levels for the user",
                    raw_data=ai_data,  # <- pass the full list, not just counts
                    context="Product quality report"
                )

                response_message += f"\nAI Summary:\n{ai_summary}"







            # --- 6. Generic AI fallback ---
            else:
                print("DEBUG: Generic AI query detected")
                previous_responses = " ".join(
                    entry['content'] for entry in request.session['conversation_history'] if entry['role'] == "bot")
                combined_query = f"{user_question} Context: {previous_responses}"
                payload = {'model': ai_model, 'messages': [{'role': 'user', 'content': combined_query}],
                           'stream': False, 'temperature': 1, 'max_tokens': 2024, 'top_p': 1}
                print("DEBUG: Sending Generic AI Payload")
                response = requests.post(ai_url, headers=headers, json=payload)
                if response.status_code == 200:
                    response_content = response.json()
                    response_message = response_content['choices'][0]['message'].get('content',
                                                                                     '') if response_content.get(
                        'choices') else "AI returned no content"
                    print("DEBUG: Generic AI Response:", response_message)
                else:
                    response_message = "Error occurred while generating response from AI service"
                    print("DEBUG: Generic AI call failed with status:", response.status_code)

            # --- Append to conversation history ---
            request.session['conversation_history'].append({"role": "bot", "content": response_message})
            if len(request.session['conversation_history']) > 2:
                request.session['conversation_history'].pop(0)
            print("DEBUG: Conversation history updated")

            # --- Build final response ---
            response_data = {
                'status': 'success',
                'message': response_message,
                'conversation_history': request.session['conversation_history']
            }
            print("DEBUG: Final Response:", response_data)
            return Response(json.dumps(response_data), status=200, content_type='application/json')

        except Exception as e:
            print("FATAL ERROR in /groq_api:", str(e))
            return Response(json.dumps({'status': 'error', 'message': str(e)}), status=500,
                            content_type='application/json')







    @http.route('/page_content_data', auth='public', methods=['POST'], csrf=False)
    def page_content_data(self, **kwargs):
        try:
            api_key = request.env['ir.config_parameter'].sudo().get_param('ai_bot_odoopim.ai_bot_odoopim_api_key')
            request_data = json.loads(request.httprequest.data)
            user_question = request_data.get('question', 'No question provided')
            # Ollama API integration
            url = 'https://api.groq.com/openai/v1/chat/completions'
            # url = 'https://ollamaui-openweb.clearancekommerce.com/api/chat/completions'
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}'
            }
            ai_model = request.env['ir.config_parameter'].sudo().get_param('ai_bot_odoopim.ai_bot_odoopim_model')
            payload = {
                # 'model': 'llama3.1:latest',
                'model': f'{ai_model}',
                'messages': [
                    {
                        'role': 'user',
                        'content': user_question
                    }
                ],
                'stream': False,
                'temperature': 1,
                'max_tokens': 2024,
                'top_p': 1,
            }

            # Make the POST request
            response = requests.post(url, headers=headers, json=payload)

            # Handle the response
            if response.status_code == 200:
                response_content = response.json()

            else:
                response_content = "Error occurred while generating response from Ollama"
            # Extract the required fields
            model = response_content.get('model', '')
            content = response_content['choices'][0]['message'].get('content', '') if response_content.get(
                'choices') else ''
            prompt_tokens = response_content['usage'].get('prompt_tokens', 0)
            completion_tokens = response_content['usage'].get('completion_tokens', 0)
            total_tokens = response_content['usage'].get('total_tokens', 0)
            total_time = response_content['usage'].get('total_time', 0)

            print("Page Content Question")
            response_data = {
                'status': 'success',
                'model': model,
                'message': content,
                'prompt_tokens': prompt_tokens,
                'completion_tokens': completion_tokens,
                'total_tokens': total_tokens,
                'total_time': total_time,
                'product_details': 'matched_product_details'
            }

        except Exception as e:
            response_data = {
                'status': 'error',
                'message': str(e)
            }

        # Return a valid HTTP response
        return Response(
            json.dumps(response_data),
            status=200,
            content_type='application/json'
        )






class ApiSettingsModel(models.TransientModel):
    _inherit = 'res.config.settings'

    ai_bot_odoopim_api_key = fields.Char(string='AI Bot API Key')
    ai_bot_odoopim_model = fields.Char(string='AI Bot Model')

    def set_values(self):
        super(ApiSettingsModel, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('ai_bot_odoopim.ai_bot_odoopim_api_key',
                                                         self.ai_bot_odoopim_api_key)
        self.env['ir.config_parameter'].sudo().set_param('ai_bot_odoopim.ai_bot_odoopim_model',
                                                         self.ai_bot_odoopim_model)

    @api.model
    def get_values(self):
        res = super(ApiSettingsModel, self).get_values()
        res['ai_bot_odoopim_api_key'] = self.env['ir.config_parameter'].sudo().get_param(
            'ai_bot_odoopim.ai_bot_odoopim_api_key', default='')
        res['ai_bot_odoopim_model'] = self.env['ir.config_parameter'].sudo().get_param(
            'ai_bot_odoopim.ai_bot_odoopim_model', default='')
        return res
