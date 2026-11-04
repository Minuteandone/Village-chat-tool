#!/usr/bin/env python3
"""Inspect public archived SQL dump headers and AWS import categories only.
Never execute the archive, inspect live URLs, or reproduce original SQL rows/hosts/credentials.
"""
import hashlib,io,json,pathlib,re,urllib.parse,urllib.request,zipfile,collections
HERE=pathlib.Path(__file__).resolve().parent
URL="https://archive.org/download/monster-game-server/monster-game-server.zip"
HASH="df086c9ca4581733f73f2e8aaea1408382232e4d"
class ArchiveRedirect(urllib.request.HTTPRedirectHandler):
    count=0
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        self.count+=1
        host=urllib.parse.urlsplit(newurl).hostname or ""
        if self.count>5 or not newurl.startswith("https://") or not(host=="archive.org" or host.endswith(".archive.org")):raise ValueError("Unexpected redirect")
        return super().redirect_request(req,fp,code,msg,headers,newurl)
req=urllib.request.Request(URL,headers={"User-Agent":"Public-MSM-Archive-Research/1.0"})
with urllib.request.build_opener(ArchiveRedirect()).open(req,timeout=80) as response:raw=response.read(20_000_001)
if len(raw)>20_000_000 or hashlib.sha1(raw).hexdigest()!=HASH:raise RuntimeError("Unexpected archive")
z=zipfile.ZipFile(io.BytesIO(raw))
result={"archive_url":URL,"verified_sha1":HASH,"sql":{},"cloud_java":{},"notes":"Only program/version and category flags retained; no hosts, secrets, game database rows or original code."}
for member in z.namelist():
    if not member.endswith(".sql"):continue
    data=z.read(member).decode("utf-8","replace")
    name=member.split("/")[-1]
    # Which generator recognizable from conventional non-sensitive literal header signature?
    header=data[:3000]
    indicators={
        "mysql_dump_header":bool(re.search(r"MySQL dump",header,re.I)),
        "mysqldump_style_table_sections":bool(re.search(r"Dumping data for table",data,re.I)),
        "mysqldump_style_structure_sections":bool(re.search(r"Table structure for table",data,re.I)),
        "phpmyadmin_export_header":bool(re.search(r"phpMyAdmin",header,re.I)),
        "adminer_export_header":bool(re.search(r"Adminer",header,re.I)),
        "mysql_dump_completed":bool(re.search(r"Dump completed",data,re.I)),
        "mentions_rds_amazonaws_domain":bool(re.search(r"\b(?:[a-z0-9-]+\.)+[a-z0-9-]+\.rds\.amazonaws\.com\b",header,re.I)),
        "aws_rds_region":(re.search(r"\.([a-z]{2}-[a-z]+-\d)\.rds\.amazonaws\.com\b",header,re.I).group(1) if re.search(r"\.([a-z]{2}-[a-z]+-\d)\.rds\.amazonaws\.com\b",header,re.I) else None),
        "mysqldump_client_distribution":(re.search(r"(?im)^\s*--\s*MySQL dump\s+\S+\s+Distrib\s+([\d.]+)",header).group(1) if re.search(r"(?im)^\s*--\s*MySQL dump\s+\S+\s+Distrib\s+([\d.]+)",header) else None),
        "dump_client_platform_linux_x86_64":bool(re.search(r"MySQL dump[^\n]*for Linux \(x86_64\)",header,re.I)),
        "amazon_word_occurrences":len(re.findall(r"\bAmazon\b",data,re.I)),
        "aws_word_occurrences":len(re.findall(r"\bAWS\b",data,re.I)),
        "amazon_web_services_phrase_occurrences":len(re.findall(r"Amazon Web Services",data,re.I)),
        "structure_section_count":len(re.findall(r"Table structure for table",data,re.I)),
        "data_section_count":len(re.findall(r"Dumping data for table",data,re.I)),
        "has_source_generator_version_line":bool(re.search(r"(?im)^\s*--\s*MySQL dump \d",header)),
        "has_server_version_line":bool(re.search(r"(?im)^\s*--\s*Server version",header)),
        "has_generation_timestamp_line":bool(re.search(r"(?im)^\s*--\s*(?:Generation Time|Dump completed on)",data)),
    }
    # Only literal output for version numbers from well-known tool headers; avoid hostname/account info.
    dump_ver=re.search(r"(?im)^\s*--\s*(MySQL dump\s+\d+(?:\.\d+)+(?:\s+Distrib\s+[\w.\-]+)?)\s*$",header)
    if dump_ver:indicators["mysql_dump_tool_header"]=dump_ver.group(1)[:120]
    server_ver=re.search(r"(?im)^\s*--\s*Server version\s+([\d.]+)",header)
    if server_ver:indicators["server_version_numeric"]=server_ver.group(1)
    gen_date=re.search(r"(?im)^\s*--\s*Dump completed on\s+(\d{4}-\d\d-\d\d(?:\s+\d\d:\d\d:\d\d)?)",data)
    if gen_date:indicators["completed_on_header_date"]=gen_date.group(1)
    result["sql"][name]=indicators
# API/cloud terms only in first party BBB Java, not bundled Amazon SDK class names.
services=collections.Counter();filenames=[]
for name in z.namelist():
    if not name.endswith(".java") or "/com/bigbluebubble/" not in name:continue
    data=z.read(name).decode("utf-8","replace")
    found=[]
    for label,regex in {
        "SQS messaging":r"\b(?:AmazonSQSClient|SqsWrapper|SendMessageRequest|com[.]amazonaws[.]services[.]sqs)\b",
        "SNS notifications":r"\b(?:AmazonSNSClient|SnsWrapper|PublishRequest|com[.]amazonaws[.]services[.]sns)\b",
        "CloudWatch metrics":r"\b(?:AmazonCloudWatchClient|CloudWatchReporter|PutMetricDataRequest|com[.]amazonaws[.]services[.]cloudwatch)\b",
        "EC2 instance metadata":r"\b(?:EC2Metadata|AmazonEC2Client|com[.]amazonaws[.]services[.]ec2)\b",
        "Elasticache/memcache":r"\b(?:MemcachedClient|ElastiCache|spymemcached)\b",
        "S3 storage":r"\b(?:AmazonS3Client|AmazonS3|com[.]amazonaws[.]services[.]s3)\b",
    }.items():
        if re.search(regex,data):
            found.append(label)
            services[label]+=1
    if found:filenames.append({"file":name.split("/")[-1],"services":found})
result["cloud_java"]={"classes_by_service":dict(services),"files":filenames}
(HERE/"server-dump-aws-evidence.json").write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps(result,indent=2))
