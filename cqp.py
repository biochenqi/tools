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
import random,string
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

def send_info(infos,now_file,now_size,orig_info,all_file,Total_size,start_time):
    end_time=time.time()
    read_rate=float(now_size)/float(end_time-start_time)
    time_remaind=float(Total_size-now_size)/float(read_rate)
    all_time=float(Total_size)/float(read_rate)+float(start_time)
    sender = 'from@runoob.com'
    file_rate=int((float(int(now_file)-2)/float(all_file))*100)
    size_rate=int((float(now_size)/float(Total_size))*100)
    file_bar='['+'>'*int(file_rate/2)+'='*(50-int(file_rate/2))+']'
    size_bar='['+'>'*int(size_rate/2)+'='*(50-int(size_rate/2))+']'
    subject=orig_info+'''
#==============================
Finished file number:
{0}  {1}%   {2} / {3}

Finished file size:
{4}  {5}%  {6} / {7} Mb

#==============================
Used time:            |    Remained time    |      Estimated time    
{8}                   |    {9}              |       {10}             

'''.format(file_bar,file_rate,format(int(now_file)-2,','),format(int(all_file),','),size_bar,size_rate,format(int(str(now_size)[:-6]),','),format(int(str(Total_size)[:-6]),','),fmt_time(end_time-start_time),fmt_time(time_remaind),time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(all_time)))
    receivers = [infos[2]]
    message = MIMEText(subject, 'plain', 'utf-8')
    message['From'] = Header(infos[1], 'utf-8')
    message['To'] =  Header(infos[0], 'utf-8')
    message['Subject'] = Header('the status of cp and md5check!', 'utf-8')    
    try:
        smtpObj = smtplib.SMTP('localhost')
        smtpObj.sendmail(sender, receivers, message.as_string())
        print('success')
    except smtplib.SMTPException:
        print("Error: faild to send email")


def send_log(file,infos,orig_info,start_time):
    sender = 'from@runoob.com'
    receivers = [infos[2]]
     
    message = MIMEMultipart()
    message['From'] = Header(infos[1], 'utf-8')
    message['To'] =  Header(infos[0], 'utf-8')
    subject = 'gcp finished!'
    message['Subject'] = Header(subject, 'utf-8')
    end_time=time.time()
    message.attach(MIMEText(
orig_info+'''
#==============================
Used time:       |       Finished time
{0}              |        {1}
'''.format(fmt_time(end_time-start_time),time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time)))
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

def md5check(files,data_md5):
    prog=Popen('md5sum %s'%(files),shell=True,stdout=PIPE,stderr=PIPE)
    a,b=prog.communicate()
    stdout=a.decode("utf8").replace('\n','')
    stderr=b.decode("utf8").replace('\n','')
    info=re.split(r'\s+',stdout)
    file=files.strip().split('/')[-1]
    if file in data_md5:
        if info[0] not in data_md5[file]:
            show_info('md5check:\'%s\' check faild,please check it!'%files)
            return 0
        else:
            return 1
    else:
        show_info('md5check:\'%s\' may not exists in md5.txt,please check it'%files)
        return 0


def cp_info(dir_in,dir_out,infos,prefix,resume,orig_info,start_time,type_wirte):
    success_file=[]
    if resume:
        for line in open(resume,'r'):
            success_file.append(line.strip())
    data_md5={}
    old_path=os.path.abspath(dir_out)
    num_dir=dir_in.split('/')
    num_dir=len(num_dir) if num_dir[-1]!='' else len(num_dir)-1
    w=open('%s/%s_rig.log'%(dir_out,prefix),type_wirte)
    in_length=dir_in.split('/') if dir_in.split('/')[-1]!='' else dir_in.split('/')[:-1]
    length_in=len(in_length)
    for i in os.popen('find %s -type f'%dir_in):
        if re.findall(r'md5',i.strip().lower().split('/')[-1]):
            for line in open(i.strip(),'r'):
                info=re.split(r'\s+',line.strip())
                #here need to check if the path of file_name eq files
                file_name=info[1].strip().split('/')[-1]
                if file_name not in data_md5:data_md5[file_name]=[]
                data_md5[file_name].append(info[0])
    for i in os.popen('find %s -type f'%dir_in):
        if i.strip() in success_file:
            continue
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
        #here need to check if the path of file_name eq files
        files=dir_out+'/'.join(path)+'/'+i.strip().split('/')[-1]
        if re.findall(r'md5',i.strip().lower().split('/')[-1]):
            pass
        else:
            judg=md5check(files,data_md5)
            if judg:
                w.write(i)
    w.close()
    os.chdir(dir_out)
    send_log('%s.log'%prefix,infos,orig_info,start_time)

