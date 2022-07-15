import boto3
import csv
import ipaddress
import argparse
import logging
import sys

# This class is essentially an array of dictionaries used to store instance metadata including tags.
#
class Table(object):
    def __init__(self):
        self._rows = []     # each row contains a dictionary of ec2 instance metadata
        self._instance_id_map = {}  # for searching a row by instance id
        self._private_ipv4_map = {} # for searching a row by private ipv4
        self._public_ipv4_map = {}  # for searching a row by public ipv4

    def add_row(self, row):
        self._rows.append(row)
        self._instance_id_map[row['search_instance_id']] = row
        self._private_ipv4_map[row['search_private_ipv4']] = row
        if 'search_public_ipv4' in row and row['search_public_ipv4']:
            self._public_ipv4_map[row['search_public_ipv4']] = row

    def get_rows(self):
        return self._rows

    def get_row_instance_id(self, instance_id):
        return self._instance_id_map[instance_id]

    def get_row_private_ipv4(self, ip_address):
        return self._private_ipv4_map[ip_address]

    def get_row_public_ipv4(self, ip_address):
        return self._public_ipv4_map[ip_address]

    def contains_instance_id(self, instance_id):
        return True if instance_id in self._instance_id_map else False

    def contains_private_ipv4(self, ip_address):
        return True if ip_address in self._private_ipv4_map else False
    
    def contains_public_ipv4(self, ip_address):
        return True if ip_address in self._public_ipv4_map else False


# Setup basic logging to console
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

# Tests if a string is ipv4 
def is_ipv4(ip):
    try:
        ipaddress.IPv4Address(ip)
        return True
    except ipaddress.AddressValueError:
        return False

# Read in file where each line corresponds to an IP or instance-id
def parse_input_file(filename):
    with open(filename) as f:
        entries = f.readlines()
    ip_list = []
    instance_list = []
    for entry in entries:
        ip_list.append(entry.strip()) if is_ipv4(entry.strip()) else instance_list.append(entry.strip())
    return ip_list, instance_list

# Takes in boto3 tag dictionary and turns it into normal dictionary
def dict_format(tag_list):
    tmp_dict = {}
    if not tag_list:
        return tmp_dict
    for tag in tag_list:
        tmp_dict[tag['Key']] = tag['Value']
    return tmp_dict


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-i','--inputfile', help='Input file containing a list of public or private ipv4s or instance ids with one entry per line', required=True)
    parser.add_argument('-o','--outputfile', help='Output csv file', required=True)
    parser.add_argument("-r", "--region", help="The AWS Region to search the instances", required=True)
    parser.add_argument("-p", "--profile", help="The credential profile to use if not using default credentials")
    args = parser.parse_args()
    inputfile = args.inputfile
    outputfile = args.outputfile
    region = args.region
    if args.profile:
        session = boto3.session.Session(region_name=region, profile_name=args.profile)
    else:
        session = boto3.session.Session(region_name=region)

    # Get all running instances in the account
    logging.info('Retrieving ec2 info...')
    ec2_resource = session.resource('ec2')
    running_instances = ec2_resource.instances.all()

    # Parse inputfile into two lists, one to store ips and other for instance-ids
    search_ip_list, search_instance_list = parse_input_file(inputfile)

    # Create a table to store needed metadata of all ec2 instances in region
    logging.info('Processing...')
    all_instance_table = Table()
    private_ipv4_list = []  
    public_ipv4_list = []
    for instance in running_instances:
        info_dict = {'search_instance_id':instance.id, 'search_public_ipv4':instance.public_ip_address, 'search_private_ipv4':instance.private_ip_address}
        info_dict.update(dict_format(instance.tags))
        all_instance_table.add_row(info_dict)
        private_ipv4_list.append(instance.private_ip_address)
        public_ipv4_list.append(instance.public_ip_address)

    # Create a table to store needed metadata of all ec2 instance that's being searched
    search_table = Table()
    for instance_id in search_instance_list:
        if all_instance_table.contains_instance_id(instance_id):
            search_table.add_row(all_instance_table.get_row_instance_id(instance_id))
    for ip_address in search_ip_list:
        if all_instance_table.contains_private_ipv4(ip_address):
            search_table.add_row(all_instance_table.get_row_private_ipv4(ip_address))
        elif all_instance_table.contains_public_ipv4(ip_address):
            search_table.add_row(all_instance_table.get_row_public_ipv4(ip_address))

    # Find unique tag key among all the instances that have been found.  These will be the columns.
    columns = []
    for row in search_table.get_rows():
        for key,value in row.items():
            if key not in columns:
                columns.append(key)
    columns.sort()
    headers = ['search_instance_id', 'search_public_ipv4', 'search_private_ipv4', 'Name']
    columns = [ e for e in columns if e not in headers]
    columns = ['search_instance_id', 'search_public_ipv4', 'search_private_ipv4', 'Name'] + columns

    # Write result to file.  If a tag does not exist, it is left blank 
    logging.info('Writing result to {}'.format(outputfile))
    with open(outputfile, 'w') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(columns)
        for row in search_table.get_rows():
            writer.writerow([row.get(column, None) for column in columns])
