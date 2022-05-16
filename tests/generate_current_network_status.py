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


def get_value_from_subquery(network):
    project_data = use_subquery_cli(subquery_cli_version, '--token', token, 'deployment', 'list', '--key', 'nova-wallet-'+network, '--org', 'nova-wallet', '-o', 'json')
    response = json.loads(project_data)
    return response


def get_percentage(network):
    try:
        percentage = use_subquery_cli(subquery_cli_version, '--token', token, 'deployment',
                                  'sync-status', '--id', str(network['id']), '--key', network['projectKey'].split('/')[1], '--org', 'nova-wallet')
        status = percentage.split("percent: ")[1:]
        returning_value = status[0].split('%')[0:][0].split('.')[0]
    except:
        returning_value = False
    return returning_value


def generate_progress_status(network):
    data = get_value_from_subquery(network)
    prod_commit = prod_progress_bar = stage_commit = stage_progress_bar = '-'

    for network in data:
        if (network['type'] == 'primary'):
            prod_commit = network['version'][0:8]
            if (network['status'] == 'error'):
                prod_progress_bar = '![0](https://progress-bar.dev/0?title=Error)'
            elif (network['status'] == 'running'):
                prod_percent = get_percentage(network)
                if (prod_percent):
                    prod_progress_bar = "![%s](https://progress-bar.dev/%s?title=Prod)" % (prod_percent, prod_percent)
                else:
                    prod_progress_bar = '![0](https://progress-bar.dev/0?title=Error)'

        elif (network['type'] == 'stage'):
            stage_commit = network['version'][0:8]
            if (network['status'] == 'error'):
                stage_progress_bar = '![0](https://progress-bar.dev/0?title=Error)'
            elif (network['status'] == 'running'):
                stage_percent = get_percentage(network)
                if (stage_percent):
                    stage_progress_bar = "![%s](https://progress-bar.dev/%s?title=Stage)" % (stage_percent, stage_percent)
                else:
                    stage_progress_bar = '![0](https://progress-bar.dev/0?title=Error)'
    return prod_progress_bar, prod_commit, stage_commit, stage_progress_bar


def generate_value_matrix():
    network_list = get_networks_list(folder="./networks")
    returning_array = []
    for network in network_list:
        network_data_array = []
        network_data_array.append(
            "[%s](https://explorer.subquery.network/subquery/nova-wallet/nova-wallet-%s)" % (
                network.title(), network)
        )
        prod_progress_bar, prod_commit, stage_commit, stage_progress_bar = generate_progress_status(network)
        network_data_array.append(stage_progress_bar)
        network_data_array.append(prod_progress_bar)
        network_data_array.append(stage_commit)
        network_data_array.append(prod_commit)
        returning_array.append(network_data_array)
        print('%s generated!'%network.title())
    returning_array.sort()
    return returning_array


if __name__ == '__main__':
    with open("./docs/README.md", "w") as f:
        f.write(readme.render(
            dapps_table=generate_networks_list()
        ))
