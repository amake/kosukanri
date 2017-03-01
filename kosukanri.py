import sys
import os
from os import path
import subprocess
from datetime import date, datetime
from collections import namedtuple, defaultdict
from calendar import monthrange
import logging
import re

logging.basicConfig(level=logging.DEBUG)

Entry = namedtuple('Entry', ['repo', 'authored', 'committed', 'summary'])


def get_stdout(cmd, cwd=None):
    proc = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE)
    stdout, stderr = proc.communicate()
    return stdout if proc.returncode == 0 else None

GIT_LOG = ['git', 'log']
GIT_CONFIG_GET = ['git', 'config', '--get']
TICKET_PATTERN = re.compile(r'[A-Z0-9]+-[0-9]+')

def list_git_repos(in_dir):
    items = [path.join(in_dir, item) for item in os.listdir(in_dir)]
    return [item for item in items if path.isdir(item)
            and path.isdir(path.join(item, '.git'))]

def get_git_author(repo):
    name = get_stdout(GIT_CONFIG_GET + ['user.name'], cwd=repo).strip()
    email = get_stdout(GIT_CONFIG_GET + ['user.email'], cwd=repo).strip()
    return '%s <%s>' % (name, email)

def get_entries(repo, since=None, authors=None):
    if not since:
        since = date.today().replace(day=1)
    if not authors:
        authors = set(get_git_author(r) for r in [repo, None])
    log_cmd = GIT_LOG + git_log_args(since, authors)
    log = get_stdout(log_cmd, cwd=repo)
    return [Entry(repo, *entry.split('\x00')) for entry in log.strip().split('\n')] if log else []

def git_log_args(since, authors):
    return ['--format=%at%x00%ct%x00%<(80,trunc)%s',
            '--all',
            '--since=%s' % since,
            '--author=%s' % '\|'.join(authors)]

def print_summary(data, month):
    _, days_in_month = monthrange(month.year, month.month)
    days = [month.replace(day=d) for d in xrange(1, days_in_month + 1)]
    for day in days:
        entries = data[day]
        print('%s |%s' % (day, '*' * len(entries)))
    for day in days:
        entries = data[day]
        if entries:
            print_day_summary(entries, day)

def print_day_summary(entries, day):
    print(day)
    for repo, ents in group_by_repo(entries).iteritems():
        repo_name = path.basename(repo)
        commits = len(ents)
        if not commits:
            raise Error('No commits on day that should have commits')
        elif commits == 1:
            print('  %s: 1 commit' % repo_name)
        else:
            span = calculate_timespan(ents, day)
            tickets = group_by_ticket(ents)
            if not tickets:
                print('  %s: %d commits over %s' % (repo_name, commits, span))
            elif len(tickets) == 1:
                print('  %s: %d commits over %s (%s)' % (repo_name, commits, span, tickets.keys()[0]))
            else:
                print('  %s: %d commits over %s' % (repo_name, commits, span))
                print('    %s' % summarize_tickets(tickets, day))

def calculate_timespan(entries, day):
    times = [float(time) for entry in entries for time in [entry.authored, entry.committed]]
    times_in_day = [time for time in times if datetime.utcfromtimestamp(time).date() == day]
    seconds = max(times_in_day) - min(times_in_day)
    return seconds_to_string(seconds) if seconds > 0 else ''

def seconds_to_string(seconds):
    if seconds < 60:
        return '1 second' if seconds == 1 else '%d seconds' % seconds
    minutes = seconds / 60.0
    if minutes < 60:
        return  '1 minute' if minutes == 1 else '%d minutes' % minutes
    hours = minutes / 60.0
    return '1 hour' if hours == 1 else '%d hours' % hours

def group_by_day(entries):
    daily = defaultdict(list)
    for entry in entries:
        for day in get_entry_days(entry):
            daily[day].append(entry)
    return daily

def get_entry_days(entry):
    times = [float(time) for time in [entry.authored, entry.committed]]
    return set(datetime.utcfromtimestamp(time).date()
               for time in times)

def group_by_repo(entries):
    repos = defaultdict(list)
    for entry in entries:
        repos[entry.repo].append(entry)
    return repos

def group_by_ticket(entries):
    tickets = defaultdict(list)
    for entry in entries:
        match = TICKET_PATTERN.search(entry.summary)
        if match:
            tickets[match.group(0)].append(entry)
    return tickets

def summarize_tickets(tickets, day):
    raw_times = {ticket: calculate_timespan(ents, day) for ticket, ents in tickets.iteritems()}
    times = [ticket if not time else '%s: %s' % (ticket, time)
             for ticket, time in sorted(raw_times.iteritems())]
    return ', '.join(times)

def main(root, datestr):
    logging.debug('Looking for repos in %s...',path.abspath(root))
    repos = list_git_repos(root)
    logging.debug('Found %d repos', len(repos))
    try:
        month = datetime.strptime(datestr, '%Y-%m').date()
    except ValueError, e:
        logging.critical('Bad date format: %s', e)
        sys.exit(1)
    entries = [entry for repo in repos for entry in get_entries(repo, month)]
    daily = group_by_day(entries)
    print_summary(daily, month)
        

if __name__ == '__main__':
    main(*sys.argv[1:])
