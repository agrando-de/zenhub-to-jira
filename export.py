"""
Originally from: https://gist.github.com/unbracketed/3380407
Exports Issues from a specified repository to a CSV file
Uses basic authentication (Github username + password) to retrieve Issues
from a repository that username has access to. Supports Github API v3.

JIRA issue fields:
https://confluence.atlassian.com/adminjiracloud/issue-fields-and-statuses-776636356.html

Other JIRA import fields:
https://confluence.atlassian.com/adminjiracloud/importing-data-from-csv-776636762.html

Post here: https://github.com/ZenHubIO/support/issues/1070
"""
import csv
import datetime
import requests

GITHUB_USER = ''
GITHUB_PASSWORD = ''
AUTH = (GITHUB_USER, GITHUB_PASSWORD)

ZENHUB_AUTHENTICATION_TOKEN = ''
ZENHUB_REPO_ID = ''
ZENHUB_HEADERS = {
    'X-Authentication-Token': ZENHUB_AUTHENTICATION_TOKEN,
}
REPO = ''  # format is username/repo


def iterate_pages(repository):
    """
    Make request for 100 issues starting from the first page until the last page is reached
    Every request text is appended to 'results'
    :return JSON object with all issues
    """
    results = []
    page_number = 1
    # per_page can be moved into a var in case you need less than 100 issues per request
    issues = 'https://api.github.com/repos/{}/issues?state=all&page={}&per_page=100'.format(repository, page_number)
    request = requests.get(issues, auth=AUTH)
    results.append(request.json())

    # make requests until the 'last' url is reached and increase the page number by 1 for each request
    while 'last' in request.headers['link'] and 'next' in request.headers['link']:
        page_number += 1
        issues = 'https://api.github.com/repos/{}/issues?state=all&page={}&per_page=100'.format(repository, page_number)
        request = requests.get(issues, auth=AUTH)
        results.append(request.json())
        print(request.headers['link'])
    else:
        print("No more pages")
    return results


def get_comments_max_nr():
    """
    Get maximum number of comments for one issue in order to write header columns when creating the CSV file
    :return: count of the max comments per issue
    """
    comments_list = []
    for result in total_result:
        for issue in result:
            if issue.get('pull_request') is None:
                if issue['comments'] > 0:
                    comments_list.append(issue['comments'])
    return max(comments_list)


def get_labels_nr():
    """
    Get number of labels for the repo. Used to write header columns when creating the CSV file
    Appends each unique label found to 'labels_list'
    :returns length of the labels_list
    """
    labels_list = []
    for result in total_result:
        for issue in result:
            if issue.get('pull_request') is None:
                for label in issue['labels']:
                    if label is not None:
                        # Check if the label name is already appended to 'labels_list'
                        if label['name'] not in labels_list:
                            labels_list.append(label['name'])
    return len(labels_list)


