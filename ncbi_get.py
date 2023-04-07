#!/usr/local/bin/python3.6
from bs4 import BeautifulSoup as Soup
from Bio import Entrez
import sys,os,argparse
import aiohttp
import asyncio
from urllib import error,request
#关闭ssl验证，防止出现urllib.error.URLError
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
##防止出现IncompleteRead的错误
import http.client
http.client.HTTPConnection._http_vsn = 10
http.client.HTTPConnection._http_vsn_str = 'HTTP/1.0'

from datetime import datetime
import socket,os
socket.setdefaulttimeout(240)

Entrez.email='2040463170@qq.com'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36',
    'sec-ch-ua-platform': "Windows"

}

usages = """ 
Author : chenqi
Email  : qic@sansure.com.cn
Date   : 2021/12/10
Version: v1.0
Description:
    用来从ncbi的nucleotide里爬取物种查询到的所有条目的碱基序列以及meta信息
Example:
    python3 %s -o <outdir> --input <txid> --number 100 --prefix <species name>

Example path:/project/usr/chenqi/test/test_software_make/ncbi_get/

Example cmd:
    python3 %s -o . -i txid11709 --number 100 --prefix HIV2

"""%(sys.argv[0],sys.argv[0])

class HelpFormatter(argparse.RawDescriptionHelpFormatter, argparse.ArgumentDefaultsHelpFormatter):
    pass

def getopt():
    parser = argparse.ArgumentParser(
        formatter_class=HelpFormatter, description=usages)
    parser.add_argument('-o','--output',help = 'output dir[default:current directory]',type = str,default='.',dest='outdir')
    parser.add_argument('-i','--input',help='input species txid',type=str,dest='input')
    parser.add_argument('--number',help='each Crawling the number of the gi information[default:10]',type=int,default=10,dest='number')
    parser.add_argument('--timeout',help='Set the socket timeout [default 120 seconds].',type=int,default=120,dest='timeout')
    parser.add_argument('--prefix',help='prefix of fasta file[species name]',type=str,dest='prefix',default='')
    args = parser.parse_args()
    if not args.input:
        print('species name must be given!!')
        sys.exit(0)
    return args

def judg_label(label):
    if label == None:
        return ''
    else:
        return label.text.replace('\n',' ')


def xml_deal(xml_info):
    soup = Soup(xml_info,'xml')
    list_meta_info,list_sequnce_info,list_gi = [],[], []
    for gbseq in soup.find_all('GBSeq'):
        defnition = judg_label(gbseq.find('GBSeq_definition'))
        version = judg_label(gbseq.find('GBSeq_accession-version'))
        #增加一列linneage信息
        linneage = judg_label(gbseq.find('GBSeq_taxonomy'))
        for i in gbseq.find_all('GBSeqid'):
            if i.text.startswith('gi'):
                gi = i.text.split('|')[1]

        organism = judg_label(gbseq.find('GBSeq_organism'))
        list_info = ['','','','','','','','','']
        for GBQualifier in gbseq.find_all('GBQualifier'):
            name = GBQualifier.find('GBQualifier_name')
            value = GBQualifier.find('GBQualifier_value')
            if value == None or name == None:
                continue
            name = judg_label(name)
            value = judg_label(value) + ' '
            i = -1
            if name == 'db_xref':
                i = 0
            elif name == 'mol_type':
                i = 1
            elif name == 'isolate':
                i = 2
            elif name == 'strain':
                i = 2
            elif name == 'host':
                i = 3
            elif name == 'isolation_source':
                i = 4
            elif name == 'culture_collection':
                i = 5
            elif name == 'country':
                i = 6
            elif name == 'collection_date':
                i = 7
            elif name == 'note':
                i = 8
            elif i == -1:
                continue
            list_info[i] = list_info[i] + value
        locus = judg_label(gbseq.find('GBSeq_locus')) + '\t' + judg_label(gbseq.find('GBSeq_length')) + 'db\t' + judg_label(gbseq.find('GBSeq_moltype')) + '\t' + judg_label(gbseq.find('GBSeq_topology')) + '\t' + judg_label(gbseq.find('GBSeq_division')) + '\t' + judg_label(gbseq.find('GBSeq_update-date'))
        sequnce = gbseq.find('GBSeq_sequence')
        if sequnce != None:
            sequnce = sequnce.text.replace('\n','')
            sequnce_info = '>%s\n%s'%(gi,sequnce)
        else:
            #有些序列过长导致在下载的xml里并没有该gi的fasta序列，通过直接使用fasta的方式进行序列下载
            xml_info = Entrez.efetch(db='nuccore',id=str(gi),rettype='fasta',retmode='text')
            sequnce_info = xml_info.read().rstrip('\n')
        list_sequnce_info.append(sequnce_info)
            
        meta_info = '%s\t%s\t%s\t%s\t%s\t%s\t%s'%(defnition,version,gi,organism, linneage,'\t'.join(list_info),locus)
        list_meta_info.append(meta_info)
        list_gi.append(str(gi))
    if list_meta_info:
        with open(file_meta,'a') as f_meta,open(file_seq,'a') as f_fasta:
            f_meta.write('\n'.join(list_meta_info)+'\n')
            f_fasta.write('\n'.join(list_sequnce_info)+'\n')
    # return list_meta_info,list_sequnce_info,list_gi


