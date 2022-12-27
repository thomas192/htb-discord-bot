# Hack The Box Discord Bot

A Discord bot that sends messages when members flag a box or a challenge (actives only).

## Usage

Rename ``.env-example`` to ``.env``. ``DISCORD_TOKEN`` and ``HTB_TOKEN`` values must be set.

Initialize the bot on the designated channel with ``!init``. By default, the channel's name must be ``pwned``.

Users can bind their HTB id with ``!bind <id>`` and unbind with ``!purge``. 

## Note

If you come across this repository, pull requests are welcome. I'm sure there's room for improvement.