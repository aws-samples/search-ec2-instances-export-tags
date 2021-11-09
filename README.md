## Search EC2 Instances and Export Tags to CSV

Imagine you're working on a task and out of the blue, the security team send you a ticket with a list of instances with outdated software that needs to be updated.  You might be looking at a list of hundreds of instance ids or ip addresses and you'll be wondering what these instances are or who they belong to.  This project can help you answer that question.  This is a python script that takes in a list of instance-ids, private or public ipv4 addresses and searches for them in your AWS account.  For the ones it finds, it creates a CSV file that contains the combined tags of all the instances.  By looking at this CSV file, you should be able to better categorize these instances.

### Input Example

![Example Input](images/input.png?raw=true "Title")

### Output Example

![Example Input](images/output.png?raw=true "Title")

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

