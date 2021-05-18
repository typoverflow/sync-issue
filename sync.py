from sre_constants import REPEAT_ONE
import requests
import pathlib
import json
from dateutil import parser
from requests.api import patch
import os
import re
import copy

GH_TOKEN = os.environ.get("GH_TOKEN", "")
root = pathlib.Path(__file__).parent.resolve()

class Issue(object):
    img_url_pattern = {
        "gitlab": r"!\[image\]\((/uploads/.*/image\..{3,4})\)", 
        "github": None, 
        "gitee": None,
    }

    def __init__(self, type, data, repo_url):
        if type == "gitlab":
            data["body"] = data.get("description", "")

        self.type = type
        self.raw_data = data
        self.repo_url = repo_url

        self.title = data.get("title", "")
        self.labels = data.get("labels", "")
        self.created_at = data.get("created_at", "")
        self.updated_at = data.get("updated_at", "")
        self.body = data.get("body", "")
        self.resources = re.findall(Issue.img_url_pattern[self.type], self.body)

    def download_resources(self, img_dir: pathlib.Path):
        if not img_dir.exists():
            img_dir.mkdir()
        for suffix in self.resources:
            r = requests.get(self.repo_url+suffix)
            img_path = img_dir / suffix
            if img_path.exists() and img_path.is_file():
                continue
            with open(img_path, "wb") as fp:
                for chunk in r.iter_content(chunk_size=64):
                    fp.write(chunk)

    def convert_url(self):
        """
        由于github和gitlab对于处理issue中图片的方式不同，我们这里直接将github中的issue导向repo中已经存储的图片
        """
        if self.type == "gitlab":
            targets = [self.repo_url + suffix for suffix in self.resources]
            for i in range(len(self.resources)):
                self.body.replace(self.resources[i], targets[i])
        elif self.type == "github":
            targets = [self.repo_url + "/raw/master" + suffix for suffix in self.resources]
            for i in range(len(self.resources)):
                self.body.replace(self.resources[i], targets[i])
        elif self.type == "gitee":
            raise NotImplementedError
        else:
            raise ValueError

    def to(self, new_type, new_repo_url):
        new_issue = copy.deepcopy(self)
        new_issue.type = new_type
        new_issue.repo_url = new_repo_url
    


#     def download_resources(self, img_dir: pathlib.Path):
#         if not img_dir.exists():
#             img_dir.mkdir()
#         for suffix in self.resources:
#             r = requests.get(self.repo_url+suffix)
#             img_path = img_dir/suffix
#             if img_path.exists():
#                 continue
#             with open(img_path, "wb") as fp:
#                 for chunk  in r.iter_content(chunk_size=64):
#                     fp.write(chunk)

#     def to(self, new_type, new_repo_url):
#         if new_type == self.type:
#             return self
#         # new_issue = Issue(new_type, data=None, repo_url=new_repo_url)
#         new_data = {Issue.ops[new_type]["property_map"][key]}
#         for (key, value) in Issue.ops[self.type]["property_map"].items():





        

# def fetch_issues_list(url, headers=None, type="gitlab", focused_property=None):
#     if type not in ["gitlab", "github", "gitee"]:
#         raise NotImplementedError
#     r = requests.get(url, headers=headers)
#     assert r.status_code == 200
#     issues = json.loads(r.text)

#     if len(issues) == 0:
#         return []
#     if focused_property is None:
#         focused = issues[0].keys()



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
