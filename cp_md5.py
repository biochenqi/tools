#!/usr/bin/env python
# -*- coding: utf-8 -*-

#####Import Module#####
import random
import time
import sys
import os,re
import logging
import math
import argparse
import smtplib
import threading
from subprocess import PIPE,Popen
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

usage = '''
Author : chenqi
Email  : chenqi@gooalgene.com
Date   : 2018-09-08 16:16:18
Link   : 
Version: v1.0
Description:
    monitor cp and md5check!
Example:
    python %s 
''' % (__file__[__file__.rfind(os.sep) + 1:])

class Config():
    def __init__(self):
        self.Email='chenqi@gooalgene.com'
        self.From='bio02' #server num:103|T640|....
        self.To='chenqi'  #your name:handsome chen|super handsome chen|...
        self.range_time=25 #set how long to send you email:3600|60

class HelpFormatter(argparse.RawDescriptionHelpFormatter, argparse.ArgumentDefaultsHelpFormatter):
    pass

def run_time(start_time):
    spend_time = time.time() - start_time
    logging.info("Total  spend time : " + fmt_time(spend_time))
    return 0


def fmt_time(spend_time):
    spend_time = int(spend_time)
    day = 24 * 60 * 60
    hour = 60 * 60
    min = 60
    if spend_time < 60:
        return "%ds" % math.ceil(spend_time)
    elif spend_time > day:
        days = divmod(spend_time, day)
        return "%dd%s" % (int(days[0]), fmt_time(days[1]))
    elif spend_time > hour:
        hours = divmod(spend_time, hour)
        return '%dh%s' % (int(hours[0]), fmt_time(hours[1]))
    else:
        mins = divmod(spend_time, min)
        return "%dm%ds" % (int(mins[0]), math.ceil(mins[1]))

def show_info(text):
    now_time = time.time()
    logging.info(text)
    return now_time

def pro_bar(now_file,all_file):
    if all_file>500:
        all_file=all_file//2
        now_file=now_file//2
        return pro_bar(now_file,all_file)
    else:
        return now_file,all_file


def send_info(infos,now_file,all_file):
    sender = 'from@runoob.com'
    now_file,all_file=pro_bar(now_file,all_file)
    process_look='['+'>'*int(now_file)+'-'*(int(all_file)-int(now_file))+']'
    subject='''
cp5check still running!
{2} {0}/{1} 
'''.format(now_file,all_file,process_look)
    receivers = [infos.Email]
    message = MIMEText(subject, 'plain', 'utf-8')
    message['From'] = Header(infos.From, 'utf-8')
    message['To'] =  Header(infos.To, 'utf-8')
    message['Subject'] = Header('the status of cp and md5check!', 'utf-8')    
    try:
        smtpObj = smtplib.SMTP('localhost')
        smtpObj.sendmail(sender, receivers, message.as_string())
        print('success')
    except smtplib.SMTPException:
        print("Error: faild to send email")


def send_log(file,infos):
    sender = 'from@runoob.com'
    receivers = [infos.Email]
     
    message = MIMEMultipart()
    message['From'] = Header(infos.From, 'utf-8')
    message['To'] =  Header(infos.To, 'utf-8')
    subject = 'cp and md5 check finished!'
    message['Subject'] = Header(subject, 'utf-8')
     
    message.attach(MIMEText(
'''
    cp and md5 check already finished!!

    please check the file which file got problem!!
'''
        , 'plain', 'utf-8'))
     
    att1 = MIMEText(open(file, 'rb').read(), 'base64', 'utf-8')
    att1["Content-Type"] = 'application/octet-stream'
    att1["Content-Disposition"] = 'attachment; filename="md5.txt"'
    message.attach(att1)
     
    try:
        smtpObj = smtplib.SMTP('localhost')
        smtpObj.sendmail(sender, receivers, message.as_string())
        print("success")
    except smtplib.SMTPException:
        print("Error: fail to send mail")

def check_dir(dirs):
    if not os.path.exists(dirs):os.mkdir(dirs)

