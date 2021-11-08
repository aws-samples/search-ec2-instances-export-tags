## Search EC2 Instances and Export Tags to CSV

### Pre-requisites Installation

1. Install and Setup virtualenv

python3 -m pip install virtualenv
python3 -m venv env
source env/bin/activate

2. Install packages:

pip3 install -r requirements.txt

3. Configure the AWS CLI:

aws configure

### Script Usage

python search_instances.py -i instance_list -o out.csv -r us-east-1

Example syntax: python search_instances.py -i INPUTFILE -o OUTPUTFILE -r REGION [-p PROFILE]

Parameters:
1. -i/--inputfile (required) - This is the list of instance-ids, private or public ipv4s of the EC2 instances you are searching for.  The list can be any combination of them.
2. -o/--outputfile (requied) - This is the output csv file
3. -r/--region (required) - This is the region to search the instances.
4. -p/--profile profile (optional) - This is the AWS CLI named profile to use. If not specified, the default configured credential will be used.

Examples:
1) python search_instances.py -i instance_list -o out.csv -r us-east-1
2) python search_instances.py -i instance_list -o out.csv -r us-east-1 -p devprofile


## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

