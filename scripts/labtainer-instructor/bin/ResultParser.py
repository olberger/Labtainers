#!/usr/bin/env python

# ResultParser.py
# Description: * Read results.config
#              * Parse stdin and stdout files based on results.config
#              * Create a json file

import datetime
import json
import glob
import os
import re
import sys
import time
import MyUtil

UBUNTUHOME = "/home/ubuntu/"
logfilelist = []
exec_proglist = []
containernamelist = []
stdinfnameslist = []
stdoutfnameslist = []
timestamplist = {}
line_types = ['CONTAINS', 'LINE', 'STARTSWITH', 'NEXT_STARTSWITH', 'HAVESTRING', 'LINE_COUNT']
just_field_type = ['LINE_COUNT']
def ValidateTokenId(each_value, token_id):
    if token_id != 'ALL' and token_id != 'LAST':
        try:
            int(token_id)
        except ValueError:
            sys.stderr.write("ERROR: results.config line (%s)\n" % each_value)
            sys.stderr.write("ERROR: results.config has invalid token_id\n")
            sys.exit(1)

def findLineIndex(values):
    for ltype in line_types:
        if ltype in values:
            return values.index(ltype)

    return None
    
def ValidateConfigfile(labidname, each_key, each_value):
    valid_field_types = ['TOKEN', 'PARENS', 'QUOTES', 'SLASH', 'LINE_COUNT', 'CONTAINS']
    if not MyUtil.CheckAlphaDashUnder(each_key):
        sys.stderr.write("ERROR: Not allowed characters in results.config's key (%s)\n" % each_key)
        sys.exit(1)
    values = []
    # expecting either:
    # 1. - [ stdin | stdout ] : [<field_type>] : <field_id> :  <line_type1> : <line_id>
    #    field_type = (a valid_field_type defined above)
    #    field_value is a numeric identifying the nth field of the given type
    #    line_type1 = LINE | STARTSWITH | NEXT_STARTSWITH | HAVESTRING
    #    line_id is a number if the type is LINE, or a string if the type is STARTSWITH/HAVESTRING
    # 2. - [ stdin | stdout ] : <line_type2> : <line_id>
    #    line_type2 = CONTAINS
    #    line_id is a string if the type is CONTAINS

    # NOTE: Split using ' : ' - i.e., "space colon space"
    values = [x.strip() for x in each_value.split(' : ')]
    #print values
    numvalues = len(values)
    #print "numvalues is (%d)" % numvalues
    if numvalues < 3 and values[1] not in just_field_type:
        sys.stderr.write("ERROR: results.config contains unexpected value (%s) format\n" % each_value)
        sys.exit(1)
    line_at = findLineIndex(values)
    if line_at is None:
        sys.stderr.write('No line_type in %s\n' % each_value)
        exit(1)
    num_splits = line_at+1
    #print "line_at is (%d) and num_splits is (%d)" % (line_at, num_splits)
     
    # Split into either four or five parts (for line_type1) or three parts (for line_type2)
    # NOTE: Split using ' : ' - i.e., "space colon space"
    values = [x.strip() for x in each_value.split(' : ', num_splits)]

    # Make sure it is 'stdin' or 'stdout'
    newprogname_type = values[0].strip()
    # <cfgcontainername>:<exec_program>.<type>
    if ':' in newprogname_type:
        cfgcontainername, progname_type = newprogname_type.split(':', 1)
    else:
        cfgcontainername = ""
        progname_type = newprogname_type
    # Construct proper containername from cfgcontainername
    if cfgcontainername == "":
        containername = ""
    else:
        containername = labidname + "." + cfgcontainername + ".student"

    if containername != "":
        if containername not in containernamelist:
            containernamelist.append(containername)
    # Use rsplit() here because exec_program may have '.' as part of name
    (exec_program, targetfile) = progname_type.rsplit('.', 1)
    # No longer restricted to stdin/stdout filenames anymore
    if (targetfile != "stdin") and (targetfile != "stdout"):
        # Not stdin/stdout - add the full name
        if progname_type not in logfilelist:
            logfilelist.append(progname_type)
    else:
        if exec_program not in exec_proglist:
            exec_proglist.append(exec_program)
    #    sys.stderr.write("ERROR: results.config line (%s)\n" % each_value)
    #    sys.stderr.write("ERROR: results.config uses not stdin or sdout\n")
    #    sys.exit(1)

    # If line_type1 (line_at != 1) - verify token id
    if line_at != 1:
        token_index = 1
        if line_at == 3:
            token_index = 2
        ValidateTokenId(each_value, values[token_index])

    if values[line_at] == 'LINE':
        try:
            int(values[line_at+1])
        except:
            sys.stderr.write('Expected integer following LINE type, got %s in %s' % (values[line_at+1], each_value))
            exit(1)

    # Validate <field_type> - if exists (i.e., line_at == 3)
    #                       - because <field_type> is optional
    if line_at == 3:
        field_type = values[1].strip()
        if field_type not in valid_field_types:
            sys.stderr.write("ERROR: results.config line (%s)\n" % each_value)
            sys.stderr.write("ERROR: results.config invalid field_type\n")
            sys.exit(1)

    return 0

