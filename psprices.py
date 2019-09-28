#!/usr/bin/env python3

"""Send an email to the configured email adress if a game you want is on sale"""

import email
import json
import logging
import smtplib
import sys
import threading

import feedparser

logging.getLogger().setLevel(logging.INFO)


class Platform(object):
    def __init__(self, name, feed_url):
        self.name = name
        self.feed = feedparser.parse(feed_url)

    def search(self, game_list):
        result = []
        for game in game_list:
            for item in self.feed['items']:
                if game.lower() in item['title'].lower():
                    result.append(item['title'])
        return result


class Gmail(object):
    def __init__(self, host, port, sender, password, receiver):
        logging.info('Opening mail connection')
        self.smtp = smtplib.SMTP(host, port)
        self.sender = sender
        self.receiver = receiver

        self.smtp.starttls()
        self.smtp.login(sender, password)

    def send_email(self, platform_name, body):
        logging.info(f'Sending mail to {self.receiver} for {platform_name}')

        message = email.message.EmailMessage()
        message.set_content(str(body))
        message['From'] = self.sender
        message['To'] = self.receiver
        message['Subject'] = f'New prices for {platform_name}'

        self.smtp.send_message(message, self.sender, self.receiver)

    def close(self):
        logging.info('Closing mail connection')
        self.smtp.quit()


def parse_configuration():
    """Parse configuration file"""
    with open('config.json') as config_file:
        configuration = json.load(config_file)

    return configuration


def main():
    """Send an email to the configured email adress if a game you want is on sale"""

    # Parse configuration and set vars
    try:
        configuration = parse_configuration()
        timer = configuration.get('timer')
        gmail = configuration.get('gmail')
        feeds = configuration.get('feeds')
        games = configuration.get('games')
    except json.decoder.JSONDecodeError:
        logging.error('Failed to decode JSON configuration file')
        sys.exit(1)

    # Create thread timer logic
    threading.Timer(timer, main).start()

    # Generate all platforms feeds
    platforms = {}
    for platform_name, url in feeds.items():
        logging.info(f'Generating {platform_name} feed')
        platforms[platform_name] = Platform(platform_name, url)

    # Search prices for all platform, according to game list
    results = {}
    for platform_name, platform in platforms.items():
        game_list = games.get(platform_name)
        if game_list:
            logging.info(f'Searching for {platform_name} prices')
            results[platform_name] = platform.search(game_list)
        else:
            logging.info(f'Empty game list for {platform_name}')

    # Create mail object
    gmail = Gmail(gmail['host'], gmail['port'], gmail['sender'], gmail['password'], gmail['receiver'])

    # Send an email for each platform
    for platform_name, platform_result in results.items():
        if platform_result:
            message = f'New prices for {platform_name}:\n\n'
            for result in platform_result:
                message += f'- {result}\n'
            gmail.send_email(platform_name, message)

    gmail.close()
    logging.info(f'Next pass in {timer} seconds')


if __name__ == '__main__':
    main()

