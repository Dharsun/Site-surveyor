import concurrent.futures
import logging
import urllib.parse
import json
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
from colorama import init, Fore, Style
import os
import smtplib
import subprocess


print(Fore.RED + """                                                                                                                                                                                             
###########################################################
           #-------) Web crawler pro (---------#
                    Code By Dharsun R J 
###########################################################
""")

print(Fore.GREEN + """╔════════════════════════════════════════════════════════════════════════════════════════════════════════════╗""" + Style.RESET_ALL)
print(Fore.YELLOW + """   Output Files : If there is no files, Means crawler doesn't find any output. \n\n""" +
   Fore.LIGHTCYAN_EX + """   crawler.log""" + Style.RESET_ALL + """ = File contains all logs of crawler \n""" +
   Fore.LIGHTCYAN_EX + """   links.txt""" + Style.RESET_ALL + """ = File contains all URL's crawled \n""" +
   Fore.LIGHTCYAN_EX + """   GET_URL.txt""" + Style.RESET_ALL + """ = File contains GET based URL's \n""" +
   Fore.LIGHTCYAN_EX + """   /gf/""" + Style.RESET_ALL + """ = Directory contains GF Outputs \n""" +
   Fore.LIGHTCYAN_EX + """   tree.txt """ + Style.RESET_ALL + """ = File contains all webroot in tree format \n""" +
   Fore.LIGHTCYAN_EX + """   directories.txt """ + Style.RESET_ALL + """ = File contains all found directories \n""" +
   Fore.LIGHTCYAN_EX + """   L1-directories.txt """ + Style.RESET_ALL + """ = File contains only level=1 directories \n""" +
   Fore.LIGHTCYAN_EX + """   Injection-URLS.txt """ + Style.RESET_ALL + """= File contains URLS that consumes UNIQUE user inputs (field + value) \n""" +
   Fore.LIGHTCYAN_EX + """   URL_with_same_input_field.txt """ + Style.RESET_ALL + """= File contains all URLS that consumes user inputs \n""" +
   Fore.LIGHTCYAN_EX + """   js.txt """ + Style.RESET_ALL + """= File contains all analyzed javascript, If JS contains sensitive data will be highlighted as RED \n""" +
   Fore.LIGHTCYAN_EX + """   Detailed-Nuclei-Report.txt""" + Style.RESET_ALL + """ = File contains entire nuclei logs \n""" +
   Fore.LIGHTCYAN_EX + """   Nuclei-results.txt """ + Style.RESET_ALL + """= File contains required nuclei results """)
print(Fore.GREEN + """╚════════════════════════════════════════════════════════════════════════════════════════════════════════════╝
""" + Style.RESET_ALL)

with open('modules.txt', 'r') as f:
    modules = f.readlines()

EXCLUDE_EXTENSIONS = [
    "logout", "Logout", "sign-out", "signout", "sign-off", "sign-off"
]

domains = input(Fore.YELLOW + "Enter Target Domain = " + Style.RESET_ALL)
target_url = input(Fore.YELLOW + "Enter Target-URL = " + Style.RESET_ALL)

proxies = {'http': 'http://127.0.0.1:8080',
           'https': 'https://127.0.0.1:8080'}

fileheader = input(Fore.YELLOW + "Enter File name that contains required headers = " + Style.RESET_ALL)

print()

print("Target domain : " + Fore.RED + domains + Fore.RESET)

print("Target URL : " + Fore.RED + target_url + Fore.RESET)

print("Header file : " + Fore.RED + fileheader + Fore.RESET)

with open(fileheader, 'r') as f:
    data = {}
    for line in f:
        key, value = line.strip().split(': ')
        data[key] = value

json_data = json.dumps(data, indent=4)
headers = json.loads(json_data)

# Create a new directory
match = re.match(r'^https?://([^/]+)', domains)
if match:
    domain_name = match.group(1)
    #print(domain_name)
dirname = ("output_" + domain_name)
os.makedirs(dirname)

# Change to the new directory
os.chdir(dirname)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("crawler.log"),
    ]
)

print()
print(Fore.CYAN + "################################################################################" + Style.RESET_ALL)
print(Fore.YELLOW + "Crawling Started " + Style.RESET_ALL + "..." )
print("Live Outputs will be stored in " + Fore.LIGHTCYAN_EX + dirname + "/links.txt" + Style.RESET_ALL)

