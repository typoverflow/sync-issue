import requests
import pathlib
import json
from dateutil import parser
from requests.api import patch
import os

GH_TOKEN = os.environ.get("GH_TOKEN", "")
root = pathlib.Path(__file__).parent.resolve()
# client = GraphqlClient(endpoint="https://api.github.com/graphql")

def fetch_gitlab_issues(url, headers=None, params=None, focused=None):
    r = requests.get(url, headers=headers, params=params)
    assert r.status_code == 200
    issues = json.loads(r.text)
    if len(issues) == 0:
        return []
    if focused is None:
        focused = issues[0].keys()

    issues = [{key:value for (key, value) in issue.items() if key in focused} for issue in issues] 
    return issues

def post_github_issues(url, new_issues, mapping):
    headers = {'Authorization': 'token {}'.format(GH_TOKEN)}
    session = requests.session()
    r = session.get(url, headers=headers)
    assert r.status_code == 200
    old_issues = json.loads(r.text)

    for new_issue in new_issues:
        flag = True
        for old_issue in old_issues:
            if old_issue["title"] == new_issue["title"]:
                if parser.parse(old_issue["updated_at"]) < parser.parse(new_issue["updated_at"]):
                    patch_dict = {mapping[key]:value for (key, value) in new_issue.items() if key in mapping.keys()}
                    r = session.patch(url+"/{}".format(old_issue["number"]), json.dumps(patch_dict), headers=headers)
                    assert r.status_code == 200
                flag = False
        if flag: 
            post_dict = {mapping[key]:value for (key, value) in new_issue.items() if key in mapping.keys()}
            r = session.post(url, json.dumps(post_dict), headers=headers)
            assert r.status_code == 201



if __name__ == "__main__":
    mapping = {
        "title": "title", 
        "description": "body", 
        "labels": "labels"
    }
    url = "https://git.nju.edu.cn/api/v4/projects/2412/issues"
    new_issues = fetch_gitlab_issues(url, focused=["title", "description", "created_at", "updated_at", "labels"])
    post_github_issues('https://api.github.com/repos/typoverflow/issue-sync/issues', new_issues, mapping)
