Changelog
=========

0.3.1
-----

* Support Pigeons without model instances, by using model class and
  classmethods. If you are upgrading you will need to drop the NOT NULL
  constraint on Pigeon.source_id to use this functionality.

0.2.0
-----

* Adopt semantic versioning.
* Add new function ``pigeonpost.utils.generate_email``

0.1.9
-----

* Fix race condition: running ``deploy_pigeons`` when it's already running
  results in duplicate sending, now it uses a lockfile.
* Protection against client code accidentally returning the same user.
* When sending mail fails, record and report it... this was intended, but code
  was incorrectly expecting a return value instead of catching exceptions.

0.1.8
-----

* truncate number of sink emails that are sent when a pigeon has lots of
  destination users.

0.1.7
-----

* Move to base64 representation of outbox messages. Due to pickle not actually
  using ASCII! See the official bug `here`_.
  You will need to purge your outbox of any unsent messages before upgrading.
  The best process is to deploy_pigeons and upgrade before any new Outbox
  objects are created (usually this only happens from the deploy_pigeons task).

.. _here: http://bugs.python.org/issue2980

0.1.6
-----

* Catch bug where pigeons that had no recipients would never get marked to_send=False.

0.1.5
-----

* Support ``PIGEONPOST_SINK_EMAIL`` setting, which redirects ALL email to a single
  email address. Good for development and staging environments.

0.1.4
-----

* Fix ``process_outbox`` log messages.
* Fix bad use of django mail connection.
* Allow ``Pigeon.send_to`` to be blank.

0.1.3
-----

Minor changes to improve the admin display and slight logic change to updating
pigeons that have already been sent.

0.1.2
-----

This version supports targetted delivery and allows multiple pigeons per model
instance. To upgrade from 0.1.1, the appropriate sql patches in
pigeonpost/sql-migrations should be applied.

