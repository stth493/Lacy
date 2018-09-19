import sys
import telnetlib
import datetime
import time
import socket
import ipaddress
#import openpyxl

admin = 'admin'
adpro = 'adpro'
password = "ViOLinNET"
enable = 'enable'
conft = 'configure terminal'

show_run ={
        ' Omni-OS6450-10' : ['show configuration snapshot'],
        ' T-Marc 280' : ['terminal length 0','show running-config'],
        ' T-Marc 340' : ['terminal length 0','show running-config'],
        ' T-Marc 380' : ['terminal length 0','show running-config'],
        ' S5720-12TP' : ['screen-length 512 temporary','display current-configuration' ],
        'Apresia13000' : 'login: ',
        'Apresia13200' : [conft,'terminal length 0','show running-config'],
        'Apresia15000' : 'login: ',
        'Apresia18005' : 'login: ',
        'Apresia18008' : 'login: ',
        'Apresia26K' : 'login: '    
    }

end_char ={
        ' Omni-OS6450-10' : '! TWAMP :',
        ' T-Marc 280' : '\nend\n!',
        ' T-Marc 340' : '!\nend\n!',
        ' T-Marc 380' : '!\nend\n!',        
        ' S5720-12TP' : '#\nreturn',
        'Apresia13200' : '!\nend',        
          
    }    

login_prompt ={
        ' Omni-OS6450-10' : 'login : ',
        ' T-Marc 280' : 'Password:',        
        ' T-Marc 340' : 'Password:',
        ' T-Marc 380' : 'Password:',        
        ' S5720-12TP' : 'Username:',
        'Apresia13000' : 'login: ',
        'Apresia13200' : 'login: ',
        'Apresia15000' : 'login: ',
        'Apresia18005' : 'login: ',
        'Apresia18008' : 'login: ',
        'Apresia26K' : 'login: '
    }

save_command ={
        ' Omni-OS6450-10' : ['write memory','copy working certified'],
        ' T-Marc 280' : ['write memory'],
        ' T-Marc 340' : ['write memory'],
        ' T-Marc 380' : ['write memory'],
        ' S5720-12TP' : ['save','Y'],
        'Apresia13000' : ['write memory'],
        'Apresia13200' : ['write memory'],
        'Apresia15000' : ['write memory'],
        'Apresia18005' : ['write configuration built-in','y'],
        'Apresia18008' : ['write configuration built-in','y'],
        'Apresia26K' : ['write configuration built-in','y']
    }

login_command ={
        ' Omni-OS6450-10' : [admin,password],
        ' T-Marc 280' : [password, enable, password], 
        ' T-Marc 340' : [password, enable, password], 
        ' T-Marc 380' : [password, enable, password],         
        ' S5720-12TP' : [admin,password],
        'Apresia13000' : [adpro,password,enable],
        'Apresia13200' : [adpro,password,enable],
        'Apresia15000' : [adpro,password,enable],
        'Apresia18005' : [adpro,password],
        'Apresia18008' : [adpro,password],
        'Apresia26K' : [adpro,password]
    }
     

class Telnet(telnetlib.Telnet,object):
    if sys.version > '3':
        def read_until(self,expected,timeout=None):
            expected = bytes(expected, encoding='utf-8')
            received = super(Telnet,self).read_until(expected,timeout)
            return str(received, encoding='utf-8')

        def write(self,buffer):
            buffer = bytes(buffer, encoding='utf-8')
            super(Telnet,self).write(buffer)

        def expect(self,list,timeout=None):
            for index,item in enumerate(list):
                list[index] = bytes(item, encoding='utf-8')
            match_index, match_object, match_text = super(Telnet,self).expect(list,timeout)
            return match_index, match_object, str(match_text, encoding='utf-8')


def telnetlogin(session,model):
    
    session.read_until(login_prompt.get(model))
    
    for command in login_command.get(model):
        session.write(command + '\n')
        time.sleep(1)
        
    return session


