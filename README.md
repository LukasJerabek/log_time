# 🕒 logtime
This is minimalistic time-tracking tool based on the presumption, that the simplest way to track time is by writing down the timestamp, when switching context.

Calculates statistics from timestamps and optionally sends them to Redmine api.

---

## How to run

- Clone this repo anywhere you want \
`git clone https://github.com/LukasJerabek/logtime.git`
- Enter repo \
`cd logtime`
- Read through the below "How It Works" section and do the necessary preparation.
- After preparation run logtime preferably with uv: \
`uv run logtime --days-back <number>` \
or just \
`uv run logtime <number>` \
or for todays daily file rely on default 0 \
`uv run logtime` \
--days-back parameter lets you compute files older than today.
- You can prepare daily file by running \
`uv run logtime --days-back <number> prepare` \
or just \
`uv run logtime <number> prepare` \
or for todays daily file rely on default 0 \
`uv run logtime prepare`
- You can add record to your daily file by running \
`uv run logtime --days-back <number> add 77887 initial consultation with tech lead` \
or just \
`uv run logtime <number> add 77887 initial consultation with tech lead` \
or for todays daily file rely on default 0 \
`uv run logtime add 77887 initial consultation with tech lead` \
or find the daily file and add a record manually

It is recommended to create some alias to run logtime for example in you .bashrc/.zshrc/...:
```
logtime() {
  pushd ~/Projects/logtime/ || return

  local days_back=""

  # If the first argument is --days-back
  if [[ "$1" == "--days-back" ]]; then
    days_back="--days-back $2"
    shift 2
  # If the first argument is a number
  elif [[ "$1" =~ '^[0-9]+$' ]]; then
    days_back="--days-back $1"
    shift
  fi

  # Now $@ is the subcommand + arguments
  echo $days_back
  echo $@
  uv run logtime $days_back "$@"

  popd
}
```

After that you can just call these simpler commands from anywhere in your shell. Don't forget to reload the shell before trying.

| Command                         | Runs as                                |
| ------------------------------- | -------------------------------------- |
| `logtime 2`                     | `uv run logtime --days-back 2`         |
| `logtime prepare`               | `uv run logtime prepare`               |
| `logtime add asdf`              | `uv run logtime add asdf`              |
| `logtime 2 prepare`             | `uv run logtime --days-back 2 prepare` |
| `logtime --days-back 3 add foo` | `uv run logtime --days-back 3 add foo` |

Alternatively you can install logtime in your global environment, but this is left for advanced users to manage on their own.

---

## How It Works

1. Typically, after configuring root_folder, you would prepare your daily file with `logtime prepare` command automatically creating below directory structure \
`root_folder/YYYY/MM/YYYY-MM-DD {DAYOFWEEK}.md` \
where DAYOFWEEK is any of MO,TU,WE,TH,FR,SA,SU.

3. Then you would start filling in the timestamps with optional task id and optional description similar to this:
```
08:00 12345 Same description will be tracked together in statistics, and reported together in redmine.
08:30 12345 differing description will be tracked separately in statistics, also reported to redmine separately.
09:00 12345 Same description will be tracked together in statistics, and reported together in redmine.
09:10 45678
10:00 This will appear as work activity in statistics, but without task id can't be reported to redmine api.
10:10 organization
10:20 # lunch, hashtag marks nonworking activity
10:30 45678
11:00 # end, this was a short day
```
Records with only task id still work, but redmine report won't have any text.\
You can also make use of add command explained below.

4. To make this work create a copy of logtime/config_example.yaml and name it logtime/config.yaml.

5. Don't forget to investigate your logtime/config.yaml.
- set your root_folder path of the daily files.
- Optionally adjust defaults dict, that serves as a dictionary of texts, that you want to exchange for task id at computation time, so that you wouldn't have to remember all the ids that you use regularly.

5. After you would run logtime it will:
   * Read timestamps and descriptions
   * Compute deltas between entries
   * Group by task and description
   * Produce a summary in your log file
   * Optionally send rounded hours to Redmine

6. Daily file will be extended with statistics
```
Summary:
40 = 0h 40m ~ 0.75h: 12345 same description will be tracked together in statistics, and reported together in redmine statistics
30 = 0h 30m ~ 0.5h: 12345 differing description will be tracked separately in statistics, also reported to redmine statistics separately.
80 = 1h 20m ~ 1.25h: 45678
10 = 0h 10m ~ 0.25h: This will appear as work activity in statistics, but without task id can't be reported to redmine api.
10 = 0h 10m ~ 0.25h: 77549 organization  # notice this has been updated with task id from defaults in logtime/config.yaml
10 = 0h 10m ~ 0.25h: # lunch, hashtag marks nonworking activity

total: 3h 0m (180)
total work: 2h 50m (170)
total work rounded hours: 3.0
total free:  0h 10m (10)
saldo: -5h 0m (-300)
working too little  # this assumes 8 hours shifts
already parsed
```

7. Finally you will be prompted with
`Send on api? (y/n):`
For redmine report to work, you also need to set environment variables LOGTIME_REDMINE_API_KEY and LOGTIME_REDMINE_URL first.
Alternatively you can put values directly in your config.yaml, but nowhere else, definitely not in config_example.yaml, because only the config.yaml is ignored by git!

---

## Contributing

Contribution is welcome, however please keep the tool simple.

---

## License

This project is licensed under **MIT**.

---
