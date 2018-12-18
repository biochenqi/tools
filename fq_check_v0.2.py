#!/usr/bin/python
# -*- coding: utf-8 -*-

########packages########
import os
import re
import sys
import time
import gzip
import glob
import math
import argparse
import multiprocessing
import numpy as np
try:
    import matplotlib as mpl
    mpl.use('Agg')
    import matplotlib.pyplot as plt
    # plt.switch_backend('agg')
    from matplotlib.backends.backend_pdf import PdfPages
except:
    print('matplotlib error:may you should check the package!!')
    sys.exit(0)
#######Description######
usage = '''
Author : chenqi
Email  : chenqi@gooalgene.com
Date   : 2018-09-08 16:16:18
Link   : 
Version: latest
Description:

Usage:
    python %s 
'''% (__file__[__file__.rfind(os.sep) + 1:])

#####HelpFormat#####
class HelpFormatter(argparse.RawDescriptionHelpFormatter, argparse.ArgumentDefaultsHelpFormatter):
    pass

def getopt():
    parser = argparse.ArgumentParser(
        formatter_class=HelpFormatter, description=usage)
    parser.add_argument(
        '-i','--indir',help='input fq dir',type=str,dest='indir')
    parser.add_argument(
        '-o','--outdir',help='ouput result dir',type=str,dest='outdir')
    parser.add_argument(
        '-n','--thread',help='set num of thread(default:depend on system)',type=int,dest='thread')
    parser.add_argument(
        '--suffix',help='input fq suffix',type=str,dest='suffix',default='fastq.gz')
    parser.add_argument(
        '--minbase',help='set the sample base num',type=int,dest='bin')
    args=parser.parse_args()
    if not args.indir:
        print('indir must be given!!!')
        sys.exit(0)
    elif not args.outdir:
        print('outdir must be given!!!')
        sys.exit(0)
    elif not args.bin:
        print('minbase must be given!!!')
        sys.exit(0)
    return args

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

def fq_check_stat(fq_1,fq_2,bin_num,sample_name):
    f_1=gzip.open(fq_1,'rb')
    f_2=gzip.open(fq_2,'rb')
    count,r1_read_num,r2_read_num,r1_base_num,r2_base_num,id_judg=0,0,0,0,0,'y'
    line_1,line_2=f_1.readline().decode('utf8'),f_2.readline().decode('utf8')
    wrong_id=[]
    while 1:
        if not line_1 and not line_2:
            break
        else:
            count+=1
            if count==1:
                if line_1.split(' ')[0]==line_2.split(' ')[0]:
                    pass
                else:
                #do you want to know which line didn't sam
                    id_judg='n'
                    # wrong_id.append([line_1.strip(),line_2.strip()])
            elif count==2:
                if line_1:
                    r1_read_num+=1
                    r1_base_num+=len(line_1.strip())
                if line_2:
                    r2_read_num+=1
                    r2_base_num+=len(line_2.strip())
            elif count==4:
                count=0
            line_1,line_2=f_1.readline().decode('utf8'),f_2.readline().decode('utf8')
    read_judg='y' if r1_read_num==r2_read_num else 'n'
    base_judg='y' if r1_base_num+r2_base_num>bin_num else 'n'
    result='\t'.join([sample_name,str(r1_read_num),str(r1_base_num),str(r2_read_num),str(r2_base_num),read_judg,id_judg,base_judg])
    return [read_judg,id_judg,base_judg,r1_base_num+r2_base_num,sample_name,wrong_id,result]

def system_cpu():
    total_thread,used_thread=0,0
    for i in os.popen('cat /proc/cpuinfo|grep processor|wc -l'):
        total_thread+=int(i.strip())
    judg_info=0
    for i in os.popen('top -b -n 1'):
        if i.strip().startswith('PID'):
            info=re.split(r'\s+',i.strip())
            cpu_index=info.index('%CPU')
            judg_info=1
            continue
        if judg_info:
            info=re.split(r'\s+',i.strip())
            used_thread+=int(float(info[cpu_index])/float(100))
    thread_num=int((total_thread-used_thread)*2/3)
    return thread_num

