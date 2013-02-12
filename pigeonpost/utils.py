import os
import sys
import datetime

class single_instance(object):

    def __init__(self, pidfile_name):
        self.pidfile_name = pidfile_name

    def __call__(self, f):
        def wrapped_f(*args,**kwargs):
            full_path = os.path.join(self.pidfile_name + '.pid')
            # Check if there is already a lock file existing
            if os.access(full_path, os.F_OK):
                if self.check_pid(full_path):
                    sys.exit(1)
            # put a PID in the pid file
            self.create_pid_file(full_path)
            try:
                f(*args,**kwargs)
            except:
                # Catch any errors and delete pidfile
                os.remove(full_path)
                raise

            os.remove(full_path)
        return wrapped_f

    def create_pid_file(self, fn):
        pidfile = open(fn, "w")
        pidfile.write("%s" % os.getpid())
        pidfile.close()

    def check_pid(self, full_path):
        # if the lockfile is already there then check the PID number
        # in the lock file
        pidfile = open(full_path, "r")
        pidfile.seek(0)
        old_pid = pidfile.readline().strip()
        pidfile.close()

        # Check PID is running, return True if we should exit
        if not old_pid:
            print "Existing PID file %s was empty, can't check whether it is still running!" % self.pidfile_name
            return True
        if os.path.exists("/proc/%s" % old_pid):
            run_time = datetime.datetime.now() - self.modification_date(full_path)
            print "PID file %s exists. You already have an instance of the program running" % self.pidfile_name
            print "It has been running as process %s for %s" % (old_pid,run_time)
            return True
        else:
            print "PID file %s exists but the program is not running" % self.pidfile_name
            print "Removing stale lock file for pid %s" % old_pid
            os.remove(full_path)
            return False

    def modification_date(self, filename):
        t = os.path.getmtime(filename)
        return datetime.datetime.fromtimestamp(t)

