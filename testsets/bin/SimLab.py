#!/usr/bin/env python
'''
This software was created by United States Government employees at 
The Center for the Information Systems Studies and Research (CISR) 
at the Naval Postgraduate School NPS.  Please note that within the 
United States, copyright protection is not available for any works 
created  by United States Government employees, pursuant to Title 17 
United States Code Section 105.   This software is in the public 
domain and is not subject to copyright. 
'''
import os
import subprocess
import argparse
import time
'''
Use xdotool to simulate a lab being performed, as driven by
a simthis.txt file
'''
def isProcRunning(proc_string):
    ''' return True if given string in ps -ao args '''
    cmd = 'ps -ao args'
    ps = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = ps.communicate()
    for line in output[0].splitlines():
        print('is %s in %s' % (proc_string, line))
        if proc_string in output[0]:
            return True
    return False

class SimLab():
    def __init__(self, lab, logger=None):
        self.sim_path = os.path.abspath(os.path.join('../../../simlab', lab))
        self.current_wid = None
        self.logger = logger
        if not os.path.isdir(self.sim_path):
            return None

    def hasSim(self):
        if os.path.isdir(self.sim_path):
            return True
        else:
            return False

    def getExpectedPath(self):
        return os.path.join(self.sim_path, 'expected')

    def dotool(self, cmd):
        cmd = 'xdotool %s' % cmd
        #print('dotool cmd: %s' % cmd)
        ps = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = ps.communicate()
        if len(output[1]) > 0:
            print output[1]
        return output[0].strip()
    
    
    def searchWindows(self, name):
        wid = None
        while wid is None or len(wid) == 0:
            time.sleep(1)
            cmd = 'search %s' % name
            output=self.dotool(cmd)
            print('searchWindows %s' % cmd)
            parts = output.strip().split()
            if len(parts) == 1:
                print('search out is %s' % output)
                wid = output.rsplit(' ',1)[0].strip()
            elif len(parts)>0:
                last = sorted(parts)[-1]
                #print('last is %s' % last)
                wid = last
            
        return wid
    
    def activate(self, wid):
        self.current_wid = int(wid)
        cmd = 'windowactivate --sync %s' % wid
        self.dotool(cmd)
    
    def typeLine(self, string):
        #cmd = "type --window %d '%s'" % (self.current_wid, string)
        cmd = 'type "%s"' % (string)
        self.dotool(cmd)
        #cmd = 'key Return'
        #self.dotool(cmd)
    
    def commandFile(self, fname):
        full = os.path.join(self.sim_path, fname)
        with open(full) as fh:
            for line in fh:
                if len(line.strip()) > 0:
                    self.typeLine(line)
                    while isProcRunning(line.strip()):
                        print('%s running, wait' % params)
                        time.sleep(1)
                    
    def typeFile(self, fname):
        full = os.path.join(self.sim_path, fname)
        with open(full) as fh:
            for line in fh:
                if len(line.strip()) > 0:
                    self.typeLine(line)
                    time.sleep(1.1)
                else:
                    #print 'sleep 2'
                    time.sleep(2)

    def addFile(self, params, replace=False):
        from_file, to_file = params.split()
        from_file = os.path.join(self.sim_path, from_file) 
        cmd = 'vi %s' % to_file
        self.typeLine(cmd) 
        if replace:
            cmd = "type '9999dd'"
            self.dotool(cmd)
        else:
            self.dotool("type 'G'")
        self.dotool("type 'i'")
        with open(from_file) as fh:
            for line in fh:
                self.typeLine(line)
        self.dotool("key Escape")
        self.dotool("type 'ZZ'")
       
    
    def handleCmd(self, cmd, params):
        if self.logger is not None:
            self.logger.debug('cmd %s  params: %s' % (cmd, params))
        if cmd == 'window':
            wid = self.searchWindows(params)
            self.activate(wid)
        elif cmd == 'type_file':
            self.typeFile(params)
        elif cmd == 'command_file':
            self.commandFile(params)
        elif cmd == 'add_file':
            self.addFile(params)
        elif cmd == 'replace_file':
            self.addFile(params, True)
        elif cmd == 'key':
            send = "key %s" % params
            self.dotool(send)
        elif cmd == 'wait_proc':
            while isProcRunning(params):
                print('%s running, wait' % params)
                time.sleep(1)
 
            
        elif cmd == 'sleep':
            time.sleep(int(params))

    
    def simThis(self):
        fname = os.path.join(self.sim_path, 'simthis.txt')
        if self.logger is not None:
            self.logger.debug('smithThis for %s' % fname)
        with open(fname) as fh:
            for line in fh:
                if line.strip().startswith('#'):
                    continue
                #print line
                cmd, params = line.split(' ', 1)
                #print('cmd: %s params %s' % (cmd, params))
                self.handleCmd(cmd.strip(), params.strip())
                #print('back from handleCmd')


def __main__():
    parser = argparse.ArgumentParser(description='Simulate student performing lab')
    parser.add_argument('labname', help='The lab to simulate')
    args = parser.parse_args()
    lab = args.labname
    simlab = SimLab(lab)
    simlab.simThis() 

if __name__=="__main__":
    __main__()
