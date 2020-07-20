import requests
from jinja2 import Environment, FileSystemLoader
import random
import os

TEAMCITY_USER = os.environ.get('teamcity_user')
TEAMCITY_PASSWORD = os.environ.get('teamcity_password')

VCS_USER = os.environ.get('vcs_user')
VCS_PASSWORD = os.environ.get('vcs_password')

URL = 'http://localhost:8080'


class ProjectCreator:
    def __init__(self, projectName, parentProjectId):
        self.projectName = projectName
        self.parentProjectId = parentProjectId
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        self.env = Environment(
            loader=FileSystemLoader('templates'),
            trim_blocks=True,
            lstrip_blocks=True)
        self.teamcity_auth()

    def teamcity_auth(self):
        self.session = requests.session()
        self.session.auth = (TEAMCITY_USER, TEAMCITY_PASSWORD)
        self.headers['X-TC-CSRF-Token'] = self.get_csrf()
        self.session.headers = self.headers

    def get_csrf(self):
        csrf = self.get_request('/authenticationTest.html?csrf').text
        return csrf

    def get_request(self, api_path=""):
        return self.session.get(URL + api_path)

    def post_request(self, api_path, data):
        return self.session.post(URL + api_path, data=data, allow_redirects=False)

    def create_simple_project(self):
        template = self.env.get_template('createBaseProject.j2')
        data = template.render({
            'projectName': self.projectName,
            'parentProjectId': self.parentProjectId
        })
        response = self.post_request(api_path='/app/rest/projects/', data=data).json()
        self.created_project_id = response['id']

    def create_vcs_root(self):
        template = self.env.get_template('createVCSRoot.j2')
        data = template.render({
            'projectName': self.projectName,
            'projectID': self.created_project_id,
            'password': VCS_PASSWORD,
            'user': VCS_USER,
            'gitRepoURL': 'https://github.com/o-bychkov/spring-petclinic-teamcity-dsl.git'
        })
        response = self.post_request(api_path='/app/rest/vcs-roots', data=data).json()
        self.vcs_root_id = response['id']

    def enable_vcs_sync(self):
        template = self.env.get_template('sync_feature.j2')
        data = template.render({
            'VCSRootID': self.vcs_root_id
        })
        response = self.post_request('/app/rest/projects/id:{}/projectFeatures'.format(self.created_project_id), data)
        print response.text

    def disable_sync(self):
        data = {}
        string_from_the_hell = "?synchronizationMode=disabled&-ufd-teamcity-ui-settingsVcsRootId={0}&settingsVcsRootId={1}&buildSettingsMode=PREFER_VCS&_showSettingsChanges=&useCredentialsStorage=true&_useCredentialsStorage=&-ufd-teamcity-ui-settingsFormat=Kotlin&settingsFormat=kotlin&useRelativeIds=true&_useRelativeIds=&tc-csrf-token={2}&projectId={0}&confirmation=".format(
            self.created_project_id,
            self.vcs_root_id,
            self.headers['X-TC-CSRF-Token'])
        self.post_request('/admin/versionedSettings.html' + string_from_the_hell, data=data)

    def enable_sync(self):
        data = {}
        string_from_the_hell = "?synchronizationMode=enabled&-ufd-teamcity-ui-settingsVcsRootId={0}&settingsVcsRootId={1}&buildSettingsMode=PREFER_VCS&_showSettingsChanges=&useCredentialsStorage=true&_useCredentialsStorage=&-ufd-teamcity-ui-settingsFormat=Kotlin&settingsFormat=kotlin&useRelativeIds=true&_useRelativeIds=&tc-csrf-token={2}&projectId={0}&confirmation=import".format(
            self.created_project_id,
            self.vcs_root_id,
            self.headers['X-TC-CSRF-Token'])

        print string_from_the_hell
        self.post_request('/admin/versionedSettings.html' + string_from_the_hell, data=data)


if __name__ == '__main__':
    projectName = 'autoGenProject' + str(random.randint(1,99))
    creator = ProjectCreator(projectName, '_Root')
    creator.create_simple_project()
    creator.create_vcs_root()
    creator.enable_vcs_sync()
    creator.disable_sync()
    creator.enable_sync()

