# tools
各种各样的工具集

cqp:  
    
    简介：该脚本用来监控md5校验以及拷贝过程中出的问题，它会每隔一段时间（可以设定）向指定的邮箱发送邮件来提醒脚本是否还在运行，结束后会发送一个log文件包含了所有的错误信息以及运行时间，该软件的断点续传功能可以当你拷贝异常中端之后继续你之前已经拷完的文件继续拷贝但是需要提供生成的n_rig.log文件。（每次使用该脚本会生成两个Log文件，一个是错误日志n.log，另外一个是成功拷贝的文件的日志n_rig.log） 
    
    使用：cqp [options] SOURCE DEST
    
    参数：  
    -r     当以目录作为拷贝时需加此参数
    --name=<prefix> 设置日志文件的前缀（默认：cqp)
    --rangetime=<int> 设置发送给指定邮箱的间隔时间, 单位：秒 (默认：1800）
    --email=<email> 设置指定的邮箱地址来发送监控邮件 （默认：自动识别）
    --resume=<n_rig.log> 断点续传（使用需要指定n_rig.log的日志文件）

fq_check_v0.2: 
    
    简介：该脚本用于校验fq文件，最终会生成一个pdf文件用于显示双端fq文件的id和碱基数是否一致，碱基数是否达标，并且显示两fq文件的碱基数目，reads数量。
    
    使用：python fq_check_v0.2.py -i fq_dir -o outdir -n thread_num[default:depend on system] --suffix sample.suffix[default:fastq.gz] --minbase minbase_num
    
    参数：
    -i     输入含有所有fastq文件的目录
    -o     输入输出的目录
    -n     设置线程数,默认：基于系统现有的线程数来分配
    --suffix     设置后缀名，默认：fastq.gz
    --minbase    设置校验的最小碱基数


ncbi_get.py: 
    
    简介：该脚本用于爬取ncbi上的物种序列和meta信息。
    
    使用：python3 ncbi_get.py -o <outdir> --input <txid> --number 100 --prefix <species name>
    
    参数：
    -i     输入物种taid号
    -o     输出的目录
    --number     设置线程数,默认为10
    --timeout    设置socket连接时长，默认为120秒
    --prefix     输出文件前缀