def getToken(linerequested, field_type, token_id):
        #print "Line requested is (%s)" % linerequested
        if linerequested == "NONE":
            token = "NONE"
        else:
            linetokens = {}
            if field_type == 'PARENS':
                myre = re.findall('\(.+?\)', linerequested)
                linetokenidx = 0
                for item in myre:
                    #print "linetokenidx = %d" % linetokenidx
                    linetokens[linetokenidx] = item[1:-1]
                    linetokenidx = linetokenidx + 1
                numlinetokens = len(linetokens)
            elif field_type == 'QUOTES':
                myre = re.findall('".+?"', linerequested)
                linetokenidx = 0
                for item in myre:
                    #print "linetokenidx = %d" % linetokenidx
                    linetokens[linetokenidx] = item[1:-1]
                    linetokenidx = linetokenidx + 1
                numlinetokens = len(linetokens)
            elif field_type == 'SLASH':
                myre = linerequested.split('/')
                linetokenidx = 0
                for item in myre:
                    #print "linetokenidx = %d" % linetokenidx
                    linetokens[linetokenidx] = item
                    linetokenidx = linetokenidx + 1
                numlinetokens = len(linetokens)
            else:
                # field_type == "TOKEN"
                linetokens = linerequested.split()
                numlinetokens = len(linetokens)
            if token_id == 'ALL':
                token = linerequested.strip()
            elif token_id == 'LAST':
                token = linetokens[numlinetokens-1]
            else:
                #print linetokens
                # make sure tokenno <= numlinetokens
                tokenno = int(token_id)
                #print "tokenno = %d" % tokenno
                if tokenno > numlinetokens:
                    token = "NONE"
                    #print "setting result to none tokenno > numlinetokens"
                else:
                    token = linetokens[tokenno-1]
        return token