#need to change
def md5check(files,data_md5):
    prog=Popen('md5sum %s'%files,shell=True,stdout=PIPE,stderr=PIPE)
    a,b=prog.communicate()
    stdout=a.decode("utf8").replace('\n','')
    stderr=b.decode("utf8").replace('\n','')
    info=re.split(r'\s+',stdout)
    file_name=files.strip().split('/')[-1]
    if file_name in data_md5:
        if data_md5[file_name]!=info[0]:show_info('md5check:\'%s\' check faild,please check it!'%files)
    else:
        show_info('md5check:\'%s\' may not exists md5.txt,please check it'%files)


def cp_info(dir_in,dir_out,infos,prefix):
    begin=show_info('############cp and md5check is start!############')
    data_md5={}
    old_path=os.path.abspath(dir_out)
    num_dir=dir_in.split('/')
    num_dir=len(num_dir) if num_dir[-1]!='' else len(num_dir)-1
    for i in os.popen('find %s -type f'%dir_in):
        if re.findall(r'md5',i.strip().lower().split('/')[-1]):
            for line in open(i.strip(),'r'):
                info=re.split(r'\s+',line.strip())
                file_name=info[1].split('/')[-1]
                if file_name not in data_md5:data_md5[file_name]=info[0]
    for i in os.popen('find %s -type f'%dir_in):
        sta=dir_out
        path=i.strip().split('/')[num_dir-1:-1]
        if path:
            #you need to change here
            for path_dir in path:
                check_dir(sta+'/'+path_dir)
                sta=sta+'/'+path_dir
        prog=Popen('cp {0} {1}'.format(i.strip(),dir_out+'/'+'/'.join(path)),shell=True,stdout=PIPE,stderr=PIPE)
        stdout,stderr=prog.communicate()
        if stderr:
            show_info(stderr.decode("utf8").replace('\n',''))
            continue
        files=dir_out+'/'+'/'.join(path)+'/'+i.strip().split('/')[-1]
        if re.findall(r'md5',i.strip().lower().split('/')[-1]):
            pass
        else:
            md5check(files,data_md5)
    os.chdir(dir_out)
    send_log('%s.log'%prefix,infos)
    run_time(begin)

def just_warning(infos,dir_in,dir_out):
    for i in os.popen('find %s -type f|wc -l'%dir_in):
        all_file=i.strip()
    sta=time.time()
    while 1:
        end=time.time()
        if end-sta>=infos.range_time:
            for i in os.popen('find %s -type f|wc -l'%dir_out):
                now_file=int(i.strip())-1
            send_info(infos,now_file,all_file)
            sta=end

def getopt():
    parser = argparse.ArgumentParser(
            formatter_class=HelpFormatter, description=usage)
    parser.add_argument(
        '-i','--indir',help='input cp start dir',dest='indir',type=str)
    parser.add_argument(
        '-o','--outdir',help='output cp end dir',dest='outdir',type=str)
    parser.add_argument(
        '-n','--name',help='give the prefix of log file',dest='name',type=str)
    args = parser.parse_args()
    if not args.indir:
        print('indir must be given')
        sys.exit(0)
    elif not args.outdir:
        print('outdir must be given')
        sys.exit(0)
    elif not args.name:
        print('prefix of log file must be given')
        sys.exit(0)
    return args

def main():
    infos=Config()
    args=getopt()
    logging.basicConfig(level=logging.INFO,
            format='%(asctime)s [line:%(lineno)d][%(levelname)s:] %(message)s',
            datefmt='%Y-%m-%d  %H:%M:%S',
            filename="%s/%s.log"%(args.outdir,args.name),
            filemode='w')
    thrs=threading.Thread(target=just_warning,args=(infos,args.indir,args.outdir))
    thrs.setDaemon(True)
    thrs.start()
    cp_info(args.indir,args.outdir,infos,args.name)

if __name__=='__main__':
    try:
        t1 = time.time()
        time1 = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t1))
        print('Start at : ' + time1)

        main()
        t2 = time.time()
        time2 = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t2))
        print('End at : ' + time2)
        t3 = t2 - t1
        print('Spend time: ' + fmt_time(t3))
    except KeyboardInterrupt:
        sys.stderr.write("User interrupt me! ;-) See you!\n")
        sys.exit(0)
        