def getinput():
    
    while True:
        host = input('\nEnter IP address of switch :')
        try:
            ipaddress.ip_address(host)
        except:
            print('\nYou enter incorrect IPv4 format\n')
            continue
            
        port = input('Enter access port [x/x/x] or [x/x] :')
        
        speed = input('Enter new speed [Mbps] :')
        if speed.isdigit():
            break
        else:
            print('\nYou did not enter a digit !\n')
            continue
    
    return host,port,speed


def getconfirm():
    
    print('\n Are you sure these command is correct ? : ')
    print('\n 1. Correct. I want to deploy now. \n')
    print(' 2. Correct. I want to schedule this task. \n')
    print(' 3. Incorrect. Do not deploy these commands. \n')
    
    confirm = input('Enter your choice : ')
    if confirm == '1':
        return True
    if confirm == '2':
        schedule_task()
        return True
    else:
        return False

def telco280_confspd(session,accport,speed):
    
    command =[]
    telcospeed = str(int(speed) * 1030)
    isaccport = False   #Check if it is the correct port
    qosrx = False       
    qostx = False

    session.write('terminal length 0 \n')
    session.write('show run port \n')

    for line in session.read_until('end', timeout = 2).splitlines():
        if line.startswith('interface ' + accport):
            isaccport = True
            
        elif line.startswith('name '):
            name =  line.strip().split()
            
        elif line.startswith('qos rx rate-limit') and isaccport:
            qosrx = True
            
        elif line.startswith('qos tx shaper rate') and isaccport:
            qostx = True
            break       #Got all information. break for loop            
            
        elif line.startswith('!') and isaccport and not qosrx and not qostx:
            return False    #The port do not have QoS-rx or QoS-tx
                                
    command.append(conft + '\n')
    command.append('interface {}\n'.format(accport))
    command.append('{} {} {} {}Mb \n'.format(name[0],name[1],name[2],speed))    #Change port description
    
    command.append('qos rx rate-limit priority txq0 {}K 13312K \n'.format(telcospeed))
    command.append('qos tx shaper rate {}K\n'.format(telcospeed))
    
    command.append('end\n')
    return command


def telco340_confspd(session,accport,speed):
    
    command =[]

    telcospeed = str(int(speed) * 1030)
    isaccport = False   #Check if it is the correct port
    np = None           
    accgroup = None

    session.write('terminal length 0 \n')
    session.write('show run \n')

    for line in session.read_until(end_char.get(' T-Marc 340'), timeout = 2).splitlines():
        if line.startswith('interface ' + accport):
            isaccport = True
            
        elif line.startswith('name ') and isaccport:
            name =  line.strip().split()
                
        elif line.startswith('qos-network-policy') and isaccport:
            np = line
            
        elif line.startswith('mac access-group') and isaccport:
            accgroup = line
            break       #Got all information. break for loop
        
        elif line.startswith('!') and isaccport and not np and not accgroup:
            return False    #The port do not have Rate-limit or QoS
                                
    command.append(conft + '\n')
    command.append('interface ' + accport + '\n')
    command.append('{} {} {} {}Mb\n'.format(name[0],name[1],name[2],speed))    #Change port description
    
    if np != None:
        command.append('no qos-network-policy\n')
        command.append('exit\n')
        command.append('qos\n')
        command.append('shaper {} {}K 16M\n'.format(np[-1],telcospeed))
        command.append('exit\n')
        command.append('interface ' + accport + '\n')
        command.append(np + '\n')
    else:
        print('\n\n[Warning] There is no QoS on port {} !!'.format(accport))
    if accgroup != None:
        command.append(accgroup + '\n')
        command.append('rate-limit single-rate {}K 16M' '\n'.format(telcospeed))
        
    else:
        print('\n\nThere is no Rate-limit on port {} !! Please configure it manually'.format(accport))
        return False
    
    command.append('end\n')
    
    return command
        