def handleConfigFileLine(labidname, line, nametags, studentlabdir, container_list, timestamppart):
    retval = True
    targetlines = None
    #print('line is %s' % line)
    (each_key, each_value) = line.split('=', 1)
    each_key = each_key.strip()

    #print each_key
    # Note: config file has been validated
    # Split into four parts or five parts
    # NOTE: Split using ' : ' - i.e., "space colon space"
    values = [x.strip() for x in each_value.split(' : ')]
    line_at = findLineIndex(values)
    num_splits = line_at+1
    # NOTE: Split using ' : ' - i.e., "space colon space"
    values = [x.strip() for x in each_value.split(' : ', num_splits)]
    newtargetfile = values[0].strip()
    #print('newtargetfile is %s' % newtargetfile)
    # <cfgcontainername>:<exec_program>.<type>
    containername = None
    if ':' in newtargetfile:
        cfgcontainername, targetfile = newtargetfile.split(':', 1)
    else:
        ''' default to first container? '''
        #print('first cont is %s' % container_list[0])
        containername = container_list[0]
        targetfile = newtargetfile
    # Construct proper containername from cfgcontainername
    if containername is None:
        containername = labidname + "." + cfgcontainername + ".student"
    #print('targetfile is %s containername is %s' % (targetfile, containername))

    if containername is not None and containername not in container_list:
        print "Config line (%s) containername %s not in container list (%s), skipping..." % (line, containername, str(container_list))
        # set nametags - value pair to NONE
        #nametags[mycontainername][each_key] = "NONE"
        nametags[each_key] = "NONE"
        return False

    command = values[line_at].strip()
    # field_type - if exists (because field_type is optional)
    #              has been validated to be one of the valid field types.
    #              
    # if it does not exists, default field_type is TOKEN
    if line_at == 3:
        field_type = values[1].strip()
    else:
        field_type = "TOKEN"
    # command has been validated to be either 'LINE' or 'STARTSWITH' or 'HAVESTRING'
    token_index = 1
    if line_at == 3:
        token_index = 2
    token_id = values[token_index].strip()
    if command == 'LINE':
        lineno = int(values[line_at+1].strip())
    elif command not in just_field_type:
        # command = 'STARTSWITH': or 'HAVESTRING'
        lookupstring = values[line_at+1].strip()

    result_home = '%s/%s/%s' % (studentlabdir, containername, ".local/result/")
    if timestamppart is not None:
        targetfname = '%s%s.%s' % (result_home, targetfile, timestamppart)
    else:
        ''' descrete file, no timestamp. '''
        if targetfile.startswith('~/'):
            targetfile = targetfile[2:]
        targetfname = os.path.join(studentlabdir, containername, targetfile)
    #print "targetfname is (%s)" % targetfname
    #print "labdir is (%s)" % studentlabdir

    if not os.path.exists(targetfname):
        # If file does not exist, treat as can't find token
        token = "NONE"
        #sys.stderr.write("ERROR: No %s file does not exist\n" % targetfname)
        #sys.exit(1)
        return False
    else:
        # Read in corresponding file
        targetf = open(targetfname, "r")
        targetlines = targetf.readlines()
        targetf.close()
        targetfilelen = len(targetlines)
        #print('targetfname %s' % targetfname)

        # command has been validated to be either 'LINE' or 'STARTSWITH' or 'HAVESTRING'
        linerequested = "NONE"
        if command == 'LINE':
            # make sure lineno <= targetfilelen
            if lineno <= targetfilelen:
                linerequested = targetlines[lineno-1]
        elif command == 'HAVESTRING':
            # command = 'HAVESTRING':
            found_lookupstring = False
            for currentline in targetlines:
                if found_lookupstring == False:
                    if lookupstring in currentline:
                        found_lookupstring = True
                        linerequested = currentline
                        break
            # If not found - set to NONE
            if found_lookupstring == False:
                linerequested = "NONE"
        elif command == 'LINE_COUNT':
            tagstring = str(targetfilelen)
            nametags[each_key] = tagstring
            #print('tag string is %s for eachkey %s' % (tagstring, each_key))
            return True

        elif command == 'CONTAINS':
            if token_id == 'CONTAINS':
                ''' search entire file, vice searching for line '''
                remain = line.split(command,1)[1]
                remain = remain.split(':', 1)[1].strip()
                tagstring = 'False'
                for currentline in targetlines:
                    #print('look for <%s> in %s' % (remain, currentline))
                    if remain in currentline:
                        tagstring = 'True'
                        break 
                nametags[each_key] = tagstring
                #print('tag string is %s for eachkey %s' % (tagstring, each_key))
                return True
            else:
                found_lookupstring = False
                for currentline in targetlines:
                    if found_lookupstring == False:
                        if lookupstring in currentline:
                            found_lookupstring = True
                            linerequested = currentline
                            #print('line requested is %s' % linerequested)
                            break
                # If not found - set to NONE
                if found_lookupstring == False:
                    linerequested = "NONE"


        elif command == 'STARTSWITH':
            #print('is startswith')
            found_lookupstring = False
            for currentline in targetlines:
                if found_lookupstring == False:
                    if currentline.startswith(lookupstring):
                        found_lookupstring = True
                        linerequested = currentline
                        #print('line requested is %s' % linerequested)
                        break
            # If not found - set to NONE
            if found_lookupstring == False:
                linerequested = "NONE"
        elif command == 'NEXT_STARTSWITH':
            found_lookupstring = False
            prev_line = None
            for currentline in targetlines:
                if found_lookupstring == False:
                    if currentline.startswith(lookupstring) and prev_line is not None:
                        found_lookupstring = True
                        linerequested = prev_line
                        break
                prev_line = currentline
            # If not found - set to NONE
            if found_lookupstring == False:
                linerequested = "NONE"
        else:
            print('ERROR: unknown command %s' % command)
            exit(1)

        token = getToken(linerequested, field_type, token_id)


    #print token
    if token == "NONE":
        tagstring = "NONE"
    else:
        tagstring = token

    # set nametags - value pair
    nametags[each_key] = tagstring
    return True


