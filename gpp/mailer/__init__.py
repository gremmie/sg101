from socket import error as socket_error
import smtplib
import time

import django.core.mail

import mailer.models


def enqueue_mail(subject, message, from_email, recipient_list):
    """Creates mailer mail queue entries for the given email."""

    if len(subject) > mailer.models.MAX_SUBJECT:
        subject = u'%s...' % subject[:mailer.models.MAX_SUBJECT - 3]

    for recipient in recipient_list:
        mailer.models.Message(
                from_address=from_email,
                to_address=recipient,
                subject=subject,
                body=message).save()


def send_queued_mail():
    """Reads the queued messages from the database, sends them, and removes them
    from the queue."""

    sent, errors = 0, 0

    import logging
    logging.debug("Sending queued mail...")
    start_time = time.time()

    msgs = mailer.models.Message.objects.all()
    for msg in msgs:
        try:
            django.core.mail.send_mail(
                    msg.subject, 
                    msg.body, 
                    msg.from_address, 
                    [msg.to_address],
                    fail_silently=False)
        except (socket_error, smtplib.SMTPException), e:
            errors += 1
            logging.error("Error sending queued mail: %s" % e)
        else:
        	sent += 1
        	msg.delete()

    end_time = time.time()
    logging.debug("Sent queued mail: %d successful, %d error(s); elapsed time: %.2f" % (
        sent, errors, end_time - start_time))