def just_warning(infos,dir_out,orig_info,all_file,Total_size,start_time):
    sta=time.time()
    while 1:
        end=time.time()
        if end-sta>=infos[3]:
            now_file,now_size=0,0
            for i in os.popen('find %s -type f'%dir_out):
                now_file+=1
                for s in os.popen('stat --format=%s {0}'.format(i.strip())):
                    now_size+=int(s.strip())
            send_info(infos,now_file,now_size,orig_info,all_file,Total_size,start_time)
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
    parser.add_argument(
        '--rangetime',help='set how long send you an letter(unit:s)',dest='rangetime',type=int,default=1800)
    parser.add_argument(
        '--email',help='send letter to the email you point',dest='email',type=str)
    parser.add_argument(
        '--resume',help='breakpoint resume(need right log file)',dest='resume',type=str)
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
    eamil_info={
"chenqi":"chenqi@gooalgene.com",
"pyfan":"fanpy@gooalgene.com",
"yhfu":"fuyh@gooalgene.com",
"ctguo":"guoct@gooalgene.com",
"xmkang":"kangxm@gooalgene.com",
"konglp":"konglp@gooalgene.com",
"tyli":"lity@gooalgene.com",
"liuan":"liuan@gooalgene.com",
"liujq":"liujq@gooalgene.com",
"liuyc":"liuyc@gooalgene.com",
"pengbing":"pengbing@gooalgene.com",
"qianyt":"qianyt@gooalgene.com",
"zqshu":"shuzq@gooalgene.com",
"suncc":"suncc@gooalgene.com",
"support":"support@gooalgene.com",
"wanght":"wanght@gooalgene.com",
"wanglu":"wanglu@gooalgene.com",
"zhujuan":"zhujuan@gooalgene.com",
"zhushilin":"zhusl@gooalgene.com",
"zouyu":"zouyu@gooalgene.com",
    }
    args=getopt()
    start_time=time.time()
    infos=[]
    for i in os.popen('whoami'):
        Operator=i.strip()
        infos.append(Operator)
    for i in os.popen('hostname'):
        hostname=i.strip()
        infos.append(hostname)
    if args.email:
        infos.append(args.email)
    else:
        if Operator in eamil_info:
            infos.append(eamil_info[Operator])
        else:
            print('you should give a email address!')
            sys.exit(0)
    infos.append(args.rangetime)
    process_id=''.join(random.sample(string.ascii_letters+string.digits,16))
    

    type_wirte='a' if args.resume else 'w'
    logging.basicConfig(level=logging.INFO,
            format='%(asctime)s [line:%(lineno)d][%(levelname)s:] %(message)s',
            datefmt='%Y-%m-%d  %H:%M:%S',
            filename="%s/%s.log"%(args.outdir,args.name),
            filemode=type_wirte)
    begin=show_info('############cp and md5check is start!############')
    all_file,Total_size=0,0
    for i in os.popen('find %s -type f'%args.indir):
        all_file+=1
        for s in os.popen('stat --format=%s {0}'.format(i.strip())):
            Total_size+=int(s.strip())
    path_from_dir=os.path.abspath(args.indir)
    path_to_dir=os.path.abspath(args.outdir)
    orig_info='''
#==============================
File number：{0}
Total size：{1} Mb
Start time： {2}
From: {3}
To: {4}
Err.Log： {5}
Rig.Log : {6}
Operator: {7}
Process ID: {8}
'''.format(format(int(all_file),','),format(int(str(Total_size)[:-6]),','),time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time)), path_from_dir,path_to_dir,"%s/%s.log"%(path_to_dir,args.name),"%s/%s_rig.log"%(path_to_dir,args.name),Operator,process_id)

    thrs=threading.Thread(target=just_warning,args=(infos,args.outdir,orig_info,all_file,Total_size,start_time))
    thrs.setDaemon(True)
    thrs.start()
    cp_info(args.indir,args.outdir,infos,args.name,args.resume,orig_info,start_time,type_wirte)
    run_time(begin)

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
        sys.stderr.write("User interrupt me! >_< See you!\n")
        sys.exit(0)
        
