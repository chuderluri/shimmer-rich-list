from iota_client import IotaClient
import json
import pandas
import argparse

node_url = 'https://api.shimmer.network'


def command_line_arguments():
    parser = argparse.ArgumentParser(description="This script calculates the address rich list of a shimmer token",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-n", "--node", help="shimmer Node URL", default=node_url)
    parser.add_argument("-c", "--csv_name", help="name of the csv file", default='rich_list.csv')
    parser.add_argument("token_id", help="The token ID which should be analyzed")
    args = parser.parse_args()
    return vars(args)


def read_basic_token_info(client, token_id):

    foundry_output_id = client.foundry_output_id(token_id)
    token_data = client.get_output(foundry_output_id)

    max_supply = int(token_data['output']['tokenScheme']['maximumSupply'], 0)

    json_data = token_data['output']['immutableFeatures'][0]['data'].replace('0x', '')
    json_data = json.loads(bytearray.fromhex(json_data).decode('utf-8'))

    name = json_data['name']
    symbol = json_data['symbol']
    decimals = json_data['decimals']

    return {
        'name': name,
        'id': token_id,
        'max_supply': max_supply,
        'symbol': symbol,
        'decimals': decimals
    }


if __name__ == '__main__':

    config = command_line_arguments()

    # Connect to Node
    client = IotaClient({'nodes': [config['node']]})
    node_info = client.get_info()
    if node_info['nodeInfo']['status']['isHealthy'] is not True:
        raise Exception('Selected node is not healthy')

    # Get basic token information
    token_info = read_basic_token_info(client, config['token_id'])
    print('========= Token Information =========')
    print('Token Name: {}'.format(token_info['name']))
    print('Token Id: {}'.format(token_info['id']))
    print('Token Decimals: {}'.format(token_info['decimals']))

    # Get all Outputs with tokens
    print('Read all outputs ids with tokens..')
    output_ids_with_tokens = client.basic_output_ids([{'hasNativeTokens': True}])
    print('Read all output data..')
    outputs = client.get_outputs(output_ids_with_tokens)
    print(f'This token is on {len(outputs)} outputs')

    # Calculate amount per address
    address_with_amount = {}
    for output in outputs:
        for nativeToken in output['output']['nativeTokens']:

            if nativeToken['id'] != config['token_id']:
                continue

            if output['output']['unlockConditions'][0]['address']['type'] == 0:
                address = client.hex_to_bech32(output['output']['unlockConditions'][0]['address']['pubKeyHash'], 'smr')

            if address not in address_with_amount.keys():
                address_with_amount[address] = 0

            address_with_amount[address] += int(nativeToken['amount'], 0)

    # Postprocessing
    print('Start postprocessing..')
    df = pandas.DataFrame(address_with_amount, index=['amount']).transpose()
    assert df.amount.sum() == token_info['max_supply']
    df = df.sort_values(by='amount', ascending=0)
    df['percent'] = 100 / token_info['max_supply'] * df.amount
    df.amount = df.amount / 10 ** token_info['decimals']        # use correct decimal count
    df = df.reset_index(names='address')

    # Export
    print('Export to CSV')
    df.to_csv(config['csv_name'])

    # Print Rich-List
    print('========= Adress Rich List =========')
    print(df.head(n=20).to_string())
    print('..')