def omni_confspd(session,accport,speed):
    
    command = []
    name = None
        
    session.write('show configuration snapshot\n')
    for line in session.read_until('! Udld :\n', timeout = 2).splitlines():
        if line.startswith('interfaces ' + accport + ' alias'):
            name = line.replace('"','').split()
    
    if name != None:
        command.append('{} {} {} "{} {} {}Mb"\n'.format(name[0],name[1],name[2],name[3],name[4],speed))    

    command.append('qos port {} maximum egress-bandwidth {}M maximum ingress-bandwidth {}M\n'.format(accport,str(speed),str(speed),))
    command.append('qos apply \n')

    return command

        
def huawei_confspd(session,accport,speed):

    command = []
    huaweispeed = str(int(speed) * 1024)
    istp = False
    tp = None

    session.write('screen-length 512 temporary \n')
    session.write('display current-configuration interface GigabitEthernet {}\n'.format(accport))

    for line in session.read_until('return', timeout = 2).splitlines():
        if line.startswith(' description'):
            name =  line.strip().split()

        elif line.strip().startswith('traffic-policy'):
            tp = line.split()[1]
            break

    session.write('display current-configuration \n')
    time.sleep(0.5)
    
    for line in session.read_until('return', timeout = 2).splitlines():
        line = line.strip()

        if line == ('traffic policy '+ tp):
            istp = True
            continue
        elif line.startswith('classifier') and istp:
            bh = line.split()[3]  
            break

    command.append('system-view \n')
    if name != None:
        command.append('interface GigabitEthernet {}\n'.format(accport))
        command.append('{} {} {} {}Mb \n'.format(name[0],name[1],name[2],speed))
        command.append('quit \n')
    
    if tp != None:
        command.append('traffic behavior {}\n'.format(bh))
        command.append('car cir {} pir {} cbs 128000 pbs 128000 green pass yellow pass red discard \n'.format(huaweispeed,huaweispeed))        
    else:
        command.append('return \n')    
        return False
    command.append('return \n')

    return command

def hitachi132k_confspd(session,accport,speed):

    command = []
    hitchispeed = str(int(speed) * 1000)
    isaccport = False   #Check if it is the correct port        
    isshaping = False
    
    session.write('show running-config \n')
        
    for line in session.read_until(end_char.get('Apresia13200'), timeout = 2).splitlines():
        if line.startswith('interface port ' + accport):
            isaccport = True
            
        elif line.startswith(' description ') and isaccport:
            name =  line.strip().split()
            
        elif line.startswith(' switchport mode trunk') and isaccport:
            return False    #The port is trunk port. Not allow using Lacy to configure    
            
        elif line.startswith(' egress-shape ') and isaccport:
            isshaping = True
            break       #Got all information. break for loop
        
        elif line.startswith('!') and isaccport and not isshaping:
            return False    #The port do not have Rate-limit or QoS        
            
    command.append('interface port {}\n'.format(accport))
    command.append('{} {} {} {}Mb\n'.format(name[0],name[1],name[2],speed))    #Change port description      
        
    command.append('egress-shape {} 131072\n'.format(hitchispeed))
    command.append('end \n')

    return command

def get_backup(session,model,backup):
    
    for command in show_run.get(model):
        session.write(command + '\n')
        time.sleep(1)
    for line in session.read_until(end_char.get(model),timeout = 2).splitlines():
        backup.write(line+'\n')

def print_command(commandfile):
    
    print('\n Please re-view following command before confirm \n\n')
    with open (commandfile,'r') as command:
        for line in command:
            print(line)


def deploy_command(session,commandfile):
    
    with open (commandfile,'r') as command:
        for line in command:
            session.write(line + '\n')
            time.sleep(0.5)
            
def schedule_task():
    
    timeformat = "%H:%M"
    while True:
        '''
        1st Loop to verify user time input before go scheduling
        '''
        schedule = input("\n\n\t\tPlease enter time to deploy [HH:MM] : \n\n")
        try:
            datetime.datetime.strptime(schedule, timeformat)
            print("\nYour task is already scheduled. Do not close me before " + schedule +'\n')
            break
        except ValueError:
            print("\nYou did not entered expected time format")
            
    while True:
        '''
        2nd Loop is run until time reached
        '''
        if schedule == time.strftime(timeformat):
            break

