import subprocess
import os
import shutil


def _resolve_executable(name):
    """
    Resolve an executable from PATH in a cross-platform way.
    """
    return shutil.which(name)

class BackupManager:
    @staticmethod
    def dump_database(host, user, password, port, database, output_file):
        """
        Creates a database dump using mysqldump.
        """
        # mysqldump -h host -P port -u user -ppassword database > output_file
        # Note: Providing password on command line is insecure but simple for this context.
        # Better to use a config file or environment variable.
        # For now, we'll try to use the environment variable for password to be slightly safer.
        
        env = os.environ.copy()
        env['MYSQL_PWD'] = password
        
        dump_exec = _resolve_executable('mysqldump')
        if not dump_exec:
            return (
                False,
                "mysqldump not found in PATH. Install MySQL client tools and add the MySQL bin folder to PATH."
            )

        cmd = [
            dump_exec,
            '-h', host,
            '-P', str(port),
            '-u', user,
            database
        ]
        
        try:
            with open(output_file, 'w') as f:
                subprocess.run(cmd, env=env, stdout=f, stderr=subprocess.PIPE, check=True)
            return True, "Dump successful"
        except subprocess.CalledProcessError as e:
            return False, f"Dump failed: {e.stderr.decode()}"
        except FileNotFoundError:
            return False, "mysqldump executable not found. Check your PATH configuration."
        except Exception as e:
            return False, str(e)

    @staticmethod
    def restore_database(host, user, password, port, database, input_file):
        """
        Restores a database from a dump file using mysql.
        """
        # mysql -h host -P port -u user -ppassword database < input_file
        
        env = os.environ.copy()
        env['MYSQL_PWD'] = password
        
        mysql_exec = _resolve_executable('mysql')
        if not mysql_exec:
            return (
                False,
                "mysql not found in PATH. Install MySQL client tools and add the MySQL bin folder to PATH."
            )

        cmd = [
            mysql_exec,
            '-h', host,
            '-P', str(port),
            '-u', user,
            database
        ]
        
        try:
            with open(input_file, 'r') as f:
                subprocess.run(cmd, env=env, stdin=f, stderr=subprocess.PIPE, check=True)
            return True, "Restore successful"
        except subprocess.CalledProcessError as e:
            return False, f"Restore failed: {e.stderr.decode()}"
        except FileNotFoundError:
            return False, "mysql executable not found. Check your PATH configuration."
        except Exception as e:
            return False, str(e)
