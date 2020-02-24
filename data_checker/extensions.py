import glob
import filecmp

from scrapy import signals
from scrapy.exceptions import NotConfigured
from scrapy.mail import MailSender


class EmailOnChange:
    def __init__(self, destination, mailer):
        self.destination = destination
        self.mailer = mailer

    @classmethod
    def from_crawler(cls, crawler):
        if not crawler.settings.getbool("EMAIL_ON_CHANGE_ENABLED"):
            raise NotConfigured

        destination = crawler.settings.get("EMAIL_ON_CHANGE_DESTINATION")
        if not destination:
            raise NotConfigured("EMAIL_ON_CHANGE_DESTINATION not set")

        mailer = MailSender.from_settings(crawler.settings)

        # instanciate extension
        extension = cls(destination, mailer)

        crawler.signals.connect(extension.engine_stopped, signal=signals.engine_stopped)
        return extension

    def engine_stopped(self):
        # List out previous runs
        runs = sorted(
            glob.glob("/tmp/[0-9]*-[0-9]*-[0-9]*T[0-9]*-[0-9]*-[0-9]*.json"),
            reverse=True,
        )
        if len(runs) < 2:
            return

        # Grab the newest 2 runs
        current_file, previous_file = runs[0:2]

        # Compare them
        if not filecmp.cmp(current_file, previous_file):
            print("\n\n\n THE FILES ARE DIFERENT \n\n\n")
            with open(current_file) as f:
                self.mailer.send(
                    to=[self.destination],
                    subject="Datasets Changed",
                    body="Changes in datasets detected, see attachment for current datasets",
                    attachs=[(current_file.split("/")[-1], "application/json", f)],
                )
        else:
            print("\n\n\n NO CHANGE \n\n\n")

        # If difference? send an email

