import subprocess
from .models import *
from googlesearch import search
from urllib.parse import urlparse
from celery import shared_task
from celery.contrib.abortable import AbortableTask
import re
from collections import defaultdict
import json


@shared_task(base=AbortableTask)
def get_deepdive(user_id):
    # Query user
    print("Searching . . .")
    user = User.query.filter_by(platform_id=user_id).first()

    query = user.firstname + " " + user.lastname
    google_final, found_usernames = google_results(query)

    found_usernames["name"] = [user.firstname + user.lastname]
    found_usernames["nameDot"] = [(user.firstname + user.lastname).lower()]
    found_usernames["nameShortened"] = [user.firstname[0] + user.lastname]
    found_usernames["nameShortenedDot"] = [user.firstname[0] + "-" + user.lastname]

    print(found_usernames)

    if user.type == 'linkedin':
        # check headline
        print("Checking LinkedIn User. . .")
        headline = user.headline
        print(headline)
        pattern = r"(?:@|at)\s*([A-Za-z]+(?:\s+[A-Za-z]+)*)"
        matches = re.findall(pattern, headline)
        print(matches)
        if matches:
            for match in matches:
                linkedin_query = query + " " + match
                linked_in_search_result, usernames_linkedin_result = google_results(linkedin_query)
                google_final.extend(linked_in_search_result)

    #remove duplicates
    google_final = list(set(google_final))

    social_media_links = {
        'twitter': [],
        'linkedin': [],
        'reddit': [],
        'facebook': [],
        'instagram': [],
        'tiktok': [],
        'other': []  # For links that don't match the above categories
    }

    # Categorize Google search results
    for link in google_final:
        parsed_url = urlparse(link)
        hostname = parsed_url.hostname

        if 'twitter.com' in hostname:
            social_media_links['twitter'].append(link)
        elif 'linkedin.com' in hostname:
            social_media_links['linkedin'].append(link)
        elif 'reddit.com' in hostname:
            social_media_links['reddit'].append(link)
        elif 'facebook.com' in hostname:
            social_media_links['facebook'].append(link)
        elif 'instagram.com' in hostname:
            social_media_links['instagram'].append(link)
        elif 'tiktok.com' in hostname:
            social_media_links['tiktok'].append(link)
        else:
            social_media_links['other'].append(link)

    twitter_links = json.dumps(social_media_links.get('twitter', []))
    linkedin_links = json.dumps(social_media_links.get('linkedin', []))
    reddit_links = json.dumps(social_media_links.get('reddit', []))
    facebook_links = json.dumps(social_media_links.get('facebook', []))
    instagram_links = json.dumps(social_media_links.get('instagram', []))
    tiktok_links = json.dumps(social_media_links.get('tiktok', []))
    other_links = json.dumps(social_media_links.get('other', []))

    possible_accounts = None
    # finds possible accounts on other platforms based on initial google results
    if any(found_usernames.values()):
        print("RUNNING SHERLOCK")
        possible_accounts = run_sherlock(found_usernames)

    print(possible_accounts)

    serialized_possible_accounts = json.dumps(possible_accounts)

    # Create new DeepdiveResult record
    deepdive_result = DeepdiveResult(
        user_id=user_id,
        twitter_links=twitter_links,
        linkedin_links=linkedin_links,
        reddit_links=reddit_links,
        facebook_links=facebook_links,
        instagram_links=instagram_links,
        tiktok_links=tiktok_links,
        other_links=other_links,
        possible_accounts=serialized_possible_accounts
    )

    # Save to database
    db.session.add(deepdive_result)
    db.session.commit()


def run_sherlock(given_usernames):
    cmd = ["/usr/local/bin/python3", "/usr/src/app/project/sherlock/sherlock/sherlock.py"]
    for usernames in given_usernames.values():
        cmd.extend(usernames)

    result = subprocess.run(cmd, capture_output=True, text=True, cwd="/usr/src/app/project/sherlock/sherlock")
    if result.returncode != 0:
        raise Exception(result.stderr)

    # Use a regex to capture each username section
    username_sections = re.findall(r'\[\*\] Checking username (\w+) on:(.+?)(?=\[\*\] Checking username|\Z)',
                                   result.stdout, re.DOTALL)

    processed_results = {}
    for username, section in username_sections:
        # Split the section into individual entries based on '[+]'
        entries = section.strip().split('\n[+] ')
        # Skip the first entry which is just the header
        entries = entries[1:] if len(entries) > 1 else []

        # Extract URLs
        urls = [re.match(r'([^:]+): (https?://\S+)', entry).groups() for entry in entries]

        processed_results[username] = {site.strip(): url for site, url in urls}

    return processed_results


def google_results(query):
    # google name and store results
    terms_to_look_for = ["Instagram", "Twitter", "Reddit", "GitHub", "Facebook", "LinkedIn", "TikTok", "YouTube"]
    g_results = []  # store all found urls
    results_terms = []  # store only urls with terms of interest
    for url in search(query, num_results=20):
        for term in terms_to_look_for:
            if term.lower() in url.lower():
                results_terms.append((term, url))
        g_results.append(url)
    # look for usernames from those services
    print(g_results)
    g_usernames = defaultdict(list)
    for term, url in results_terms:
        parsed = urlparse(url)
        path_components = parsed.path.strip('/').split('/')
        username = None
        # Conditions for different platforms
        if 'reddit.com' in parsed.netloc:
            username = path_components[1] if len(path_components) > 1 else None
        elif 'github.com' in parsed.netloc:
            username = path_components[0]
        elif 'facebook.com' in parsed.netloc:
            username = path_components[0]
        elif 'linkedin.com' in parsed.netloc:
            if 'in' in path_components:
                username_index = path_components.index('in') + 1
                if username_index < len(path_components):
                    username = path_components[username_index]
        elif 'tiktok.com' in parsed.netloc:
            username = path_components[0].lstrip('@')
        elif 'youtube.com' in parsed.netloc:
            username = path_components[0].lstrip('@')

        if username is not None and username not in g_usernames[term]:
            print("FOUND: " + username)
            g_usernames[term].append(username)

    return g_results, g_usernames

# class CustomPDF(FPDF):
#     def header(self):
#         self.set_font('Arial', 'B', 12)
#         self.cell(0, 10, 'User Information', 0, 1, 'L')
#
#     def add_user_data(self, final_results, descriptions):
#         self.set_font('Arial', '', 10)
#         for key, value in final_results.items():
#             self.set_font('Arial', 'B', 12)
#             self.cell(0, 10, key.title(), 0, 1)
#             self.set_font('Arial', '', 10)
#             desc = descriptions.get(key, "No description available.")
#             self.multi_cell(0, 10, desc)
#             self.ln(2)
#
#             if isinstance(value, dict):
#                 for service, username in value.items():
#                     line = f"{service}: {username}"
#                     self.multi_cell(0, 10, line)
#             elif isinstance(value, list):
#                 for item in value:
#                     self.multi_cell(0, 10, str(item))
#             else:
#                 self.multi_cell(0, 10, str(value))
#             self.ln(5)
#
#
# def create_pdf_fpdf(final_results: dict, descriptions: dict, filename: str) -> str:
#     print("Creating PDF...hzzzzzzzzzzzzzjhnjjjjjjjjjjjjjjjj")  # cat
#     pdf = CustomPDF()
#     pdf.add_page()
#     pdf.add_user_data(final_results, descriptions)
#     pdf.output(filename)
#     return filename