def average(list_v):
    averages=int(sum(list_v)/len(list_v))
    return averages

def draw_picture(a,col_table,table_vel,output):
    num=int((average(a)/5)/1000000)
    col_colors = ['red' for x in range(len(col_table))]
    if num<100:
        range_num=100
    elif 0<num%100<50:
        range_num=num-num%100
    elif 50<=num%100:
        range_num=num-num%100+100

    max_num=int(max(a)/1000000)+range_num
    sta,end=0,0
    list_x,list_y=[],[]
    for i in range(range_num,max_num,range_num):
        end=i
        count=0
        for s in a:
            if sta<=s/1000000<=end:
                count+=1
                if '-'.join([str(sta),str(end)]) not in list_x:
                    list_x.append('-'.join([str(sta),str(end)]))
    #            a.remove(s)
        if count:list_y.append(count)
        sta=end
    with PdfPages('%s/test.pdf'%(output)) as pdf:
        fig, (ax0, ax1) = plt.subplots(nrows=2, figsize=(14,14),sharey=True)
        plt.subplot(2,1,1)
        width = 0.45
        plt.bar(list_x,list_y,width)
        plt.xlabel('base unit:M')
        plt.ylabel('number of sample')
        plt.subplot(2,1,2)
        my_table=plt.table(cellText=table_vel,colLabels=col_table,colColours=col_colors,cellLoc='center',colWidths=[0.15]*len(col_table),loc='best')
        my_table.set_fontsize(10)
        my_table.auto_set_column_width([i for i in range(len(col_table))])
        #        ax1.text(0,0,'good')
        plt.axis('off')
        plt.show()
        pdf.savefig(fig)
        plt.close()

def main():
    args=getopt()
    thread_num=args.thread if args.thread else system_cpu()
    print(thread_num)
    error_sample_num,less_than_bin=0,0
    w=open('%s/fq_stat_check.txt'%args.outdir,'w')
    w.write('\t'.join(['sample_name','r1_read_num','r1_base_num','r2_read_num','r2_base_num','r1=r2(read_num)(y|n)','r1=r2(id)(y|n)','r1+r2(base_num)>minbase(y|n)'])+'\n')
    judg_fq={}
    # for i in os.popen('find %s -name *.fastq.gz'%args.indir):
    remove_name=['1','2','R1','R2','r1','r2']
    for i in glob.glob('%s/*.%s'%(args.indir,args.suffix)):
        sample=i.strip().split('/')[-1].split('.')[0].split('_')
        for name in i.strip().split('/')[-1].split('.')[0].split('_'):
            if name in remove_name:
                sample.remove(name)
        sample='_'.join(sample)
        

        if sample not in judg_fq:judg_fq[sample]=[]
        judg_fq[sample].append(i.strip())
    thr = thread_num if len(judg_fq)>thread_num else len(judg_fq)
    pool=multiprocessing.Pool(processes=thr)
    result,all_base=[],[]
    for key,value in judg_fq.items():
        result.append(pool.apply_async(fq_check_stat,(value[0],value[1],args.bin,key,)))
    error_sample,less_sample,table_info=[],[],[]
    for i in result:
        info=i.get()
        w.write(info[-1])
        table_info.append(info[-1].split('\t'))
        if info[0]=='n' or info[1]=='n':
            error_sample_num+=1
            error_sample.append(info[4])
        if info[2]=='n':
            less_than_bin+=1
            less_sample.append(info[4])
        for value in info[5]:
            w.write('\t'+':'.join(value))
        w.write('\n')
        all_base.append(info[3])
    total_sample=len(judg_fq)
    w.write('''
total_sample_num:{0}\terror_sample_num:{1}\tless_than_bin_sample_num:{2}

error_sample:{3}

less_than_minbase:{4}

'''.format(total_sample,error_sample_num,less_than_bin,'\t'.join(error_sample),'\t'.join(less_sample)))
    w.close()
    draw_picture(all_base,['sample_name','r1_read_num','r1_base_num','r2_read_num','r2_base_num','r1=r2(read_num)(y|n)','r1=r2(id)(y|n)','r1+r2(base_num)>minbase(y|n)'],table_info,args.outdir)

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