class Crawler:
    def __init__(self, base_url, domains=None, exclude_keywords=None, headers=None, timeout=30, max_threads=10, respect_robots=False, proxies=proxies, user_agent=None):
        self.domains = domains
        self.base_url = base_url
        self.exclude_keywords = exclude_keywords
        self.headers = headers
        self.timeout = timeout
        self.max_threads = max_threads
        self.user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"

        self.visited = set()
        self.queue = []
        self.errors = []

        self.session = requests.Session()

        self.session.headers.update({"User-Agent": self.user_agent})
        self._add_to_queue(base_url)

    def _add_to_queue(self, url):
        if url not in self.visited and url not in self.queue:
            self.queue.append(url)

    def start(self):

        logging.info("Starting crawler...")

        while self.queue:
            threads = min(self.max_threads, len(self.queue))
            batch = [self.queue.pop(0) for i in range(threads)]

            with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
                future_to_url = {executor.submit(self._process_link, url): url for url in batch}

                for future in concurrent.futures.as_completed(future_to_url):
                    url = future_to_url[future]
                    try:
                        result = future.result()
                        if result is not None:
                            logging.info(f"{url} crawled successfully with status code {result.status_code}")
                        else:
                            logging.info(f"crawled successfully {url}")
                        fd = open("links.txt", 'a')
                        txt = url + '\n'
                        fd.write(txt)
                        fd.close()

                    except Exception as e:
                        logging.exception(f"Failed to crawl {url}. Reason: {e}")


    def _process_link(self, url):

        if url in self.visited:
            return

        self.visited.add(url)

        try:
            response = self.session.get(url, headers=headers, timeout=self.timeout)
            soup = BeautifulSoup(response.content, "html.parser")

            for link in soup.find_all("a"):
                href = link.get("href")

                if href:
                    try:
                        url_obj = urllib.parse.urlparse(href)
                        if not url_obj.scheme:
                            href = urllib.parse.urljoin(url, href)
                            url_obj = urllib.parse.urlparse(href)
                        if domains not in href:
                            continue
                        if any(ext in href for ext in EXCLUDE_EXTENSIONS):
                            continue
                        href = urllib.parse.urlunparse(url_obj)
                        if href not in self.visited:
                            self._add_to_queue(href)
                    except Exception as e:
                        logging.error(f"Error processing link {href} on {url}: {str(e)}")

        except Exception as e:
            self.errors.append((url, str(e)))
            logging.error(f"{url} failed with error: {str(e)}")
        """
                        Extracts all links from the given URL and adds them to the crawling queue,
                        if they meet certain criteria.
                        """
        for link in soup.find_all("a"):
            href = link.get("href")
            if href:
                try:
                    url_obj = urllib.parse.urlparse(href)
                    if not url_obj.scheme:
                        href = urllib.parse.urljoin(url, href)
                        url_obj = urllib.parse.urlparse(href)
                    if domains not in href:
                        continue
                    if any(ext in href for ext in EXCLUDE_EXTENSIONS):
                        continue
                    href = urllib.parse.urlunparse(url_obj)
                    if href not in self.visited:
                        self._add_to_queue(href)


                except Exception as e:
                    logging.error(f"Error processing link {href} on {url}: {str(e)}")




crawler = Crawler(base_url=target_url)
crawler.start()
print("Live Outputs will be stored in " + Fore.LIGHTCYAN_EX + dirname + "/GET_URL.txt" + Style.RESET_ALL)
print("Live GF Outputs will be stored under " + Fore.LIGHTCYAN_EX + dirname + "/gf/" + Style.RESET_ALL)
# Read the links from a file
with open('links.txt', 'r') as f:
    links = f.readlines()

sdirname = f"gf"
os.makedirs(sdirname, exist_ok=True)
# Change to the new directory
os.chdir(sdirname)
# Strip the newline character from each link
links = [link.strip() for link in links]

# Strip the newline character from each module
modules = [module.strip() for module in modules]

# Iterate over each module and run the command
for module in modules:
    command = ['gf', module]

    # Run the command and capture the output
    output = subprocess.check_output(command, input='\n'.join(links), text=True)

    # Write the output to a file if the output is not empty
    if output.strip():
        with open(f"{module}.txt", 'w') as f:
            f.write(output)

os.chdir('..')

# current working directory is '/home/user'
print(Fore.GREEN + "Crawling completed" + Style.RESET_ALL)
print(Fore.CYAN + "################################################################################" + Style.RESET_ALL)