def write_issues(results):
    for page in results:
        for issue in page:

            # We're only importing active issues
            if issue.get('state') == 'closed':
                continue

            issue_type = None
            issue_resolution = None
            issue_milestone = None
            resolved_at = None
            assignee = None
            # filter only issues that are not pull requests
            if issue.get('pull_request') is None:
                issue_number = issue['number']

                # make request to zenhub with the issue number
                zenhub_request = requests.get(
                    'https://api.zenhub.io/p1/repositories/{}/issues/{}'.format(ZENHUB_REPO_ID, issue_number),
                    headers=ZENHUB_HEADERS)

                zenhub_json_object = zenhub_request.json()

                # As of 03.2020, JIRA does not create "Refactoring" and "Task" issues types, instead it makes them "Story" types.
                # It is advised to leave the "Refactoring" label and do a data migration inside of JIRA to remove the label and convert the issue type
                if zenhub_json_object.get('is_epic'):
                    issue_type = 'Epic'
                elif 'bug' in [label['name'] for label in issue['labels']]:
                    issue_type = 'Bug'
                elif 'refactor' in [label['name'] for label in issue['labels']]:
                    issue_type = 'Refactoring'
                else:
                    issue_type = 'Task'

                issue_status = zenhub_json_object['pipeline']['name']
                if zenhub_json_object.get('estimate'):
                    issue_estimation = zenhub_json_object['estimate']['value']
                else:
                    issue_estimation = ''

                if issue.get('assignee') is not None:
                    assignee = issue['assignee']['login']

                reporter = issue['user']['login']

                if issue.get('milestone') is not None:
                    issue_milestone = issue['milestone']['title']

                # Transform dates to a format that can be parsed by Jira
                # Java Format (used by Jira) "dd/MMM/yy h:mm a" == "14/Nov/18 10:39 AM"
                # Python = "%d/%b/%y %l:%M %p"
                date_format_rest = '%Y-%m-%dT%H:%M:%SZ'
                date_format_jira = '%d/%b/%y %l:%M %p'
                date_created = datetime.datetime.strptime(issue['created_at'], date_format_rest)
                created_at = date_created.strftime(date_format_jira)

                date_updated = datetime.datetime.strptime(issue['updated_at'], date_format_rest)
                updated_at = date_updated.strftime(date_format_jira)

                if issue.get('closed_at') is not None:
                    date_resolved = datetime.datetime.strptime(issue['closed_at'], date_format_rest)
                    resolved_at = date_resolved.strftime(date_format_jira)

                # Imported markdown doesn't look good in JIRA, remove the headers
                description = issue['body'].replace('#', '').replace('##', '').replace('###', '').strip() + '\n\n'

                # Append comments to description. JIRA import breaks when trying to import comments
                comments = []
                if issue['comments'] > 0:
                    comments_request = requests.get(issue['comments_url'], auth=AUTH)
                    for comment in comments_request.json():
                        issue_comments = 'Username: {}\n{};'.format(comment['user']['login'], comment['body'])
                        comments.append(issue_comments)
                comments = comments + [''] * (comments_max_nr - len(comments))
                description += '\n'.join(comments)

                # Add a label `imported_datetime`. Makes it easier to identify batch imported issues.
                labels_list = ['imported_{}'.format(datetime.datetime.now().strftime('%d.%m.%y-%H:%M'))]
                labels = issue['labels']
                for label in labels:
                    label_name = label['name']
                    labels_list.append(label_name)

                labels_list = labels_list + [None] * (labels_max_nr - len(labels_list))

                if issue_status is 'Closed':
                    issue_resolution = 'Done'

                csvout.writerow([
                    issue['title'].strip(),
                    issue_type,
                    issue_status,
                    # issue_resolution,
                    # issue_milestone,
                    description,
                    # assignee,
                    # reporter,
                    # created_at,
                    # updated_at,
                    # resolved_at,
                    issue_estimation,
                    *labels_list,  # labels (multiple labels in multiple columns)
                ])


if __name__ == '__main__':
    # Call and save the JSON object created by ´iterate_pages()´
    total_result = iterate_pages(REPO)
    comments_max_nr = get_comments_max_nr()
    labels_max_nr = get_labels_nr()

    # Create enough labels columns to hold max number of labels
    labels_header_list = ['Labels'] * labels_max_nr
    csvfile = '%s-issues.csv' % (REPO.replace('/', '-'))
    csvout = csv.writer(open(csvfile, 'w', newline=''))

    # Write CSV Header
    csvout.writerow((
        'Summary',
        'Type',  # Need Zenhub API for this (task, epic, bug)
        'Status',  # Need Zenhub API for this (in which pipeline is located)
        # 'Resolution',  # Need Zenhub API for this (done, won't do, duplicate, cannot reproduce) - for software projects
        # 'Fix Version(s)',  # milestone
        'Description',
        # 'Assignee',
        # 'Reporter',
        # 'Created',
        # 'Updated',
        # 'Resolved',
        'Estimate',
        *labels_header_list,
    ))

    write_issues(total_result)
