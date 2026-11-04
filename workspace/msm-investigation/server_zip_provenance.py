#!/usr/bin/env python3
"""Inspect only structural metadata of a public historical ZIP, never execute files."""
import collections, datetime, hashlib, io, json, pathlib, urllib.parse, urllib.request, zipfile
ROOT = pathlib.Path(__file__).resolve().parent
URL = "https://archive.org/download/monster-game-server/monster-game-server.zip"
EXPECTED = "df086c9ca4581733f73f2e8aaea1408382232e4d"
class ArchiveRedirect(urllib.request.HTTPRedirectHandler):
    def __init__(self): self.count=0
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self.count += 1
        host = (urllib.parse.urlsplit(newurl).hostname or "").lower()
        if self.count > 5 or not newurl.startswith("https://") or not (host == "archive.org" or host.endswith(".archive.org")):
            raise ValueError("Not an Internet Archive host")
        return super().redirect_request(req, fp, code, msg, headers, newurl)
request = urllib.request.Request(URL, headers={"User-Agent":"Historical-game-archive-provenance-research/1.0"})
with urllib.request.build_opener(ArchiveRedirect()).open(request, timeout=80) as resp:
    raw = resp.read(20_000_001)
if len(raw) > 20_000_000 or hashlib.sha1(raw).hexdigest() != EXPECTED:
    raise ValueError("Unexpected file size or archive SHA-1")
with zipfile.ZipFile(io.BytesIO(raw)) as z:
    members = z.infolist()
    comment_bytes = z.comment
    comment_text = comment_bytes.decode("utf-8","replace")
    roots = sorted(set(x.filename.split("/")[0] for x in members))
    dates = collections.Counter(datetime.datetime(*x.date_time).isoformat() for x in members)
    systems = collections.Counter(str(x.create_system) for x in members)
    compressions = collections.Counter(str(x.compress_type) for x in members)
    flags = collections.Counter(str(x.flag_bits) for x in members)
    eocd_pos = raw.rfind(b"PK\x05\x06")
    eocd_comment_len = int.from_bytes(raw[eocd_pos+20:eocd_pos+22],"little") if eocd_pos>=0 else None
    extra_ids = collections.Counter()
    for x in members:
        block=x.extra
        offset=0
        while offset+4<=len(block):
            kind=int.from_bytes(block[offset:offset+2],"little")
            count=int.from_bytes(block[offset+2:offset+4],"little")
            extra_ids[f"0x{kind:04x}"]+=1
            offset+=4+count
    first = members[0]
    result = {
       "source_url":URL, "verified_archive_sha1":EXPECTED,
       "downloaded_bytes":len(raw),
       "zip_file_comment_length":len(comment_bytes),
       "zip_file_comment_ascii":comment_text[:500],
       "zip_file_comment_hex":comment_bytes[:120].hex(),
       "eocd_comment_length":eocd_comment_len,
       "archive_comment_equals_folder_hash":len(roots)==1 and comment_text.strip().lower()==roots[0].split("-")[-1].lower(),
       "root_folder_names":roots,
       "entry_count":len(members),
       "file_count":sum(not x.is_dir() for x in members),
       "dir_count":sum(x.is_dir() for x in members),
       "all_member_timestamps":dict(dates.most_common(10)),
       "create_system_counts":dict(systems),
       "compression_method_counts":dict(compressions),
       "general_purpose_flags_counts":dict(flags),
       "central_directory_extra_field_ids_counts":dict(extra_ids),
       "individual_file_comment_count":sum(bool(x.comment) for x in members),
       "first_entry_metadata":{"name":first.filename,"timestamp":first.date_time,"creator_system":first.create_system,
                                 "creator_version":first.create_version,"extract_version":first.extract_version,
                                 "external_mode_oct":oct((first.external_attr>>16)&0xffff),
                                 "compression":first.compress_type,"extra_len":len(first.extra),
                                 "individual_comment_len":len(first.comment)},
       "note":"No archived code or binaries executed or republished. Git-style metadata does not prove GitHub/GitLab hosting."
    }
(ROOT/"server-zip-provenance.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
print(json.dumps(result,indent=2))
