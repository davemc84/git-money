import json, os, io, datetime, hashlib
import requests
from flask import g
from commonregex import CommonRegex
from two1.lib.wallet.hd_account import HDAccount
from two1.lib.wallet.two1_wallet import Two1Wallet
from multisig_wallet import multisig_wallet

config_path = os.path.dirname(os.path.realpath(__file__)) + '/../config/repos.json'
repository = json.loads(io.open(config_path, 'r').read())
repository_path = repository['path']
DEFAULT_WALLET_PATH = os.path.join(os.path.expanduser('~'),
                                   ".two1",
                                   "wallet",
                                   "multisig_wallet.json")

class github(object):
    def get_github_issue(issue_number):
        print('This is the issue number we are looking up')
        url = 'https://api.github.com/repos/21hackers/git-money/issues/' + issue_number
        try: 
            r = requests.get(url)
        except:
            print("Github issue fetch failed, please ensure that your repository path is properly configured")
        return r.json()['title']
        
    def _create_bitgo_wallet(issue_title, repository_path):
        issue_title_encode = str(issue_title)
        repository_path_encode = str(repository_path)

        issue_title_encode = issue_title.encode('utf-8')
        repository_path_encode = repository_path.encode('utf-8')
        passphrase = hashlib.sha256(repository_path_encode + issue_title_encode).hexdigest()
        multisig_wallet.create_wallet(issue_title, passphrase)
        print('Wallet create')
        bounty_address = multisig_wallet.generate_address(str(issue_title))
        print('Bounty address created')
        print(bounty_address)
        return bounty_address

    def _decorate_issue_params(issue_title, description):
        bitcoin_address = github._create_bitgo_wallet(issue_title, repository_path)
        bounty_image = 'http://git-money-badge.mybluemix.net/badge/' + bitcoin_address
        issue_title = issue_title
        description = "<h6>Reward  (" + bitcoin_address + ")</h>\n\n![BOUNTY](" + bounty_image + ")" + "\n\n" + description

        params = { "title": issue_title, "body": description }
        params = json.dumps(params).encode('utf8')
        return params
    
    @staticmethod
    def create_issue(issue_title, description):

        params = github._decorate_issue_params(issue_title, description)

        github_url = "https://api.github.com/repos/" + repository['path'] + "/issues"
        headers = { "Authorization": "token " + repository['token'],
                    "Content-Type": "application/json",
                    "Cache-Control": "no-cache, no-store, must-revalidate"
        }

        # Setup the request
        try: 
            r = requests.post(github_url, headers=headers, data=params)
        except:
            return print("Github issue creation failed, please ensure that your repository path is properly configured")

        issue_number=r.json()['number']
        with open(DEFAULT_WALLET_PATH, 'r') as f:
            json_data = json.load(f)
            ## ISSUE_TITLE is set as the wallet label / name
            json_data[-1]['issue_number'] = issue_number

        with open(DEFAULT_WALLET_PATH, 'w') as f:
            f.write(json.dumps(json_data))
        
        # TODO: Take the response and check for an ACK, then return true, else handle error
        print(r.json())

    @staticmethod
    def get_address_from_issue(issue_number):

        github_url = "https://api.github.com/repos/" + repository['path'] + '/issues/' + issue_number
        headers = { "Authorization": "token " + repository['token'], "Content-Type": "application/json" }

        # Setup the request
        req = urllib.request.Request(github_url, headers=headers)

        # Make the request, capture the response
        res = urllib.request.urlopen(req).read()
        res = json.loads(res.decode())

        body = res['body']
        address = CommonRegex(body).btc_addresses[0]

        return address

