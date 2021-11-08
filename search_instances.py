import boto3
import csv
import ipaddress
import argparse
import logging
import sys
from pathlib import Path

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

# Takes in boto3 tag dictionary and turns it into key=val format
def map_format(tag_list):
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

    # Create dictionaries to store info.  
    # instance_id: tag
    # private_ipv4: tag
    # public_ipv4: tag
    # instance_id: public_ipv4
    # instance_id: private_ipv4
    # private_ipv4: instance_id
    # public_ipv4: instance_id
    # private_ipv4: public_ipv4
    # public_ipv4: private_ipv4
    instance_ids_tags_dict = {}
    private_ipv4_tags_dict = {}
    public_ipv4_tags_dict = {}
    instance_ids_private_ipv4s_dict = {}
    instance_ids_public_ipv4s_dict = {}
    private_ipv4s_instance_ids_dict = {}
    public_ipv4s_instance_ids_dict = {}
    private_ipv4_public_ipv4_dict = {}
    public_ipv4_private_ipv4_dict = {}
    for instance in running_instances:
        instance_ids_tags_dict[instance.id] = map_format(instance.tags)
        private_ipv4_tags_dict[instance.private_ip_address] = map_format(instance.tags)
        public_ipv4_tags_dict[instance.public_ip_address] = map_format(instance.tags)
        instance_ids_private_ipv4s_dict[instance.id] = instance.private_ip_address
        instance_ids_public_ipv4s_dict[instance.id] = instance.public_ip_address
        private_ipv4s_instance_ids_dict[instance.private_ip_address] = instance.id
        public_ipv4s_instance_ids_dict[instance.public_ip_address] = instance.id
        private_ipv4_public_ipv4_dict[instance.private_ip_address] = instance.public_ip_address
        public_ipv4_private_ipv4_dict[instance.public_ip_address] = instance.private_ip_address

    # Search for instance-ids/ips from the input list and store their tags.  Also inject our own identifier tags into the found tags  
    logging.info('Processing ec2 info...')
    all_tags = []
    for instance_id in search_instance_list:
        if instance_id in instance_ids_tags_dict:
            instance_ids_tags_dict[instance_id]['search_instance_id'] = instance_id
            instance_ids_tags_dict[instance_id]['search_private_ipv4'] = instance_ids_private_ipv4s_dict[instance_id] if instance_ids_private_ipv4s_dict[instance_id] else None
            instance_ids_tags_dict[instance_id]['search_public_ipv4'] = instance_ids_public_ipv4s_dict[instance_id] if instance_ids_public_ipv4s_dict[instance_id] else None
            all_tags.append(instance_ids_tags_dict[instance_id])
    for ipv4 in search_ip_list:
        if ipv4 in private_ipv4_tags_dict:    
            private_ipv4_tags_dict[ipv4]['search_private_ipv4'] = ipv4
            private_ipv4_tags_dict[ipv4]['search_instance_id'] = private_ipv4s_instance_ids_dict[ipv4] if private_ipv4s_instance_ids_dict[ipv4] else None
            private_ipv4_tags_dict[ipv4]['search_public_ipv4'] = private_ipv4_public_ipv4_dict[ipv4] if private_ipv4_public_ipv4_dict[ipv4] else None
            all_tags.append(private_ipv4_tags_dict[ipv4])
        elif ipv4 in public_ipv4_tags_dict:    
            public_ipv4_tags_dict[ipv4]['search_public_ipv4'] = ipv4
            public_ipv4_tags_dict[ipv4]['search_instance_id'] = public_ipv4s_instance_ids_dict[ipv4] if public_ipv4s_instance_ids_dict[ipv4] else None
            public_ipv4_tags_dict[ipv4]['search_private_ipv4'] = public_ipv4_private_ipv4_dict[ipv4] if public_ipv4_private_ipv4_dict[ipv4] else None
            all_tags.append(public_ipv4_tags_dict[ipv4])
    
    # Create a list of distinct tag keys that exists between all the instances that are found in the input file.  
    # Force certain attributes into the beginning columns.
    columns = []
    for tag in all_tags:
        for key,value in tag.items():
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
        for tag in all_tags:
            writer.writerow([tag.get(column, None) for column in columns])