def ParseConfigForFile(studentlabdir, labidname, configfilelines, 
                       outputjsonfname, container_list, timestamppart, end_time):
    '''
    Invoked for each timestamp to parse results for that timestamp.
    Each config file line is assessed against each results file that corresponds
    to the given timestamp.  If timestamp is None, then look at all files that
    match the name found in the configuration file line, (e.g., for log files
    without timestamps.)
    '''
    #print('in ParseConfigForFile outputjsonfile: %s timestamppart %s' % (outputjsonfname, timestamppart))
    nametags = {}
    got_one = False
    for line in configfilelines:
        linestrip = line.rstrip()
        if linestrip is not None and not linestrip.startswith('#') and len(line.strip())>0:
            got_one = got_one | handleConfigFileLine(labidname, linestrip, nametags, studentlabdir, container_list, timestamppart)

    if end_time is not None:
        program_end_time = end_time
    else:
        program_end_time = 'NONE'
    if got_one:
        nametags['PROGRAM_ENDTIME'] = program_end_time
        #print nametags
        #print('will dump to %s' % outputjsonfname)
        jsonoutput = open(outputjsonfname, "w")
        for key in nametags:
            old = nametags[key]
            new = repr(old)
            nametags[key] = new
            #print('nametags[%s] = %s' % (key, new))
        try:
            jsondumpsoutput = json.dumps(nametags, indent=4)
        except:
            print('json dumps failed on %s' % nametags)
            exit(1)
        #print('dumping %s' % str(jsondumpsoutput))
        jsonoutput.write(jsondumpsoutput)
        jsonoutput.write('\n')
        jsonoutput.close()