#crawling ends

with open("links.txt", "r") as f:
    urls = [url.strip() for url in f]
for url in urls:
    if "?" in url or "=" in url:
        fd = open("GET_URL.txt", 'a')
        txt = url + '\n'
        fd.write(txt)
        fd.close()

print(Fore.YELLOW + "Initializing Tree " + Style.RESET_ALL + "...")
print("Live Outputs will be stored in " + Fore.LIGHTCYAN_EX + dirname + "/tree.txt" + Style.RESET_ALL)


def generate_tree(root, urls):
    # create dictionary to hold tree structure
    tree = {}

    # iterate over URLs
    for url in urls:
        # remove root URL from the beginning of the URL
        path = url.replace('https://' + root, '').strip('/')

        # split path into parts
        parts = path.split('/')

        # initialize current node to tree root
        current_node = tree

        # iterate over parts of path
        for i, part in enumerate(parts):
            # check if current part of path is already in tree
            if part not in current_node:
                # add part to tree
                current_node[part] = {}

            # update current node to the child node
            current_node = current_node[part]

            # add full URL to current node if it's the last part of the path
            if i == len(parts) - 1:
                current_node['__url__'] = url

    return tree

def print_tree(tree, level=0, file=None):
    # get list of keys in tree
    keys = list(tree.keys())

    # sort keys alphabetically
    keys.sort()

    # iterate over keys
    for key in keys:

        print('    ' * level, end='', file=file)
        if key == '__url__':
            print(Fore.WHITE + tree[key], file=file)
        else:
            print(Fore.RED + '├──', Fore.GREEN + key, file=file)
        if key != '__url__':
            print_tree(tree[key], level=level+1, file=file)

with open('links.txt', 'r') as f:
    urls = [url.strip() for url in f if url.strip()]

if not urls:
    print('No URLs found in file.')
else:
    root = urls[0].split('/')[2]
    tree = generate_tree(root, urls)

    with open('tree.txt', 'w') as outfile:
        print_tree(tree, file=outfile)

print(Fore.GREEN + "Tree Conversion Completed" + Style.RESET_ALL)
print(Fore.CYAN + "################################################################################" + Style.RESET_ALL)
print(Fore.YELLOW + "Initializing Directories " + Style.RESET_ALL + "...")
print("Live Outputs will be stored in " + Fore.LIGHTCYAN_EX + dirname + "/directories.txt" + Style.RESET_ALL)



with open('links.txt', 'r') as f:
    urls = f.readlines()

directory_regex = r'https?://(?:www\.)?(.+?)/(.*/)'
printed_directories = set()
for url in urls:
    url = url.strip()
    directory_match = re.match(directory_regex, url)
    if directory_match:
        directory = directory_match.group(2)
        if directory not in printed_directories:
            printed_directories.add(directory)
            fd = open("directories.txt", 'a')
            txt = directory + '\n'
            fd.write(txt)
            fd.close()

print("Live Outputs will be stored in " + Fore.LIGHTCYAN_EX + dirname + "/L1-directories.txt" + Style.RESET_ALL)

with open('directories.txt', 'r') as f:
    urls = f.readlines()

directory_regex = r'(\w+?)/'
printed_directories = set()
for url in urls:
    url = url.strip()
    match = re.match(directory_regex, url)
    if match:
        directory = match.group(1)
        if directory not in printed_directories:
            printed_directories.add(directory)
            fd = open("L1-directories.txt", 'a')
            txt = directory + '\n'
            fd.write(txt)
            fd.close()

print(Fore.GREEN + "Directories Completed" + Style.RESET_ALL)
print(Fore.CYAN + "################################################################################" + Style.RESET_ALL)
print(Fore.YELLOW + "Analyzing URLS for Injection attack " + Style.RESET_ALL + "...")
print("Live Outputs will be stored in " + Fore.LIGHTCYAN_EX + dirname + "/Injection-URLS.txt" + Style.RESET_ALL)
print("Live Outputs will be stored in " + Fore.LIGHTCYAN_EX + dirname + "/URL_with_same_input_field.txt" + Style.RESET_ALL)

input_regexes = [
    r".*\[.*\].*",  # square bracket notation, e.g. "input[name='user[email]']"
    r"^.*_.*$",  # underscore notation, e.g. "input[name='user_email']"
    r"^.*\-.+$",  # dash notation, e.g. "input[name='user-email']"
]

