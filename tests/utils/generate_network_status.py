#!/usr/bin/env python3


import json
import os
import requests
from jinja2 import Template
from pytablewriter import MarkdownTableWriter
from subquery_cli import use_subquery_cli

subquery_cli_version = '0.2.5'
token = os.environ['SUBQUERY_TOKEN']

readme = Template("""
Projects' status is updated every 4 hours
{{dapps_table}}
""")


def generate_networks_list():
    writer = MarkdownTableWriter(
        table_name="List of deployed projects",
        headers=["Network", "Stage status", "Prod status", "Stage commit", "Prod commit"],
        value_matrix=generate_value_matrix(),
        margin=1
    )
    writer.write_table()
    return writer


def get_networks_list(folder):
    sub_folders = [name for name in os.listdir(
        folder) if os.path.isdir(os.path.join(folder, name))]
    return sub_folders


def get_value_from_subquery(network: str, stage: bool):
    r = requests.get(
        'https://api.subquery.network/subqueries/nova-wallet/nova-wallet-%s?stage=%s' % (network, stage))
    response = json.loads(r.content)
    return response


def get_percentage(network, project_id):
    percentage = use_subquery_cli(subquery_cli_version, '--token', token, 'deployment',
                                  'sync-status', '--id', str(project_id), '--key', 'nova-wallet-'+network, '--org', 'nova-wallet')
    status = percentage.split("percent: ")[1:]
    returning_value = status[0].split('%')[0:][0].split('.')[0]
    return returning_value


def generate_progress_status(network, stage):
    data = get_value_from_subquery(network, stage)
    if (data.get('deployed')):
        commit = data.get('deployment').get('version')[0:8]
        if (stage):
            if (data.get('deployment').get('healthStatus').get('indexer')):
                percent = get_percentage(network, data['deployment']['id'])
                progress_bar = '![%s](https://progress-bar.dev/%s?title=Stage)' % (percent, percent)
            else:
                progress_bar = '![0](https://progress-bar.dev/0?title=Error)'
        else:
            if (data.get('deployment').get('healthStatus').get('indexer')):
                percent = get_percentage(network, data['deployment']['id'])
                progress_bar = "![%s](https://progress-bar.dev/%s?title=Prod)" % (percent, percent)
            else:
                progress_bar = '![0](https://progress-bar.dev/0?title=Error)'
    else:
        progress_bar = '![0](https://progress-bar.dev/0?title=Not%20Deployed)'
        commit = '-'
    return progress_bar, commit


def generate_value_matrix():
    network_list = get_networks_list(folder="./networks")
    returning_array = []
    for network in network_list:
        network_data_array = []
        network_data_array.append(
            "[%s](https://explorer.subquery.network/subquery/nova-wallet/nova-wallet-%s)" % (
                network.title(), network)
        )
        stage_status, stage_comit = generate_progress_status(network, stage=True)
        prod_status, prod_commit = generate_progress_status(network, stage=False)
        network_data_array.append(stage_status)
        network_data_array.append(prod_status)
        network_data_array.append(stage_comit)
        network_data_array.append(prod_commit)
        returning_array.append(network_data_array)
        print('%s generated!'%network.title())
    returning_array.sort()
    return returning_array


if __name__ == '__main__':

    dir_name = 'gh-pages'
    try:
        os.makedirs(dir_name)
        print("Directory " , dir_name ,  " Created ")
    except FileExistsError:
        print("Directory " , dir_name ,  " already exists")

    with open("./gh_pages/README.md", "w") as f:
        f.write(readme.render(
            dapps_table=generate_networks_list()
        ))