async def get(session, queue):
    count = 0
    while True:
        try:
            id_name = queue.get_nowait()
        except asyncio.QueueEmpty:
                return
        url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=nuccore&id=%s&usehistory=y&rettype=gb&retmode=xml'%id_name
        resp = await session.get(url)
        result = await resp.text(encoding='utf-8')
        if result.strip()!="":
            xml_deal(result)

async def main():
    list_id = resume()  
    # num_of_each_get = 100
    #设置超时时间为600秒
    timeout = aiohttp.ClientTimeout(total=num_of_time_out)
    #降低并发数量设置为50, 服务器可以限制TCP连接的持续时间。 默认情况下，aiohttp使用HTTP keep-alive，因此同一个TCP连接可以用于多个请求。 这可以提高性能，因为不必为每个请求都建立一个新的TCP连接。 但是，一些服务器限制TCP连接的持续时间，如果对许多请求使用相同的TCP连接，服务器可以在您完成连接之前关闭它。 您可以禁用HTTP keep-alive作为一种变通方法。 为此，您可以创建一个自定义TCPConnector，将参数force_close设置为True，并将其传递给ClientSession
    connector = aiohttp.TCPConnector(limit=num_of_each_get,force_close=True)
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        queue = asyncio.Queue()
        for i in range(int(len(list_id)/num_of_each_get)+1):
            queue.put_nowait(','.join(list_id[i*num_of_each_get:i*num_of_each_get + num_of_each_get]))
        tasks = []
        for _ in range(num_of_each_get):
            task = get(session, queue)
            tasks.append(task)
        await asyncio.wait(tasks)

def resume():
    list_id = []
    dict_id = {}
    if os.path.exists(file_gi):
        total_id_list = total_id(file_gi)
        if os.path.exists(file_meta):
            with open(file_meta,'r') as f:
                for line in f:
                    line = line.strip().split('\t')
                    if line[2] not in dict_id:dict_id[line[2]] = 0
            for i in total_id_list:
                if i not in dict_id:
                    list_id.append(i)

            return list_id
        else:
            return total_id_list
    else:
        ##总结：需要获取物种Subtree links所有的条目数而不是Direct links所有的条目数时需要在输入的txid的后面加上[Organism:exp]这样就能获取所有的条目数了
        search_handle = Entrez.esearch(db="nucleotide",term=args.input+'[Organism:exp]')
        total_num = Entrez.read(search_handle)
        total_num = int(total_num['Count'])
        search_handle = Entrez.esearch(db="nucleotide",term=args.input+'[Organism:exp]',retstart=0,retmax=total_num)
        list_id = Entrez.read(search_handle)
        list_id = list_id['IdList']
        with open(file_gi,'w') as w:
            w.write('\n'.join(list_id))
        w.close()
        return list_id


def total_id(file_id):
    list_id = []
    with open(file_id,'r') as f:
        for line in f:
            list_id.append(line.strip())
    return list_id

def check_finish():
    total_id_list = total_id(file_gi)
    with open(file_meta,'r') as f:
        count = 0
        for line in f:
            count+=1
    if count>=len(total_id_list):
        return 'ok',len(total_id_list)-count
    else:
        return 'not ok',len(total_id_list)-count

def check_dir(dir):
    if not os.path.exists(dir):os.makedirs(dir)

args = getopt()
check_dir(args.outdir)
file_gi = "%s/%s_gi.txt"%(args.outdir,args.input)
file_meta = "%s/%s_meta.%s.txt"%(args.outdir,args.input,args.prefix) if args.prefix else "%s/%s_meta.txt"%(args.outdir,args.input)
file_seq = "%s/%s_seq.%s.txt"%(args.outdir,args.input,args.prefix) if args.prefix else "%s/%s_seq.txt"%(args.outdir,args.input)
num_of_each_get = args.number
num_of_time_out = args.timeout
while 1:
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        sys.exit(0)

    info_ok, num_down = check_finish()
    if info_ok == 'ok':
        print('finished download!!')
        break
    else:
        print('still need to download %s seq'%num_down)