processed_inputs = set()  # Set to store all processed input fields across URLs


# Identify user input fields on the given web page URL
def identify_user_inputs(url):
    global processed_inputs

    try:
        # Use requests library to retrieve the web page content
        response = requests.get(url, headers=headers)
        html = response.content
    except:
        return

    # Use BeautifulSoup to parse the HTML content and find input fields
    soup = BeautifulSoup(html, 'html.parser')
    input_tags = soup.find_all(['input', 'textarea', 'select'])
    input_fields = set()  # Use a set to avoid duplicates

    for tag in input_tags:
        # Check for standard attribute names
        if tag.has_attr('name') or tag.has_attr('id'):
            input_fields.add(tag.get('name') or tag.get('id'))

        # Check for non-standard attribute names using regular expressions
        for regex in input_regexes:
            if any([re.match(regex, attr) for attr in tag.attrs]):
                input_fields.add(tag.get('name') or tag.get('id'))

    # Remove inputs that are already processed
    new_inputs = set()
    for field in input_fields:
        if not field or field not in processed_inputs:
            new_inputs.add(field)

    # Check if all input fields are already processed
    if not new_inputs:
        fd = open("URL_with_same_input_field.txt", 'a')
        txt = url + '\n'
        fd.write(txt)
        fd.close()
        return

    # Add new input fields to processed_inputs set
    processed_inputs.update(new_inputs)

    # Write URL and input fields to file
    with open("Injection-URLS.txt", "a") as f:
        f.write(Fore.CYAN + "####################################################\n" + Style.RESET_ALL)
        f.write(Fore.GREEN + f"{url}\n" + Style.RESET_ALL)
        for field in new_inputs:
            value = soup.find('input', {'name': field}) or soup.find('textarea', {'name': field}) or soup.find('select',
                                                                                                               {
                                                                                                                   'name': field})
            value = value.get('value') if value else None
            if not field:
                f.write(Fore.RED + f" input: {field}\n" + Style.RESET_ALL)
            else:
                f.write(f" input: {field}\n")



# Read URLs from input file and process them
with open("links.txt", "r") as f:
    urls = [url.strip() for url in f]

with concurrent.futures.ThreadPoolExecutor() as executor:
    executor.map(identify_user_inputs, urls)

print(Fore.GREEN + "Analyzing URLs for Injection Completed" + Style.RESET_ALL)
print(Fore.CYAN + "################################################################################" + Style.RESET_ALL)
print(Fore.YELLOW + "Analyzing JS files for sensitive data " + Style.RESET_ALL + "...")
print("Live Outputs will be stored in " + Fore.LIGHTCYAN_EX + dirname + "/js.txt" + Style.RESET_ALL)



def get_js_links(url):
    """
    Returns a list of all JavaScript file links on the given website.
    """
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    links = soup.find_all('script')

    js_links = []
    for link in links:
        href = link.get('src')
        if href and '.js' in href:
            js_links.append(href)

    return js_links

