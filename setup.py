import requests
import lxml.etree as et
import sys

# Config
JENKINS_ENDPOINT = "http://10.90.54.156:8080"
JENKINS_WEBHOOK_URL = f"{JENKINS_ENDPOINT}/github-webhook/"
GIT_ENDPOINT = f"https://wwwin-github.cisco.com/api/v3"

def translate_groovy(filename):
    results = {}
    with open('app.param', 'r') as f:
        for line in f.readlines():
            index = line.index('=')
            variable_name = line[:index].strip()
            variable_value = line[index+1:].strip()
            results[variable_name] = variable_value
            
    with open(filename, "r") as f:
        i = 0
        for line in f.readlines():
            i += 1
            if i > 9 and '=' in line:
                index = line.index('=')
                variable_name = line[:index].strip()
                variable_value = line[index+1:].strip()[1:-1]

                if '${' in variable_value:
                    index = variable_value.index('${')
                    end_index = variable_value.index('}')
                    to_resolve = variable_value[index+len('${VARMAP[')+1:end_index-2].strip()
                    resolution = results.get(to_resolve)
                    variable_value = variable_value.replace(variable_value[index:end_index+1], resolution)

                results[variable_name] = variable_value

    return results

def create_repo(context):
    print(f"Creating repo for {context['APP_NAME']}...")

    headers = {
        "Accept": "application/vnd.github.v3+json",
    }

    # Get repositories
    repos = requests.get(f"{GIT_ENDPOINT}/user/repos", auth=(context['CEC_ID'], context['GIT_TOKEN']), headers=headers)

    # Stop if repository already exists
    for repo in repos.json():
        if repo["name"] == context['APP_NAME']:
            print("Repository for this project already exists.")
            return

    # Create repository
    repo_data = {
        "name" : context['APP_NAME'],
        "description" : "Auto-generated repository",
        "private" : True
    }
    resp = requests.post(url=f"{GIT_ENDPOINT}/user/repos", auth=(context['CEC_ID'], context['GIT_TOKEN']), headers=headers, json=repo_data)
    resp.raise_for_status()
    print("Succesfully created repository")

def post_webhook(url, context):
    print(f"Creating webhook for {url}...")

    headers = {
        "Accept": "application/vnd.github.v3+json",
    }

    # Get webhooks
    hooks = requests.get(f"{GIT_ENDPOINT}/repos/{context['CEC_ID']}/{context['APP_NAME']}/hooks", auth=(context['CEC_ID'], context['GIT_TOKEN']), headers=headers)

    # Delete if URL already hooked
    for hook in hooks.json():
        if hook["config"]["url"] == url:
            resp = requests.delete(f"{GIT_ENDPOINT}/repos/{context['CEC_ID']}/{context['APP_NAME']}/hooks/{hook['id']}", auth=(context['CEC_ID'], context['GIT_TOKEN']), headers=headers)
            resp.raise_for_status()
            print("Webhook for this URL already exists. Deleting...")

    # Create webhook
    webhook_data = {
        "name" : "web",
        "config" : {
            "url" : url,
            "content_type" : "json"
        }
    }
    resp = requests.post(url=f"{GIT_ENDPOINT}/repos/{context['CEC_ID']}/{context['APP_NAME']}/hooks", auth=(context['CEC_ID'], context['GIT_TOKEN']), headers=headers, json=webhook_data)
    resp.raise_for_status()
    print("Succesfully created webhook")

def post_pipeline(context):
    print(f"Creating pipeline for {context['APP_NAME']}...")

    headers = {
        "Accept": "application/json",
    }

    # Get jobs
    print(requests.get(f"{JENKINS_ENDPOINT}/api/json", auth=("gve_devnet", context['JENKINS_TOKEN']), headers=headers).json())
    jobs = requests.get(f"{JENKINS_ENDPOINT}/api/json", auth=("gve_devnet", context['JENKINS_TOKEN']), headers=headers).json()['jobs']

    # Delete if URL already hooked
    for job in jobs:
        if job["name"] == context['APP_NAME']:
            print("Pipeline for this project name already exists.")
            return
    
    # Fill out pipeline config
    tree = et.parse('jenkins.xml')
    branch = tree.xpath('//jenkins.branch.BranchSource')[0]
    branch.xpath('//credentialsId')[0].text = 'stienvan-github'
    branch.xpath('//repoOwner')[0].text = context['CEC_ID']
    branch.xpath('//repository')[0].text = context['APP_NAME']
    branch.xpath('//repositoryUrl')[0].text = f"https://wwwin-github.cisco.com/stienvan/gve_devnet_meraki_ssid_dashboard.git"
    tree.write("jenkins.xml")

    # Create job
    headers = {
        "Content-Type" : "text/xml"
    }
    resp = requests.post(f"{JENKINS_ENDPOINT}/createItem?name={context['APP_NAME']}", auth=("gve_devnet", context['JENKINS_TOKEN']), headers=headers, data=et.tostring(et.parse('jenkins.xml')))
    resp.raise_for_status()
    print("Succesfully created Jenkins pipeline")

if __name__ == "__main__":
    context = translate_groovy("app.groovy")
    if len(sys.argv) == 2 and (sys.argv[1] == "-h" or sys.argv[1] == "--help"):
        print("""
        Hi there! This script sets up the necessary webhooks for the GVE Devnet App Template CI/CD pipeline.

        Usage: python3 setup.py [OPTIONS]

        Available options:
        github      Sets up Github webhook for Jenkins trigger on code push
        jenkins     Sets up Jenkins pipeline
        """)

    for a in sys.argv[1:]:
        if a == "github":
            post_webhook(JENKINS_WEBHOOK_URL, context) # Replaces webhook if it already exists
        elif a == "jenkins":
            post_pipeline(context) # Does not do anything if pipeline already exists
        else:
            print(f'Did not recognize argument "{a}". Use option -h or --h to see valid arguments')
        
    # create_repo(context) # Does not do anything if repo already exists
    # post_webhook(JENKINS_WEBHOOK_URL, context) # Replaces webhook if it already exists
    # post_pipeline(context) # Does not do anything if pipeline already exists