def ParseStdinStdout(studentlabdir, container_list, instructordir, labidname):

    ''' process all results files (ignore name of function) for a student.  These
        are distrbuted amongst multiple containers, per container_list.
    '''
    configfilename = '%s/.local/instr_config/%s' % (UBUNTUHOME, "results.config")
    configfile = open(configfilename)
    configfilelines = configfile.readlines()
    configfile.close()
    jsonoutputfilename = labidname
    #print("ParseStdinStdout: jsonoutputfilename is (%s) studentlabdir %s" % (jsonoutputfilename, studentlabdir))
  
    timestamplist.clear()

    del logfilelist[:]
    del exec_proglist[:]
    del containernamelist[:]
    del stdinfnameslist[:]
    del stdoutfnameslist[:]


    for line in configfilelines:
        linestrip = line.rstrip()
        if linestrip:
            if not linestrip.startswith('#'):
                #print "Current linestrip is (%s)" % linestrip
                (each_key, each_value) = linestrip.split('=', 1)
                each_key = each_key.strip()
                ValidateConfigfile(labidname, each_key, each_value)
        #else:
        #    print "Skipping empty linestrip is (%s)" % linestrip

    #print "exec_proglist is: "
    #print exec_proglist
    #print "logfilelist is: "
    #print logfilelist
    OUTPUTRESULTHOME = '%s/%s' % (studentlabdir, ".local/result/")

    if not os.path.exists(OUTPUTRESULTHOME):
        os.makedirs(OUTPUTRESULTHOME)

    '''
    A round-about-way of getting all time stamps
    '''
    for mycontainername in container_list:
        RESULTHOME = '%s/%s/%s' % (studentlabdir, mycontainername, ".local/result/")
        if not os.path.exists(RESULTHOME):
            ''' expected, some containers don't have local results '''
            #print('result directory %s does not exist' % RESULTHOME)
            pass
            
        for exec_prog in exec_proglist:
            stdinfiles = '%s%s.%s.' % (RESULTHOME, exec_prog, "stdin")
            stdoutfiles = '%s%s.%s.' % (RESULTHOME, exec_prog, "stdout")
            #print stdinfiles
            #print stdoutfiles
            globstdinfnames = glob.glob('%s*' % stdinfiles)
            if globstdinfnames != []:
                #print "globstdinfname list is "
                #print globstdinfnames
                for stdinfnames in globstdinfnames:
                    #print stdinfnames
                    stdinfnameslist.append(stdinfnames)
            globstdoutfnames = glob.glob('%s*' % stdoutfiles)
            if globstdoutfnames != []:
                #print "stdoutfnameglob list is "
                #print globstdoutfnames
                for stdoutfnames in globstdoutfnames:
                    #print stdoutfnames
                    stdoutfnameslist.append(stdoutfnames)

        for stdoutfname in stdoutfnameslist:
            #print('for stdout %s' % stdoutfname)
            for exec_prog in exec_proglist:
                stdinfiles = '%s%s.%s.' % (RESULTHOME, exec_prog, "stdin")
                stdoutfiles = '%s%s.%s.' % (RESULTHOME, exec_prog, "stdout")
                if stdoutfiles in stdoutfname:
                    #print "match"
                    (filenamepart, timestamppart) = stdoutfname.split(stdoutfiles)
                    targetmtime = os.path.getmtime(stdoutfname)
                    if timestamppart not in timestamplist:
                        #print('adding %s' % timestamppart)
                        timestamplist[timestamppart] = targetmtime
                    elif targetmtime > timestamplist[timestamppart]:
                        timestamplist[timestamppart] = targetmtime
                else:
                    #print "no match"
                    continue

    ''' process each timestamped result file. '''
    for timestamppart in timestamplist:
        targetmtime_string = datetime.datetime.fromtimestamp(timestamplist[timestamppart])
        end_time = targetmtime_string.strftime("%Y%m%d%H%M%S")
        outputjsonfname = '%s%s.%s' % (OUTPUTRESULTHOME, jsonoutputfilename, timestamppart)
        #print "ParseStdinStdout (1): Outputjsonfname is (%s)" % outputjsonfname
        ParseConfigForFile(studentlabdir, labidname, configfilelines, outputjsonfname, 
                           container_list, timestamppart, end_time)
    ''' process files without timestamps '''
    outputjsonfname = '%s%s' % (OUTPUTRESULTHOME, jsonoutputfilename)
    ParseConfigForFile(studentlabdir, labidname, configfilelines, outputjsonfname, container_list, None, None)



# Usage: ResultParser.py <studentlabdir> <mycontainername> <instructordir> <labidname>
# Arguments:
#     <studentlabdir> - directory containing the student lab work
#                    extracted from zip file (done in Instructor.py)
#     <mycontainername> - name of the container
#     <instructordir> - directory containing instructor's solution
#                       for corresponding student
#     <labidname> - name of the lab
def main():
    #print "Running ResultParser.py"
    if len(sys.argv) != 5:
        sys.stderr.write("Usage: ResultParser.py <studentlabdir> <mycontainername> <instructordir> <labidname>\n")
        sys.exit(1)

    studentlabdir = sys.argv[1]
    mycontainername = sys.argv[2]
    instructordir = sys.argv[3]
    labidname = sys.argv[4]
    ParseStdinStdout(studentlabdir, mycontainername, instructordir, labidname)
    return 0

if __name__ == '__main__':
    sys.exit(main())