def print_js_url(url, js_link):
    """
    Prints the complete URL of the given JavaScript file link.
    """
    js_url = urljoin(url, js_link)
    if js_url.startswith(domains):
        #print(js_url, flush=True)

        regex = r"""(?i)(access_key|accessKeyId|accessKeySecret|access_token|admin_pass|admin_user|algolia_admin_key|algolia_api_key|alias_pass|
                    alicloud_access_key|amazon_secret_access_key|amazonaws|ansible_vault_password|aos_key|api_key|api_key_secret|api_key_sid|
                    api_secret|api.googlemaps AIza|apidocs|apikey|apiSecret|app_debug|app_id|app_key|app_log_level|app_secret|appkey|
                    appkeysecret|application_key|appsecret|appspot|auth_token|authorizationToken|authsecret|aws_access|aws_access_key_id|
                    aws_bucket|aws_key|aws_secret|aws_secret_key|aws_token|AWSSecretKey|b2_app_key|bashrc password|bintray_apikey|
                    bintray_gpg_password|bintray_key|bintraykey|bluemix_api_key|bluemix_pass|browserstack_access_key|bucket_password|
                    bucketeer_aws_access_key_id|bucketeer_aws_secret_access_key|built_branch_deploy_key|bx_password|cache_driver|
                    cache_s3_secret_key|cattle_access_key|cattle_secret_key|certificate_password|ci_deploy_password|client_secret|
                    client_zpk_secret_key|clojars_password|cloud_api_key|cloud_watch_aws_access_key|cloudant_password|cloudflare_api_key|
                    cloudflare_auth_key|cloudinary_api_secret|cloudinary_name|codecov_token|config|conn.login|connectionstring|
                    consumer_key|consumer_secret|credentials|cypress_record_key|database_password|database_schema_test|
                    datadog_api_key|datadog_app_key|db_password|db_server|db_username|dbpasswd|dbpassword|dbuser|deploy_password|
                    digitalocean_ssh_key_body|digitalocean_ssh_key_ids|docker_hub_password|docker_key|docker_pass|docker_passwd|
                    docker_password|dockerhub_password|dockerhubpassword|dot-files|dotfiles|droplet_travis_password|dynamoaccesskeyid|
                    dynamosecretaccesskey|elastica_host|elastica_port|elasticsearch_password|encryption_key|encryption_password|
                    env.heroku_api_key|env.sonatype_password|eureka.awssecretkey)['" ]+(=|:)"""

        try:
            response = requests.get(js_url, headers=headers)
            file_contents = response.text
            matches = re.findall(regex, file_contents)
            js = open("js.txt", 'a')
            if matches:
                js.write(Fore.RED + f"Sensitive information found in {js_url}:\n + Style.RESET_ALL")
                js.write(str(matches) + "\n")
            else:
                js.write(f"No sensitive information found in {js_url}\n")
        except requests.exceptions.RequestException as e:
            js.write(f"Error accessing {js_url}: {e}\n")

# Read input URLs from file
with open('links.txt', 'r') as f:
    urls = f.read().splitlines()

# Crawl all URLs and print JavaScript links
printed_links = set()
with concurrent.futures.ThreadPoolExecutor() as executor:
    futures = [executor.submit(get_js_links, url) for url in urls]
    for i, future in enumerate(concurrent.futures.as_completed(futures)):
        url = urls[i]
        js_links = future.result()
        for link in js_links:
            if link not in printed_links:
                print_js_url(url, link)
                printed_links.add(link)

print(Fore.GREEN + "Analyzing JS files Completed" + Style.RESET_ALL)
print(Fore.CYAN + "################################################################################" + Style.RESET_ALL)
os.chdir('..')
print(Fore.YELLOW + "Initiating Nuclei Scanning..." + Style.RESET_ALL)

filepath = dirname + "/" + "links.txt"
Targets = filepath
headers = fileheader
cmd = f"nuclei -H {headers} -l " + Targets + " -t nuclei-templates -silent"

ND = "Nuclei"
nupath = os.path.join(dirname, ND)
os.makedirs(nupath)
print("Live Outputs will be stored in " + Fore.LIGHTCYAN_EX + nupath + Style.RESET_ALL)
file_path1 = os.path.join(dirname, ND, "Detailed-Nuclei-Report.txt")
file_path2 = os.path.join(dirname, ND, ".tmp-Nuclei-results.txt")
file_path3 = os.path.join(dirname, ND, "Nuclei-results.txt")

with subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=1, universal_newlines=True, shell=True) as p:
    for line in p.stdout:
        fd = open(file_path1, 'a')
        txt = line + '\n'
        fd.write(txt)
        fd.close()
        severities = ['critical', 'high', 'medium']
        printed_lines = set()
        with open(file_path1) as f:
            for line in f:
                if any(severity in line for severity in severities) and line not in printed_lines:
                    printed_lines.add(line)
                    fd = open(file_path2, 'a')
                    txt = line + '\n'
                    fd.write(txt)
                    fd.close()
                    with open(file_path2, 'r') as input_file:
                        lines = input_file.readlines()
                    lines = set(lines)
                    with open(file_path3, 'w') as output_file:
                        output_file.writelines(lines)

print(Fore.GREEN + "Nuclei Scan Completed..." + Style.RESET_ALL)
print(Fore.CYAN + "################################################################################" + Style.RESET_ALL)



sender_email = "ddrish43@gmail.com"
receiver_email = "youcanttextme@gmail.com"
password = "sxdawwkugzpddpsv"
message = """\
Subject: Hi there

Web crawler pro has completed on """ + """domain = """ + domains

with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
    server.login(sender_email, password)
    server.sendmail(sender_email, receiver_email, message)
