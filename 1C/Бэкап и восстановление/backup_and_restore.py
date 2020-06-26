#!/usr/bin/env python3

#import pyodbc
import time
import os
import psutil
import shutil
import argparse
import pymssql
import subprocess


def read_settings_from_file(path: str):
    assert isinstance(path, str)
    file = open(path, 'r')
    settings = file.read()
    file.close()

    return settings


def get_connection_string(params):
    return 'DRIVER={' + params['driver'] + '};SERVER=' + params['server'] + ';DATABASE=' \
           + params['database'] + ';UID=' + params['uid'] + ';Trusted_Connection=yes'


def get_backup_script(params):
    return "BACKUP DATABASE [" + params['database'] + "] TO  DISK = N'" + params['backup_folder'] \
           + params['database'] + ".bak' WITH NOFORMAT, NOINIT,  NAME = N'" + params['database'] \
           + "-Full database backup', SKIP, NOREWIND, NOUNLOAD, COMPRESSION,  STATS = 10"


def get_block_script(params):
    return "ALTER DATABASE [{0}] SET SINGLE_USER;".format(params['database'])


def get_unblock_script(params):
    return "ALTER DATABASE [{0}] SET MULTI_USER;".format(params['database'])


def get_restore_script(params):
    return "RESTORE DATABASE [{0}] FROM\nDISK = N'{1}{2}.bak' WITH  FILE = 1,\n" \
           "MOVE N'{2}' TO N'{3}{0}.mdf',\nMOVE N'{2}_log' TO N'{3}{0}_log.ldf',\nNOUNLOAD,  REPLACE, " \
           "STATS = 5, RECOVERY;".format(params['database'], params['folder_to'], params['database_from'], params['restore_folder'])


def get_connection(params):
    conn_string = get_connection_string(params)
    
    if params['driver'] == 'SQL Server':
        return pymssql.connect(server=params['server'], user=params['uid'], database=params['database'], password=params['password'], autocommit=True)
    else:
        return pymssql.connect(conn_string, autocommit=True)


def backup_database(params):
    backup_str = "Backup {} ({})"
    
    print(backup_str.format("start", time.ctime()))
    
    conn = get_connection(params)
    cursor = conn.cursor()
    cursor.execute(get_backup_script(params))

    while cursor.nextset():
        time.sleep(5)

    cursor.close()
    conn.close()
    
    print(backup_str.format("stop", time.ctime()))


def restore_database(params):
    restore_str = "Restore database {} ({})"
    
    conn = get_connection(params)
    cursor = conn.cursor()
    
    use_master = "USE [MASTER];"
    block_script = get_block_script(params)
    restore_script = get_restore_script(params)
    unblock_script = get_unblock_script(params)
    
    restore_script = use_master + "\n" + block_script + "\n" + restore_script + "\n" + unblock_script
    
    #print(restore_script)
    print(restore_str.format("start", time.ctime()))
    try:
        cursor.execute(restore_script)
        
        while cursor.nextset():
            pass
    except Exception as e:
        print(e)
    else:
        print(restore_str.format("stop", time.ctime()))
    
    cursor.close()
    conn.close()


def get_params(file_of_settings: str) -> dict:
    params = dict()
    
    settings = read_settings_from_file(file_of_settings)
    
    list_settings = settings.split('\n')

    for param in list_settings:
        list_param = param.split('=')
        params[list_param[0].lower()] = list_param[1]

    return params


def parse_args():
    parser = argparse.ArgumentParser(add_help = True)
    parser.add_argument("-s", "--settings", dest = 'settings', required = True, help = 'Type settings filename')
    return parser.parse_args()


def get_command(params) -> str:
    command = '''"C:\\Program Files\\1cv8\\common\\1cestart.exe" ENTERPRISE
                 /S buh-t\{} /N"{}" /P"{}"
                 /Execute "C:\\scripts\\ChangeUserPassword.epf"'''
    command = command.format(params['database_to'], params['login1c'], params['password1c'])
    return command


def main(settings_path: str):
    gigabyte_size = 1024 ** 3

    full_params = get_params(settings_path)

    params = {'driver': full_params['driver'], 'server': full_params['server_from'],
              'database': full_params['database_from'], 'uid': full_params['uid'],
              'backup_folder': full_params['backup_folder'], 'password': full_params['password']}
    
    backup_database(params)

    backup_name = full_params['database_from'] + '.bak'
    backup_path = full_params['folder_from'] + backup_name
    
    if os.path.exists(backup_path):
        backup_size = os.path.getsize(backup_path) / gigabyte_size
        free_space = psutil.disk_usage(full_params['folder_to']).free / gigabyte_size

        if free_space > backup_size:
            mov_backup_str = "Moving backup file {} ({})"
            
            print(mov_backup_str.format("start", time.ctime()))
            
            dest_path = shutil.move(backup_path, full_params['folder_to'] + backup_name)
            
            print(mov_backup_str.format("stop", time.ctime()), dest_path, sep="\n")

            params['server'] = full_params['server_to']
            params['database'] = full_params['database_to']
            params['database_from'] = full_params['database_from']
            params['folder_to'] = full_params['folder_to']
            params['restore_folder'] = full_params['restore_folder']

            restore_database(params)
            
            delete_str = "Deleting file {} ({})"
            
            print(delete_str.format("start", time.ctime()))
            
            os.remove(dest_path)
            
            print(delete_str.format("stop", time.ctime()))
            
            pswd_change_str = "Password changing {} ({})"
            
            print(pswd_change_str.format("start", time.ctime()))
            
            command_str = get_command(full_params);
            
            os.system(command_str)
            #subprocess.run(command_str)
            
            print(pswd_change_str.format("start", time.ctime()))
        else:
            print("Not enough free spece in folder={}".format(full_params['folder_to']))
    else:
        print("backup_path={} not exists".format(backup_path))


if __name__ == '__main__':
    arguments = parse_args()
    args = arguments.__dict__

    main(args['settings'])

