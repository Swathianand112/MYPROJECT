import pandas as pd
import requests
from bs4 import BeautifulSoup
from django.shortcuts import render
from urllib.parse import urlparse, parse_qs

def upload_and_compare(request):
    if request.method == 'POST':
        crf_file = request.FILES.get('crf_file')
        crf_url = request.POST.get('crf_url')
        email_file = request.FILES.get('email_file')
        email_url = request.POST.get('email_url')

        if (crf_file or crf_url) and (email_file or email_url):
            try:
                # Read CRF data
                if crf_file:
                    crf_data = pd.read_csv(crf_file)
                elif crf_url:
                    response = requests.get(crf_url)
                    crf_data = pd.read_csv(pd.compat.StringIO(response.text))

                # Read Email data
                if email_file:
                    email_html = email_file.read().decode('utf-8')
                elif email_url:
                    response = requests.get(email_url)
                    email_html = response.text

                soup = BeautifulSoup(email_html, 'html.parser')
                email_urls = {}
                email_contents = {}

                # Extract URLs, Titles, and Contents from HTML
                for a_tag in soup.find_all('a', href=True):
                    target_id = a_tag.get('data-crmqa-target-id', '')
                    url = a_tag.get('href', '')
                    title = a_tag.get('title', '').strip().lower()
                    target_blank = a_tag.get('target', '') == '_blank'
                    email_urls[target_id] = {'url': url, 'title': title, 'target_blank': target_blank}
                    
                    # Extract content based on tag type
                    if a_tag.find('img'):
                        email_contents[target_id] = f'<img src="{a_tag.find("img").get("src")}" alt="Logo" class="content-img">'
                    elif a_tag.get_text(strip=True):
                        email_contents[target_id] = a_tag.get_text(strip=True)
                    else:
                        email_contents[target_id] = title or 'No content'

                results = []
                campaign_name = None

                for _, row in crf_data.iterrows():
                    target_id = row.get('Target_id', '')
                    final_url = row.get('Final_URL', '')
                    crf_title = row.get('Title', '').strip().lower() if 'Title' in row else ''
                    crf_utm_params = row.get('UTM_Parameters', '')
                    email_info = email_urls.get(target_id, {})
                    email_url = email_info.get('url', '')
                    email_title = email_info.get('title', '')
                    email_content = email_contents.get(target_id, '')
                    final_url_target_blank = email_info.get('target_blank', False)
                    title_match_icon = 'times'

                    if crf_title and crf_title == email_title:
                        title_match_icon = 'check'

                    if email_url:
                        try:
                            response = requests.get(email_url, allow_redirects=True)
                            redirected_url = response.url

                            # Extract campaign name from the UTM parameters
                            if not campaign_name:
                                parsed_final_url = urlparse(final_url)
                                campaign_name = parsed_final_url.path.split('/')[-1]

                            # Compare Root URL
                            parsed_final_url = urlparse(final_url)
                            parsed_redirected_url = urlparse(redirected_url)
                            root_final_url = f'{parsed_final_url.scheme}://{parsed_final_url.netloc}'
                            root_redirected_url = f'{parsed_redirected_url.scheme}://{parsed_redirected_url.netloc}'

                            # Color the root URL
                            colored_url = f'<span style="color:{"green" if root_final_url == root_redirected_url else "red"};">{root_redirected_url}</span>'

                            # Extract and Compare UTM Parameters
                            crf_query_params = parse_qs(parsed_final_url.query)
                            redirected_query_params = parse_qs(parsed_redirected_url.query)

                            crf_utm_params_dict = {param: value[0] for param, value in crf_query_params.items() if param.startswith('utm_')}
                            redirected_utm_params_dict = {param: value[0] for param, value in redirected_query_params.items() if param.startswith('utm_')}

                            # Build UTM parameters display
                            param_display = []
                            for param, crf_value in crf_utm_params_dict.items():
                                redirected_value = redirected_utm_params_dict.get(param, None)
                                if redirected_value and crf_value == redirected_value:
                                    param_display.append(f'<span style="color:green;">{param}=<span style="color:lightgreen;">{crf_value}</span></span>')
                                else:
                                    param_display.append(f'<span style="color:red;">{param}=<span style="color:lightred;">{crf_value}</span></span>')

                            if crf_utm_params_dict:
                                params_str = f'?{"&".join(param_display)}'
                                colored_url += params_str

                            # Platform Appended Values
                            extra_params = {param: redirected_query_params[param][0] for param in redirected_query_params if param not in crf_utm_params_dict}
                            if extra_params:
                                extra_str = '&'.join([f'{param}={value}' for param, value in extra_params.items()])
                                colored_url += f'<span style="color:lightblue;">&{extra_str}</span>'

                            target_blank_icon = '<i class="fas fa-external-link-alt icon icon-green"></i>' if final_url_target_blank else ''

                            results.append({
                                'target_id': target_id,
                                'content': email_content,
                                'title_match_icon': title_match_icon,
                                'final_url': colored_url + target_blank_icon,
                                'final_url_target_blank': final_url_target_blank,
                            })
                        except Exception as e:
                            results.append({
                                'target_id': target_id,
                                'content': 'Error accessing URL',
                                'title_match_icon': 'times',
                                'final_url': f'<span style="color:red;">Error accessing URL</span>',
                                'final_url_target_blank': final_url_target_blank,
                            })

            except Exception as e:
                return render(request, 'upload_and_compare.html', {'error': 'Error processing files.'})

            return render(request, 'upload_and_compare.html', {'results': results, 'campaign_name': campaign_name})

        else:
            return render(request, 'upload_and_compare.html', {'error': 'Please upload both files or provide valid URLs.'})

    return render(request, 'upload_and_compare.html')