def save_config(model):

    command =[]
    for cmd in save_command.get(model):
        command.append(cmd)
        if model == ' Omni-OS6450-10':
            time.sleep(4)
    return command
    

def save_alldevice(hostfile):
    return
    #sheet = openpyxl.load_workbook(hostfile).active        
    
    #for i in range(sheet.max_row):            
    #    if(sheet.cell(row=i+2, column=1).value):
    #        host = sheet.cell(row=i+2, column=1).value.strip()
    #        model = sheet.cell(row=i+2, column=4).value
                
    #        tn = Telnet(host,timeout=2)
                
    #        telnetlogin(tn,model)
                                           
    #        save_config(tn,model)
                
    #        tn.close()

def main():
    
    user = input('\n\n\nPlease enter your name : \n\n')
    
    backupfile = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H.%M_by_' + user+'_backup.txt')
    commandfile = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H.%M_by_' + user+'_command.txt')
    #logging.basicConfig(filename=datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H.%M_by_' + user + '.txt'),level=logging.INFO)
    #logging.Formatter('%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
       
    while True:
        print('\n')
        print('Welcome to Provisioning Automate Configuration Tool. \n\n')
        print(' 1. Configure T-Marc 280 Speed. \n')
        print(' 2. Configure T-Marc 340 and T-Marc 380 Speed. \n')        
        print(' 3. Configure OmniSwitch OS6450-10 speed. \n')
        print(' 4. Configure Huawei S5720-12TP speed. \n')
        print(' 5. Configure Hitachi 13.2K speed. \n')
        print(' 6. Save configuration on all devices in the network. \n')
        choice = input('Please enter your choice : \n\n')
            
        if choice == '1':
            info = getinput()
            '''
            info[0] = IP address
            info[1] = Access port
            info[2] = Speed
            '''
            try:
                tn = Telnet(info[0],timeout=2)
            except socket.timeout:
                print('\nUnable to connect to host ! \n')
                time.sleep(2)
                continue
                
            session = telnetlogin(tn,' T-Marc 280')
            with open (backupfile,'a') as backup:
                get_backup(session,' T-Marc 280',backup)
                    
            with open (commandfile,'a') as command:
                '''
                Start creating command file
                '''
                try:      
                    for line in telco280_confspd(session,info[1],info[2]):
                        command.write(line)
                except:
                    print('\n\nThere is no QoS and Rate-limit on port ' + info[1] + ' !! Please configure it manually')
                    time.sleep(5)
                    break                                                
                        
                for line in save_config(' T-Marc 280'):
                    command.write(line + '\n')
                    
                command.write('quit\n')
            
            print_command(commandfile)        
            if getconfirm():
                deploy_command(session,commandfile)
                print('\n\nDone krub !! Please re-check the result again')
            else:
                print('\nIf commands are not correct, please configure it manually\n')
                break
            
            session.close()
            time.sleep(5)
            break

        elif choice == '2':
            info = getinput()
            '''
            info[0] = IP address
            info[1] = Access port
            info[2] = Speed
            '''
            try:
                tn = Telnet(info[0],timeout=2)
            except socket.timeout:
                print('\nUnable to connect to host ! \n')
                time.sleep(2)
                continue
            
            session = telnetlogin(tn,' T-Marc 340')
            with open (backupfile,'a') as backup:
                get_backup(session,' T-Marc 340',backup)
            with open (commandfile,'a') as command:  
                '''
                Start creating command file
                '''
                try:      
                    for line in telco340_confspd(session,info[1],info[2]):
                        command.write(line)    
                except:
                    print('\n\nThere is no QoS and Rate-limit on port ' + info[1] + ' !! Please configure it manually')
                    time.sleep(5)
                    break                                                
                        
                for line in save_config(' T-Marc 340'):
                    command.write(line + '\n')
                    
                command.write('quit\n')
            
            print_command(commandfile)        
            if getconfirm():
                deploy_command(session,commandfile)
                print('\n\nDone krub !! Please re-check the result again')
            else:
                print('\nIf commands are not correct, please configure it manually\n')
                break
            
            session.close()
                
            time.sleep(5)
            break         
        
        elif choice == '3':
            info = getinput()
            '''
            info[0] = IP address
            info[1] = Access port
            info[2] = Speed
            '''
            try:
                tn = Telnet(info[0],timeout=2)
            except socket.timeout:
                print('\nUnable to connect to host ! \n')
                time.sleep(2)
                continue
                
            session = telnetlogin(tn,' Omni-OS6450-10')
            with open (backupfile,'a') as backup:
                get_backup(session,' Omni-OS6450-10',backup)
            with open (commandfile,'a') as command:  
                '''
                Start creating command file
                '''
                for line in omni_confspd(session,info[1],info[2]):
                    command.write(line)    
                       
                for line in save_config(' Omni-OS6450-10'):
                    command.write(line + '\n')
                    
                command.write('quit\n')

            print_command(commandfile)
            if getconfirm():
                deploy_command(session,commandfile)
                print('\n\nDone krub !! Please re-check the result again')
            else:
                print('\nIf commands are not correct, please configure it manually\n')
                
            session.close()
                
            time.sleep(5)
            break         
        
        elif choice == '4':
            info = getinput()
            '''
            info[0] = IP address
            info[1] = Access port
            info[2] = Speed
            '''
            try:
                tn = Telnet(info[0],timeout=2)
            except socket.timeout:
                print('\nUnable to connect to host ! \n')
                time.sleep(2)
                continue
                
            session = telnetlogin(tn,' S5720-12TP')
            with open (backupfile,'a') as backup:
                get_backup(session,' S5720-12TP',backup)
            with open (commandfile,'a') as command:  
                '''
                Start creating command file
                '''
                for line in huawei_confspd(session,info[1],info[2]):
                    command.write(line)                                           
                        
                for line in save_config(' T-Marc 340'):
                    command.write(line + '\n')
                    
                command.write('quit\n')
            
            print_command(commandfile)        
            if getconfirm():
                deploy_command(session,commandfile)
                print('\n\nDone krub !! Please re-check the result again')
            else:
                print('\nIf commands are not correct, please configure it manually\n')
                
            session.close()
                
            time.sleep(5)
            break         
        
        elif choice == '5':
            info = getinput()
            '''
            info[0] = IP address
            info[1] = Access port
            info[2] = Speed
            '''
            try:
                tn = Telnet(info[0],timeout=2)
            except socket.timeout:
                print('\nUnable to connect to host ! \n')
                time.sleep(2)
                continue

            session = telnetlogin(tn,'Apresia13200')
            with open (backupfile,'a') as backup:
                get_backup(session,'Apresia13200',backup)
            with open (commandfile,'a') as command:  
                '''
                Start creating command file
                '''        
                try:
                    for line in hitachi132k_confspd(session,info[1],info[2]):
                        command.write(line)
                except:
                    print('\nThere is no egress-shape on port ' + info[1] + ' or this port is trunk port \n')
                    time.sleep(5)
                    break
                    
                for line in save_config('Apresia13200'):
                    command.write(line + '\n')

                command.write('quit\n')
                
            print_command(commandfile)        
            if getconfirm():
                deploy_command(session,commandfile)
                print('\n\nDone krub !! Please re-check the result again')
            else:
                print('\nIf commands are not correct, please configure it manually\n')
                
            session.close()
                
            time.sleep(5)
            break                   
        
        elif choice == '6':
            print('\n\nUnder Construction krub !! \n')
            time.sleep(4)
            break
        
        else:
            continue
        
main()
